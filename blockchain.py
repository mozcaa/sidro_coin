import json
import time
import os

from config import CHAIN_FILE, DIFFICULTY, CURRENCY, MINING_REWARD
from utils import calculate_hash
from miner import mine_block
from wallet import get_balance, is_transaction_valid, has_initial_funds
from mempool import load_mempool, add_transaction_to_mempool, clear_mempool


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
        "currency": CURRENCY,
        "reason": "INITIAL_BALANCE"
    }

    if not has_initial_funds(chain, "Tommaso"):
     
     print("Mining del blocco iniziale con 100 SID a Tommaso...")

     # Controlliamo se la transazione iniziale è valida
     if is_transaction_valid(chain, initial_transaction):
         new_block, mining_stats = mine_block([initial_transaction], chain[-1])
         chain.append(new_block)
         save_chain(chain)
         print("Blocco iniziale aggiunto.")
         print("Tentativi:", mining_stats["attempts"])
         print("Tempo mining:", round(mining_stats["mining_time"], 4), "secondi")
         print("Modalità mining:", mining_stats["mining_mode"])
     else:
         print("Transazione iniziale non valida.")

    else:
         print("Tommaso ha gia' ricevuto il saldo iniziale")

    # Seconda transazione: Tommaso manda 20 SID a Luca
    transaction = {
      "from": "Tommaso",
      "to": "Luca",
      "amount": 20,
      "currency": CURRENCY
    }

    print()
    print("Saldo Tommaso prima:", get_balance(chain, "Tommaso"))
    print("Saldo Luca prima:", get_balance(chain, "Luca"))

    if is_transaction_valid(chain, transaction):
         add_transaction_to_mempool(transaction)
         print("Transazione valida aggiunta alla mempool.")
    else:
         print("Transazione rifiutata: saldo insufficiente.")

    pending_transactions = load_mempool()

    if len(pending_transactions) > 0:
          print("Transazioni in attesa:", len(pending_transactions))
          print("Mining del nuovo blocco con le transazioni della mempool...")

          miner_name = "Miner5001"

          reward_transaction = {
              "from": "SYSTEM",
               "to": miner_name,
               "amount": MINING_REWARD,
               "currency": CURRENCY,
               "reason": "MINING_REWARD"
           }

          transactions_to_mine = pending_transactions + [reward_transaction]    

          new_block, mining_stats = mine_block(transactions_to_mine, chain[-1])
          chain.append(new_block)
          save_chain(chain)

          clear_mempool()

          print("Blocco aggiunto!")
          print("Hash:", new_block["hash"])
          print("Tentativi:", mining_stats["attempts"])
          print("Tempo mining:", round(mining_stats["mining_time"], 4), "secondi")
          print("Modalità mining:", mining_stats["mining_mode"])
          print("Mempool svuotata.")
    else:
          print("Nessuna transazione da minare.")

    print("Saldo Tommaso dopo:", get_balance(chain, "Tommaso"))
    print("Saldo Luca dopo:", get_balance(chain, "Luca"))
    print("Saldo Miner5001 dopo:", get_balance(chain, "Miner5001"))
    print()
    print("Blockchain valida:", is_chain_valid(chain))