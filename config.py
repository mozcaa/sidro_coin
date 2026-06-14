# File in cui viene salvata la blockchain
CHAIN_FILE = "chain.json"

# Difficoltà del Proof-of-Work:
# con 4, l'hash deve iniziare con "0000"
DIFFICULTY = 4

# File in cui vengono salavate le transazioni prima di essere messe nella blockchain
MEMPOOL_FILE = "mempool.json"

# Nome della valuta
CURRENCY = "SID"

# Ricompensa futura del miner
MINING_REWARD = 10

# Se True, il mining usa più processi in parallelo.
# Se False, usa il mining sequenziale normale.
USE_PARALLEL_MINING = True

# Numero di processi worker usati nel mining parallelo.
# Con 4 worker:
# worker 0 prova nonce 0, 4, 8, 12...
# worker 1 prova nonce 1, 5, 9, 13...
# worker 2 prova nonce 2, 6, 10, 14...
# worker 3 prova nonce 3, 7, 11, 15...
MINING_WORKERS = 4