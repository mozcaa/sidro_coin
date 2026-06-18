import time
from config import USE_PARALLEL_MINING, MINING_WORKERS, DIFFICULTY
from blockchain import create_genesis_block, run_mining

def run_benchmark(num_blocchi=100):
    print("="*50)
    print(" 🚀 SIDROCOIN - BENCHMARK MINING 🚀")
    print("="*50)
    
    # Stampiamo le impostazioni attuali lette da config.py
    modalita = "PARALLELA (Multiprocessing)" if USE_PARALLEL_MINING else "SEQUENZIALE (Singolo Core)"
    print(f"Modalità attiva: {modalita}")
    print(f"Difficoltà (Zeri): {DIFFICULTY}")
    if USE_PARALLEL_MINING:
        print(f"Numero di Worker: {MINING_WORKERS}")
    print(f"Blocchi da minare: {num_blocchi}")
    print("-" * 50)
    print("Inizio test... attendere prego ⏳\n")

    # Inizializziamo una blockchain "finta" solo in memoria
    chain = [create_genesis_block()]
    tempi_mining = []

    # Transazione dummy fissa per non perdere tempo a calcolare saldi
    dummy_tx = [{
        "from": "SYSTEM",
        "to": "Tester",
        "amount": 10,
        "currency": "SID",
        "reason": "BENCHMARK"
    }]

    tempo_totale_inizio = time.time()

    # Ciclo di mining per N blocchi
    for i in range(num_blocchi):
        start_time = time.time()
        
        # Minazione del blocco
        new_block, stats = run_mining(dummy_tx, chain[-1])
        
        end_time = time.time()
        
        durata_blocco = end_time - start_time
        tempi_mining.append(durata_blocco)
        chain.append(new_block)

        # Stampa i progressi (sovrascrivendo la stessa riga per non intasare il terminale)
        print(f"\rProgresso: minato blocco {i+1}/{num_blocchi} in {durata_blocco:.3f} sec...", end="", flush=True)

    tempo_totale_fine = time.time()
    durata_totale = tempo_totale_fine - tempo_totale_inizio

    print("\n\n" + "="*50)
    print(" 📊 RISULTATI BENCHMARK ")
    print("="*50)
    
    # Calcolo statistiche
    tempo_medio = sum(tempi_mining) / num_blocchi
    tempo_min = min(tempi_mining)
    tempo_max = max(tempi_mining)

    print(f"Tempo TOTALE per {num_blocchi} blocchi:  {durata_totale:.3f} secondi")
    print(f"Tempo MEDIO per blocco:      {tempo_medio:.3f} secondi")
    print(f"Tempo MINIMO registrato:     {tempo_min:.3f} secondi")
    print(f"Tempo MASSIMO registrato:    {tempo_max:.3f} secondi")
    print("="*50)

if __name__ == "__main__":
    # Puoi cambiare il numero di blocchi qui, 100 è un ottimo numero per avere una media affidabile
    run_benchmark(num_blocchi=30)