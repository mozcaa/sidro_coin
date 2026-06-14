import json
import os

from config import MEMPOOL_FILE


def load_mempool():
    """
    Carica la mempool dal file mempool.json.

    La mempool contiene le transazioni in attesa
    di essere inserite in un blocco.
    """

    if not os.path.exists(MEMPOOL_FILE):
        return []

    with open(MEMPOOL_FILE, "r") as file:
        return json.load(file)


def save_mempool(mempool):
    """
    Salva la mempool dentro mempool.json.
    """

    with open(MEMPOOL_FILE, "w") as file:
        json.dump(mempool, file, indent=4)


def add_transaction_to_mempool(transaction):
    """
    Aggiunge una nuova transazione alla mempool.
    """

    mempool = load_mempool()
    mempool.append(transaction)
    save_mempool(mempool)


def clear_mempool():
    """
    Svuota la mempool dopo che le transazioni
    sono state inserite in un blocco.
    """

    save_mempool([])