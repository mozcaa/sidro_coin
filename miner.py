import time

from config import DIFFICULTY
from utils import calculate_hash


def mine_block(transactions, previous_block):
    """
    Crea un nuovo blocco valido tramite Proof-of-Work.

    Restituisce:
    - il blocco minato
    - le statistiche del mining
    """

    nonce = 0
    timestamp = time.time()
    start_time = time.time()

    while True:
        block = {
            "index": previous_block["index"] + 1,
            "timestamp": timestamp,
            "transactions": transactions,
            "previous_hash": previous_block["hash"],
            "nonce": nonce
        }

        block_hash = calculate_hash(block)

        if block_hash.startswith("0" * DIFFICULTY):
            block["hash"] = block_hash

            end_time = time.time()

            mining_stats = {
                "mining_time": end_time - start_time,
                "attempts": nonce + 1,
                "mining_mode": "sequential"
            }

            return block, mining_stats

        nonce += 1