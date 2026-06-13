def get_balance(chain, user):
    """
    Calcola il saldo di un utente leggendo tutte le transazioni
    presenti nella blockchain.

    Non salviamo direttamente il saldo in una variabile fissa:
    lo ricostruiamo dalla cronologia delle transazioni.
    """

    balance = 0

    # Scorriamo tutti i blocchi della blockchain
    for block in chain:

        # Ogni blocco contiene una lista di transazioni
        for transaction in block["transactions"]:

            # Se l'utente è il destinatario, riceve monete
            if transaction["to"] == user:
                balance += transaction["amount"]

            # Se l'utente è il mittente, perde monete
            # SYSTEM è un mittente speciale: crea nuove monete
            if transaction["from"] == user:
                balance -= transaction["amount"]

    return balance


def is_transaction_valid(chain, transaction):
    """
    Controlla se una transazione è valida.

    Una transazione è valida se:
    - l'importo è positivo
    - il mittente ha abbastanza SID
    - oppure il mittente è SYSTEM, cioè una transazione speciale di creazione monete
    """

    sender = transaction["from"]
    amount = transaction["amount"]

    # L'importo deve essere maggiore di zero
    if amount <= 0:
        return False

    # SYSTEM può creare monete dal nulla.
    # Serve per ricompense mining o saldo iniziale.
    if sender == "SYSTEM":
        return True

    # Calcoliamo il saldo del mittente
    sender_balance = get_balance(chain, sender)

    # La transazione è valida solo se il mittente ha abbastanza soldi
    return sender_balance >= amount