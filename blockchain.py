import json
import time
import os

from config import (
    CHAIN_FILE,
    DIFFICULTY,
    CURRENCY,
    MINING_REWARD,
    USE_PARALLEL_MINING,
    MINING_WORKERS
)

from utils import calculate_hash
from miner import mine_block, mine_block_parallel
from wallet import get_balance, is_transaction_valid, has_initial_funds
from mempool import load_mempool, add_transaction_to_mempool, clear_mempool


def create_genesis_block():
    """
    Crea il primo blocco della blockchain, chiamato genesis block.

    Il genesis block è speciale perché non ha un blocco precedente.
    Per questo previous_hash viene impostato a "0".
    """

    block = {
        "index": 0,
        "timestamp": 0,
        "transactions": [],
        "previous_hash": "0",
        "nonce": 0
    }

    # Calcoliamo l'hash del genesis block
    block["hash"] = calculate_hash(block)

    return block


def load_chain():
    """
    Carica la blockchain dal file chain.json.

    Se chain.json non esiste, viene creata una nuova blockchain
    contenente solo il genesis block.
    """

    if not os.path.exists(CHAIN_FILE):
        return [create_genesis_block()]

    with open(CHAIN_FILE, "r") as file:
        return json.load(file)


def save_chain(chain):
    """
    Salva la blockchain dentro il file chain.json.
    """

    with open(CHAIN_FILE, "w") as file:
        json.dump(chain, file, indent=4)


def run_mining(transactions, previous_block):
    """
    Sceglie quale tipo di mining usare.

    Se USE_PARALLEL_MINING è True:
        usa il mining parallelo con più processi.

    Se USE_PARALLEL_MINING è False:
        usa il mining sequenziale normale.

    In questo modo possiamo cambiare modalità modificando solo config.py.
    """

    if USE_PARALLEL_MINING:
        return mine_block_parallel(
            transactions,
            previous_block,
            MINING_WORKERS
        )

    return mine_block(transactions, previous_block)


def print_mining_stats(new_block, mining_stats):
    """
    Stampa a schermo le informazioni del mining.

    Questi dati servono solo per debug/benchmark.
    Non vengono salvati dentro il blocco.
    """

    print(f"Hash: {new_block['hash']}")
    print(f"Nonce trovato: {new_block['nonce']}")
    print(f"Tempo mining: {mining_stats['mining_time']:.4f} secondi")
    print(f"Modalità mining: {mining_stats['mining_mode']}")

    if mining_stats["mining_mode"] == "sequential":
        print(f"Tentativi totali: {mining_stats['estimated_total_attempts']}")

    if mining_stats["mining_mode"] == "parallel":
        print(f"Worker usati: {mining_stats['workers']}")
        print(f"Worker vincitore: {mining_stats['winning_worker']}")
        print(f"Tentativi worker vincitore: {mining_stats['winning_worker_attempts']}")
        print(f"Tentativi totali stimati: {mining_stats['estimated_total_attempts']}")


def is_chain_valid(chain):
    """
    Verifica se la blockchain è valida.

    Controlla:
    1. Che ogni blocco punti correttamente al blocco precedente.
    2. Che l'hash salvato nel blocco sia corretto.
    3. Che l'hash rispetti la difficoltà del Proof-of-Work.
    """

    # Partiamo da 1 perché il blocco 0 è il genesis block
    for i in range(1, len(chain)):
        current = chain[i]
        previous = chain[i - 1]

        # Controllo 1: collegamento corretto al blocco precedente
        if current["previous_hash"] != previous["hash"]:
            return False

        # Controllo 2: l'hash ricalcolato deve coincidere con quello salvato
        if calculate_hash(current) != current["hash"]:
            return False

        # Controllo 3: l'hash deve rispettare la difficulty
        if not current["hash"].startswith("0" * DIFFICULTY):
            return False

    return True


# Questo blocco viene eseguito solo se lanciamo direttamente:
# python blockchain.py
if __name__ == "__main__":

    # Carichiamo la blockchain esistente oppure creiamo il genesis block
    chain = load_chain()

    # Transazione iniziale speciale:
    # SYSTEM crea 100 SID e li assegna a Tommaso.
    initial_transaction = {
        "from": "SYSTEM",
        "to": "Tommaso",
        "amount": 100,
        "currency": CURRENCY,
        "reason": "INITIAL_BALANCE"
    }

    # Evitiamo che Tommaso riceva 100 SID ogni volta che il programma viene riavviato
    if not has_initial_funds(chain, "Tommaso"):

        print("Mining del blocco iniziale con 100 SID a Tommaso...")

        if is_transaction_valid(chain, initial_transaction):

            # Usiamo run_mining invece di mine_block direttamente.
            # Così il programma sceglie da solo mining sequenziale o parallelo.
            new_block, mining_stats = run_mining([initial_transaction], chain[-1])

            chain.append(new_block)
            save_chain(chain)

            print("Blocco iniziale aggiunto.")
            print_mining_stats(new_block, mining_stats)

        else:
            print("Transazione iniziale non valida.")

    else:
        print("Tommaso ha gia' ricevuto il saldo iniziale.")

    # Transazione normale di esempio:
    # Tommaso manda 20 SID a Luca.
    transaction = {
        "from": "Tommaso",
        "to": "Luca",
        "amount": 20,
        "currency": CURRENCY
    }

    print()
    print(f"Saldo Tommaso prima: {get_balance(chain, 'Tommaso')} {CURRENCY}")
    print(f"Saldo Luca prima: {get_balance(chain, 'Luca')} {CURRENCY}")

    # Prima di inserirla nella mempool, controlliamo che la transazione sia valida
    if is_transaction_valid(chain, transaction):
        add_transaction_to_mempool(transaction)
        print("Transazione valida aggiunta alla mempool.")
    else:
        print("Transazione rifiutata: saldo insufficiente.")

    # Carichiamo le transazioni in attesa dalla mempool
    pending_transactions = load_mempool()

    if len(pending_transactions) > 0:
        print(f"Transazioni in attesa: {len(pending_transactions)}")
        print("Mining del nuovo blocco con le transazioni della mempool...")

        # Nome del miner che riceverà la ricompensa
        miner_name = "Miner5001"

        # Transazione speciale di reward:
        # SYSTEM crea 10 SID e li assegna al miner.
        reward_transaction = {
            "from": "SYSTEM",
            "to": miner_name,
            "amount": MINING_REWARD,
            "currency": CURRENCY,
            "reason": "MINING_REWARD"
        }

        # Nel blocco inseriamo sia le transazioni normali
        # sia la ricompensa del miner.
        transactions_to_mine = pending_transactions + [reward_transaction]

        # Mining del blocco usando la modalità scelta in config.py
        new_block, mining_stats = run_mining(transactions_to_mine, chain[-1])

        # Aggiungiamo il blocco minato alla blockchain
        chain.append(new_block)
        save_chain(chain)

        # Dopo aver minato le transazioni, la mempool viene svuotata
        clear_mempool()

        print("Blocco aggiunto!")
        print_mining_stats(new_block, mining_stats)
        print(f"Ricompensa assegnata a {miner_name}: {MINING_REWARD} {CURRENCY}")
        print("Mempool svuotata.")

    else:
        print("Nessuna transazione da minare.")

    print()
    print(f"Saldo Tommaso dopo: {get_balance(chain, 'Tommaso')} {CURRENCY}")
    print(f"Saldo Luca dopo: {get_balance(chain, 'Luca')} {CURRENCY}")
    print(f"Saldo Miner5001 dopo: {get_balance(chain, 'Miner5001')} {CURRENCY}")

    print()
    print(f"Blockchain valida: {is_chain_valid(chain)}")