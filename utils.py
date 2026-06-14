import json
import hashlib


def calculate_hash(block):
    """
    Calcola l'hash SHA-256 di un blocco.

    L'hash viene calcolato sul contenuto del blocco,
    escludendo il campo 'hash' stesso.
    """

    # Copiamo il blocco per non modificare l'originale
    block_copy = block.copy()

    # Rimuoviamo l'hash prima del calcolo
    block_copy.pop("hash", None)

    # Convertiamo il blocco in stringa JSON ordinata
    block_string = json.dumps(block_copy, sort_keys=True)

    # Calcoliamo e restituiamo l'hash SHA-256
    return hashlib.sha256(block_string.encode()).hexdigest()