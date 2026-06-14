import time
import multiprocessing as mp

from config import DIFFICULTY
from utils import calculate_hash


def mine_block(transactions, previous_block):
    """
    Mining sequenziale.

    Questa funzione prova i nonce uno alla volta:
    0, 1, 2, 3, 4...

    Restituisce:
    - block: il blocco minato
    - mining_stats: dati utili per stampare il benchmark a schermo
    """

    # Il nonce parte da 0 e cresce di 1 a ogni tentativo
    nonce = 0

    # Fissiamo il timestamp una sola volta.
    # Così durante il mining cambia solo il nonce.
    timestamp = time.time()

    # Salviamo il tempo iniziale per misurare quanto dura il mining
    start_time = time.time()

    while True:
        # Creiamo un blocco candidato.
        # Non ha ancora l'hash definitivo.
        block = {
            "index": previous_block["index"] + 1,
            "timestamp": timestamp,
            "transactions": transactions,
            "previous_hash": previous_block["hash"],
            "nonce": nonce
        }

        # Calcoliamo l'hash del blocco candidato
        block_hash = calculate_hash(block)

        # Controlliamo se l'hash rispetta la difficulty.
        # Esempio: se DIFFICULTY = 4, deve iniziare con "0000".
        if block_hash.startswith("0" * DIFFICULTY):

            # Se l'hash è valido, lo salviamo nel blocco
            block["hash"] = block_hash

            # Prepariamo statistiche solo per stampa/debug.
            # NON vengono salvate nel blocco.
            mining_stats = {
                "mining_time": time.time() - start_time,
                "mining_mode": "sequential",
                "workers": 1,
                "winning_worker": None,
                "winning_worker_attempts": nonce + 1,
                "estimated_total_attempts": nonce + 1
            }

            return block, mining_stats

        # Se l'hash non è valido, proviamo il nonce successivo
        nonce += 1


def parallel_worker(
    worker_id,
    workers_count,
    transactions,
    previous_block,
    timestamp,
    result_queue,
    stop_event
):
    """
    Funzione eseguita da ogni processo worker.

    Ogni worker prova una sequenza diversa di nonce.

    Esempio con 4 worker:
    worker 0 prova: 0, 4, 8, 12...
    worker 1 prova: 1, 5, 9, 13...
    worker 2 prova: 2, 6, 10, 14...
    worker 3 prova: 3, 7, 11, 15...

    In questo modo i worker non provano gli stessi nonce.
    """

    # Ogni worker parte da un nonce diverso.
    # worker 0 parte da 0, worker 1 da 1, ecc.
    nonce = worker_id

    # Conta quanti tentativi ha fatto questo singolo worker
    attempts = 0

    # Il worker continua a minare finché nessun altro worker ha trovato il blocco
    while not stop_event.is_set():

        # Creiamo un blocco candidato.
        # Tutti i worker usano stessi dati, stesso timestamp e stesso previous_hash.
        # Cambia solo il nonce.
        block = {
            "index": previous_block["index"] + 1,
            "timestamp": timestamp,
            "transactions": transactions,
            "previous_hash": previous_block["hash"],
            "nonce": nonce
        }

        # Calcoliamo l'hash del blocco candidato
        block_hash = calculate_hash(block)

        # Questo worker ha fatto un tentativo in più
        attempts += 1

        # Controlliamo se l'hash è valido
        if block_hash.startswith("0" * DIFFICULTY):

            # Salviamo l'hash nel blocco
            block["hash"] = block_hash

            # Il worker vincitore mette il risultato nella queue.
            # La Queue serve perché i processi separati non possono restituire
            # normalmente un valore con return al processo principale.
            result_queue.put({
                "block": block,
                "worker_id": worker_id,
                "attempts": attempts
            })

            # Attiviamo l'evento di stop.
            # Questo dice agli altri worker: "qualcuno ha trovato il blocco, fermatevi".
            stop_event.set()

            return

        # Se il nonce non ha funzionato, passiamo al prossimo nonce di questo worker.
        # Con 4 worker, worker 0 fa 0, 4, 8, 12...
        nonce += workers_count


def mine_block_parallel(transactions, previous_block, workers_count):
    """
    Mining parallelo.

    Crea più processi worker che cercano contemporaneamente
    un nonce valido.

    Il primo worker che trova un hash valido manda il blocco
    al processo principale tramite result_queue.

    Gli altri worker vengono fermati tramite stop_event.
    """

    # Timestamp unico per tutti i worker.
    # Così tutti stanno cercando di minare lo stesso blocco,
    # cambiando solo il nonce.
    timestamp = time.time()

    # Tempo iniziale per misurare il mining
    start_time = time.time()

    # Queue usata dal worker vincitore per mandare il blocco al processo principale
    result_queue = mp.Queue()

    # Event condiviso tra processi.
    # Funziona come una bandierina: quando viene attivato, i worker si fermano.
    stop_event = mp.Event()

    # Lista dei processi creati, così poi possiamo fermarli e aspettarli
    processes = []

    # Creiamo workers_count processi
    for worker_id in range(workers_count):

        # Creiamo un processo che eseguirà la funzione parallel_worker
        process = mp.Process(
            target=parallel_worker,
            args=(
                worker_id,
                workers_count,
                transactions,
                previous_block,
                timestamp,
                result_queue,
                stop_event
            )
        )

        # Salviamo il processo nella lista
        processes.append(process)

        # Avviamo davvero il processo
        process.start()

    # Il processo principale aspetta qui finché un worker trova un blocco valido.
    # result_queue.get() è bloccante: si sblocca solo quando qualcuno fa put().
    result = result_queue.get()

    # Per sicurezza attiviamo lo stop_event anche dal processo principale.
    # Di solito lo ha già fatto il worker vincitore.
    stop_event.set()

    # Prima proviamo a fermare i processi in modo "gentile".
    # join(timeout=1) aspetta massimo 1 secondo che il processo finisca da solo.
    for process in processes:
        process.join(timeout=1)

    # Se qualche processo è ancora vivo, lo terminiamo forzatamente.
    # Questo evita che restino processi zombie o worker ancora attivi.
    for process in processes:
        if process.is_alive():
            process.terminate()
            process.join()

    # Recuperiamo il blocco trovato dal worker vincitore
    block = result["block"]

    # Questi dati servono solo per stampa/benchmark.
    # NON fanno parte del blocco.
    mining_stats = {
        "mining_time": time.time() - start_time,
        "mining_mode": "parallel",
        "workers": workers_count,
        "winning_worker": result["worker_id"],

        # Tentativi fatti dal worker che ha trovato il blocco
        "winning_worker_attempts": result["attempts"],

        # Stima dei tentativi totali.
        # Non è perfetta, ma dà un'idea del lavoro complessivo fatto dai worker.
        "estimated_total_attempts": result["attempts"] * workers_count
    }

    return block, mining_stats