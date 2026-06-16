import sys
from flask import Flask, jsonify, request
import requests

# ==========================================
# 1. AVVIO E CONFIGURAZIONE DINAMICA
# ==========================================

# Controlliamo che l'utente abbia passato la porta da riga di comando.
# sys.argv è la lista degli argomenti: sys.argv[0] è "node.py", sys.argv[1] è la porta.
if len(sys.argv) < 2:
    print("Errore: Specifica la porta. Uso: python node.py <porta>")
    # Uscita forzata con errore se la porta manca
    sys.exit(1)

# Salviamo la porta convertendola in numero intero (es. 5001)
PORT = int(sys.argv[1])

# --- IL TRUCCO DELLA CONFIGURAZIONE DINAMICA ---
# Importiamo il modulo config PRIMA di importare blockchain.py, mempool.py ecc.
import config

# Rinominiamo i file a runtime in base alla porta.
# Se avviamo sulla porta 5001, il file diventerà "chain_5001.json".
# Questo garantisce che ogni nodo legga e scriva solo sui PROPRI file fisici,
# simulando veri computer separati e non un database condiviso.
config.CHAIN_FILE = f"chain_{PORT}.json"
config.MEMPOOL_FILE = f"mempool_{PORT}.json"

# Ora possiamo importare le nostre logiche di business. 
# Quando questi file leggeranno config.CHAIN_FILE, troveranno già il nome aggiornato!
from blockchain import load_chain, save_chain, is_chain_valid, run_mining
from wallet import get_balance, is_transaction_valid
from mempool import load_mempool, add_transaction_to_mempool, clear_mempool


# ==========================================
# 2. INIZIALIZZAZIONE NODO E RETE P2P
# ==========================================

# Inizializziamo l'applicazione web Flask
app = Flask(__name__)

# La "Rubrica" del nodo. Usiamo un Set (insieme) invece di una lista 
# per evitare che lo stesso nodo venga registrato due volte per sbaglio.
# Qui salveremo gli URL degli altri nodi, es: {"http://localhost:5002"}
PEERS = set()

# ==========================================
# 2.5 FUNZIONI DI BROADCAST (PASSAPAROLA)
# ==========================================

def broadcast_transaction(tx_data):
    """
    Quando questo nodo riceve una NUOVA transazione valida, usa questa funzione
    per inoltrarla a tutti i suoi vicini nella rubrica (PEERS).
    """
    for peer in PEERS:
        try:
            # Inviamo i dati all'endpoint /transactions/receive dei nodi vicini
            requests.post(f"{peer}/transactions/receive", json=tx_data, timeout=2)
        except requests.exceptions.RequestException:
            # Se un vicino è spento, la richiesta fallisce. Lo ignoriamo e andiamo avanti.
            pass


def broadcast_block(block):
    """
    Quando questo nodo mina con successo un NUOVO blocco, usa questa funzione
    per "urlarlo" immediatamente a tutta la rete.
    """
    for peer in PEERS:
        try:
            # Inviamo il blocco intero all'endpoint /blocks/receive dei nodi vicini
            requests.post(f"{peer}/blocks/receive", json={"block": block}, timeout=2)
        except requests.exceptions.RequestException:
            pass

# ==========================================
# 3. ENDPOINT API (Le interfacce del nodo)
# ==========================================

@app.route('/chain', methods=['GET'])
def get_node_chain():
    """ 
    Restituisce l'intera blockchain salvata localmente su questo nodo.
    Viene usato dagli utenti per vedere i blocchi e dagli altri nodi 
    durante la fase di sincronizzazione (Consenso).
    """
    chain = load_chain()
    return jsonify({
        "node_port": PORT,
        "chain": chain,
        "length": len(chain)
    }), 200


@app.route('/balance/<user>', methods=['GET'])
def get_user_balance(user):
    """
    Permette a un utente di interrogare questo specifico nodo per sapere
    il proprio saldo. Il nodo lo calcola al volo ricalcolando tutta la sua catena.
    """
    chain = load_chain()
    balance = get_balance(chain, user)
    return jsonify({
        "user": user,
        "balance": balance,
        "currency": config.CURRENCY
    }), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    """ 
    Riceve i dati di una nuova transazione (in formato JSON) inviata da un utente
    o inoltrata (broadcast) da un altro nodo.
    """
    tx_data = request.get_json()
    
    # 1. Controlliamo che il JSON contenga tutti i campi richiesti
    required_fields = ["from", "to", "amount"]
    if not tx_data or not all(field in tx_data for field in required_fields):
        return jsonify({"message": "Campi mancanti nella transazione"}), 400
    
    # Aggiungiamo la valuta se chi ha fatto la richiesta si è dimenticato di metterla
    tx_data["currency"] = config.CURRENCY
    
# 2. Validazione: il mittente ha i soldi?
    chain = load_chain()
    if is_transaction_valid(chain, tx_data):
        # Se sì, la parcheggiamo nella mempool locale del nodo
        add_transaction_to_mempool(tx_data)
        
        # --- AGGIUNTA PER IL BROADCAST ---
        # Avvisiamo subito gli altri nodi dell'esistenza di questa transazione!
        broadcast_transaction(tx_data)
        
        return jsonify({"message": f"Transazione aggiunta alla mempool del nodo {PORT} e trasmessa in rete."}), 201
    else:
        # Se no (es. saldo insufficiente o truffa), il nodo rifiuta la transazione
        return jsonify({"message": "Transazione non valida o saldo insufficiente."}), 400
    

@app.route('/transactions/receive', methods=['POST'])
def receive_transaction():
    """ 
    Endpoint chiamato dagli ALTRI nodi quando fanno il broadcast di una transazione.
    """
    tx_data = request.get_json()
    pending_transactions = load_mempool()
    
    # 1. Controllo Anti-Loop: Se abbiamo già questa transazione nella nostra mempool,
    # ci fermiamo qui per evitare che i nodi se la rimbalzino all'infinito.
    if tx_data in pending_transactions:
        return jsonify({"message": "Transazione già presente nella mempool."}), 200

    # 2. Se è nuova, verifichiamo che sia valida secondo la nostra blockchain locale
    chain = load_chain()
    if is_transaction_valid(chain, tx_data):
        add_transaction_to_mempool(tx_data)
        
        # 3. Effetto Domino: Facciamo da ripetitore e la inoltriamo ai nostri vicini!
        broadcast_transaction(tx_data)
        
        return jsonify({"message": "Transazione ricevuta dal broadcast e salvata."}), 201
    else:
        return jsonify({"message": "Transazione invalida rifiutata."}), 400


@app.route('/mine', methods=['GET'])
def mine():
    """ 
    Comanda a questo nodo di iniziare a minare (calcolo parallelo/sequenziale)
    raccogliendo le transazioni parcheggiate nella sua mempool.
    """
    chain = load_chain()
    pending_transactions = load_mempool()
    
    # Se non ci sono transazioni da approvare, è inutile minare un blocco vuoto
    if not pending_transactions:
        return jsonify({"message": "Nessuna transazione nella mempool da minare."}), 400
    
    # Creiamo la transazione speciale di ricompensa (Reward).
    # Usiamo f"Miner{PORT}" così se il nodo 5001 mina, i soldi vanno a Miner5001.
    reward_transaction = {
        "from": "SYSTEM",
        "to": f"Miner{PORT}",
        "amount": config.MINING_REWARD,
        "currency": config.CURRENCY,
        "reason": "MINING_REWARD"
    }
    
    # Uniamo le transazioni degli utenti con quella della ricompensa
    transactions_to_mine = pending_transactions + [reward_transaction]
    
    print(f"[{PORT}] Avvio mining di un nuovo blocco...")
    
    # --- CUORE DEL SISTEMA ---
    # Chiamiamo la funzione che avvia il multiprocessing!
    new_block, mining_stats = run_mining(transactions_to_mine, chain[-1])
    
    # # 🛡️ FIX CONCORRENZA: Ricarichiamo la catena ORA per vedere se nel frattempo 
    # # un altro processo (o noi stessi un millisecondo fa) ha già aggiunto questo indice!
    # current_chain = load_chain()
    # if current_chain[-1]["index"] >= new_block["index"]:
    #     print(f"[{PORT}] Blocco già presente o rete andata avanti. Scartato.")
    #     clear_mempool()
    #     return jsonify({"message": "Mining annullato per evitare sdoppiamenti."}), 409
    
    # Se siamo arrivati qui, il nonce è stato trovato.
    # Aggiungiamo il blocco alla catena, salviamo su JSON e svuotiamo la mempool.
    chain.append(new_block)
    save_chain(chain)
    clear_mempool()
    
    # --- AGGIUNTA PER IL BROADCAST ---
    # Abbiamo vinto la gara di mining! Inviamo subito il blocco agli altri nodi.
    broadcast_block(new_block)
    
    return jsonify({
        "message": "Nuovo blocco minato con successo!",
        "block": new_block,
        "stats": mining_stats
    }), 200


@app.route('/blocks/receive', methods=['POST'])
def receive_block():
    """
    Endpoint chiamato dagli ALTRI nodi quando minano un blocco e lo trasmettono.
    Questo permette di aggiornare la nostra catena in tempo reale senza aspettare.
    """
    data = request.get_json()
    new_block = data.get("block")
    
    if not new_block:
        return jsonify({"message": "Dati blocco mancanti"}), 400

    chain = load_chain()
    last_block = chain[-1]

    # 1. Validazione di Sequenza: il nuovo blocco si aggancia perfettamente alla nostra catena?
    # L'indice deve essere il successivo e l'hash precedente deve combaciare.
    if new_block["index"] == last_block["index"] + 1 and new_block["previous_hash"] == last_block["hash"]:
        
        # Il blocco è legittimo e sincronizzato. Lo accettiamo!
        chain.append(new_block)
        save_chain(chain)
        
        # Dato che il blocco contiene le transazioni che erano in sospeso, 
        # svuotiamo la nostra mempool per non minarle due volte.
        clear_mempool() 
        
        # Facciamo da ripetitore inoltrando il blocco ad altri eventuali nodi
        broadcast_block(new_block)
        
        print(f"[{PORT}] Ricevuto e accettato nuovo blocco dal broadcast! (Indice {new_block['index']})")
        return jsonify({"message": "Blocco accettato e catena aggiornata."}), 200
        
    # 2. Gestione Conflitti / Ritardi
    elif new_block["index"] > last_block["index"] + 1:
        # Se riceviamo il blocco 10 ma noi siamo fermi al blocco 7, significa che 
        # eravamo offline. Rifiutiamo il blocco singolo e avvisiamo che serve un /resolve.
        return jsonify({"message": "Nodo non sincronizzato, è necessaria una sincronizzazione intera."}), 409
    else:
        # Se l'indice è uguale o inferiore (es. biforcazione), rifiutiamo il blocco.
        return jsonify({"message": "Blocco rifiutato (conflitto o vecchio)."}), 400


# ==========================================
# 4. ALGORITMO DI CONSENSO E COMUNICAZIONE P2P
# ==========================================

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    """ 
    Riceve una lista di URL (es. ["http://localhost:5002"]) e li aggiunge
    alla rubrica di questo nodo, permettendogli di sapere chi sono i suoi vicini.
    """
    data = request.get_json()
    nodes = data.get("nodes") 
    
    if not nodes:
        return jsonify({"message": "Lista nodi non valida"}), 400
        
    for node in nodes:
        # Controllo di sicurezza: evitiamo che il nodo registri se stesso
        # (se la sua porta è 5001, ignora stringhe contenenti ":5001")
        if f":{PORT}" not in node:
            PEERS.add(node)
            
    return jsonify({
        "message": f"Nodi registrati sul nodo {PORT}.",
        "total_peers": list(PEERS)
    }), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    """ 
    Questo è l'algoritmo "Longest Chain Rule" (La catena più lunga vince).
    Risolve i conflitti quando più nodi minano contemporaneamente creando biforcazioni.
    """
    chain = load_chain()
    current_length = len(chain)
    new_chain = None
    max_length = current_length
    
    # 1. Il nodo contatta TUTTI i vicini salvati nella sua rubrica (PEERS)
    for peer in PEERS:
        try:
            # Effettua una richiesta GET all'endpoint /chain del vicino
            # Il timeout=2 evita che il nostro nodo si blocchi all'infinito se un vicino è spento
            response = requests.get(f"{peer}/chain", timeout=2)
            
            if response.status_code == 200:
                peer_data = response.get_json()
                peer_chain = peer_data["chain"]
                peer_length = peer_data["length"]
                
                # 2. Controllo critico:
                # La catena del vicino è più lunga della nostra? ED è anche valida?
                if peer_length > max_length and is_chain_valid(peer_chain):
                    max_length = peer_length
                    new_chain = peer_chain
                    
        except requests.exceptions.RequestException:
            # Se il nodo vicino è spento o irraggiungibile, lo ignoriamo e passiamo al prossimo
            continue
            
    # 3. Risoluzione:
    # Se abbiamo trovato una catena valida e più lunga in rete, sovrascriviamo la nostra!
    if new_chain:
        chain = new_chain
        save_chain(chain)
        return jsonify({
            "message": "La catena è stata sincronizzata con la catena più lunga trovata nella rete.",
            "new_length": max_length
        }), 200
        
    # Se non abbiamo trovato nulla di meglio, teniamo la nostra
    return jsonify({
        "message": "La catena locale è già aggiornata (è la più lunga e valida).",
        "length": current_length
    }), 200


# ==========================================
# 5. AVVIO DEL SERVER FLASK
# ==========================================
if __name__ == '__main__':
    # Avviamo il server in ascolto su tutte le interfacce (0.0.0.0) 
    # e sulla porta specificata al lancio dello script.
    app.run(host='0.0.0.0', port=PORT, debug=False)