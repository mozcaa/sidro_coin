import json
import hashlib
import time
import os
from wallet import get_balance, is_transaction_valid
# Nome del file in cui verrà salvata la blockchain
CHAIN_FILE = "chain.json"

# Difficoltà del Proof-of-Work.
# Significa che l'hash valido deve iniziare con 4 zeri.
DIFFICULTY = 5


def calculate_hash(block):
    """
    Calcola l'hash SHA-256 di un blocco.

    L'hash serve come "impronta digitale" del blocco.
    Se anche un solo dato del blocco cambia, cambia anche l'hash.
    """

    # Facciamo una copia del blocco per non modificare quello originale
    block_copy = block.copy()

    # Rimuoviamo il campo "hash" prima di calcolare l'hash.
    # Questo è necessario perché l'hash deve dipendere dal contenuto del blocco,
    # non da sé stesso.
    block_copy.pop("hash", None)

    # Convertiamo il blocco in una stringa JSON ordinata.
    # sort_keys=True garantisce che l'ordine dei campi sia sempre lo stesso,
    # così lo stesso blocco produce sempre lo stesso hash.
    block_string = json.dumps(block_copy, sort_keys=True)

    # Calcoliamo l'hash SHA-256 della stringa e lo restituiamo in formato esadecimale
    return hashlib.sha256(block_string.encode()).hexdigest()


def create_genesis_block():
    """
    Crea il primo blocco della blockchain, chiamato genesis block.

    Il genesis block non ha un blocco precedente,
    quindi il suo previous_hash viene impostato a "0".
    """

    block = {
        "index": 0,                 # Primo blocco della catena
        "timestamp": time.time(),   # Momento di creazione del blocco
        "transactions": [],         # Nessuna transazione iniziale
        "previous_hash": "0",       # Non esiste un blocco precedente
        "nonce": 0                  # Valore usato nel Proof-of-Work
    }

    # Calcoliamo e aggiungiamo l'hash del blocco
    block["hash"] = calculate_hash(block)

    return block


def load_chain():
    """
    Carica la blockchain dal file JSON.

    Se il file non esiste, significa che la blockchain non è ancora stata creata,
    quindi viene generato il genesis block.
    """

    # Se chain.json non esiste, creiamo una nuova blockchain con solo il genesis block
    if not os.path.exists(CHAIN_FILE):
        return [create_genesis_block()]

    # Se il file esiste, lo apriamo e carichiamo la blockchain salvata
    with open(CHAIN_FILE, "r") as file:
        return json.load(file)


def save_chain(chain):
    """
    Salva la blockchain dentro il file chain.json.
    """

    # Apriamo il file in scrittura e salviamo la lista di blocchi in formato JSON
    with open(CHAIN_FILE, "w") as file:
        json.dump(chain, file, indent=4)


def mine_block(transactions, previous_block):
    """
    Crea un nuovo blocco valido tramite Proof-of-Work.

    Il mining consiste nel provare tanti valori di nonce
    finché l'hash del blocco non inizia con un certo numero di zeri.
    """

    # Il nonce parte da 0 e viene aumentato finché non troviamo un hash valido
    nonce = 0

    while True:
        # Creiamo un blocco candidato
        block = {
            "index": previous_block["index"] + 1,      # Numero del nuovo blocco
            "timestamp": time.time(),                  # Momento di creazione
            "transactions": transactions,              # Transazioni inserite nel blocco
            "previous_hash": previous_block["hash"],   # Hash del blocco precedente
            "nonce": nonce                             # Valore tentato per il mining
        }

        # Calcoliamo l'hash del blocco candidato
        block_hash = calculate_hash(block)

        # Controlliamo se l'hash rispetta la difficoltà richiesta
        # Esempio: con DIFFICULTY = 4, l'hash deve iniziare con "0000"
        if block_hash.startswith("0" * DIFFICULTY):
            # Se l'hash è valido, lo aggiungiamo al blocco
            block["hash"] = block_hash

            # Restituiamo il blocco minato
            return block

        # Se l'hash non è valido, proviamo con un nonce successivo
        nonce += 1


def is_chain_valid(chain):
    """
    Verifica se la blockchain è valida.

    Controlla tre cose:
    1. Ogni blocco punta correttamente al blocco precedente.
    2. L'hash salvato nel blocco è corretto.
    3. L'hash rispetta la difficoltà del Proof-of-Work.
    """

    # Partiamo da 1 perché il blocco 0 è il genesis block
    for i in range(1, len(chain)):
        current = chain[i]
        previous = chain[i - 1]

        # Controllo 1:
        # il previous_hash del blocco corrente deve essere uguale
        # all'hash del blocco precedente.
        if current["previous_hash"] != previous["hash"]:
            return False

        # Controllo 2:
        # ricalcoliamo l'hash del blocco corrente e verifichiamo
        # che sia uguale a quello salvato.
        if calculate_hash(current) != current["hash"]:
            return False

        # Controllo 3:
        # verifichiamo che l'hash rispetti la difficoltà richiesta.
        if not current["hash"].startswith("0" * DIFFICULTY):
            return False

    # Se tutti i controlli sono superati, la blockchain è valida
    return True


# Questo blocco viene eseguito solo se lanciamo direttamente:
# python blockchain.py
if __name__ == "__main__":

    # Carichiamo la blockchain esistente o creiamo il genesis block
    chain = load_chain()

    # Prima transazione: SYSTEM assegna 100 SID a Tommaso
    # Questa simula la creazione iniziale di monete
    initial_transaction = {
        "from": "SYSTEM",
        "to": "Tommaso",
        "amount": 100,
        "currency": "SID"
    }


    print("Mining del blocco iniziale con 100 SID a Tommaso...")

    # Controlliamo se la transazione iniziale è valida
    if is_transaction_valid(chain, initial_transaction):
        new_block = mine_block([initial_transaction], chain[-1])
        chain.append(new_block)
        save_chain(chain)
        print("Blocco iniziale aggiunto.")
    else:
        print("Transazione iniziale non valida.")

    # Seconda transazione: Tommaso manda 20 SID a Luca
    transaction = {
        "from": "Tommaso",
        "to": "Luca",
        "amount": 20,
        "currency": "SID"
    }
    print("\n")
    print("Saldo Tommaso prima:", get_balance(chain, "Tommaso"))
    print("Saldo Luca prima:", get_balance(chain, "Luca"))

    # Verifichiamo che Tommaso abbia abbastanza SID
    if is_transaction_valid(chain, transaction):
        print("Transazione valida. Mining del nuovo blocco...")

        new_block = mine_block([transaction], chain[-1])
        chain.append(new_block)
        save_chain(chain)

        print("Blocco aggiunto!")
        print("Hash:", new_block["hash"])
    else:
        print("Transazione rifiutata: saldo insufficiente.")

    print("Saldo Tommaso dopo:", get_balance(chain, "Tommaso"))
    print("Saldo Luca dopo:", get_balance(chain, "Luca"))
    print("\n")
    print("Blockchain valida:", is_chain_valid(chain))