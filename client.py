import requests
import sys

def print_menu():
    print("\n" + "="*40)
    print(" 🛠️  SIDROCOIN - PANNELLO DI CONTROLLO ")
    print("="*40)
    print("1. Connetti i nodi (Registra Peers)")
    print("2. Crea una nuova transazione")
    print("3. Avvia il Mining su un nodo")
    print("4. Controlla il saldo di un utente")
    print("5. Controlla la lunghezza della Blockchain")
    print("6. 🔥 SIMULA ATTACCO: Invia blocco falso")
    print("0. Esci")
    print("="*40)

def main():
    while True:
        print_menu()
        scelta = input("Seleziona un'opzione (0-6): ")

        if scelta == '0':
            print("Uscita dal client...")
            sys.exit()

        # elif scelta == '1':
        #     porta_target = input("A quale nodo vuoi inviare il comando? (es. 5001): ")
        #     nodi_input = input("Inserisci le porte degli altri nodi separate da spazio (es. 5002 5003): ")
        #     nodi_list = [f"http://localhost:{p}" for p in nodi_input.split()]
            
        #     try:
        #         res = requests.post(f"http://localhost:{porta_target}/nodes/register", json={"nodes": nodi_list})
        #         print(f"\n[Risposta dal Nodo {porta_target}]: {res.json()['message']}")
        #     except requests.exceptions.ConnectionError:
        #         print(f"\n[Errore] Impossibile connettersi al Nodo {porta_target}. È acceso?")

        elif scelta == '1':
            nodi_input = input("Inserisci le porte di TUTTI i nodi da connettere tra loro (es. 5001 5002 5003): ")
            porte = nodi_input.split()
            
            if len(porte) < 2:
                print("⚠️ Inserisci almeno 2 porte per creare una rete.")
                continue
                
            # Creiamo la lista completa degli indirizzi URL
            tutti_i_nodi = [f"http://localhost:{p}" for p in porte]
            
            print("\n🌐 Creazione della rete P2P in corso...")
            
            for porta in porte:
                try:
                    res = requests.post(f"http://localhost:{porta}/nodes/register", json={"nodes": tutti_i_nodi})
                    if res.status_code == 201:
                        dati = res.json()
                        lista_peers = dati.get('peers') or dati.get('total_peers') or []
                        print(f"✅ Nodo {porta} aggiornato! Ora conosce altri {len(lista_peers)} nodi.")
                    else:
                        print(f"❌ Errore sul Nodo {porta}: {res.json().get('message', 'Errore sconosciuto')}")
                except requests.exceptions.ConnectionError:
                    print(f"⚠️ [Errore] Il Nodo {porta} non è raggiungibile. È acceso?")

        elif scelta == '2':
            porta_target = input("Da quale nodo vuoi far partire la transazione? (es. 5001): ")
            mittente = input("Mittente (es. Tommaso): ")
            destinatario = input("Destinatario (es. Luca): ")
            importo = float(input("Importo SID: "))
            
            tx_data = {"from": mittente, "to": destinatario, "amount": importo}
            
            try:
                res = requests.post(f"http://localhost:{porta_target}/transactions/new", json=tx_data)
                print(f"\n[Risposta dal Nodo {porta_target}]: {res.json()['message']}")
            except requests.exceptions.ConnectionError:
                print(f"\n[Errore] Impossibile connettersi al Nodo {porta_target}.")

        elif scelta == '3':
            porta_target = input("Quale nodo vuoi far faticare (mining)? (es. 5002): ")
            print(f"Richiesta di mining inviata al Nodo {porta_target}... attendere prego ⏳")
            try:
                res = requests.get(f"http://localhost:{porta_target}/mine")
                if res.status_code == 200:
                    data = res.json()
                    print(f"\n✅ {data['message']}")
                    print(f"Hash trovato: {data['block']['hash']}")
                    print(f"Statistiche mining: {data['stats']}")
                else:
                    print(f"\n⚠️ {res.json()['message']}")
            except requests.exceptions.ConnectionError:
                print(f"\n[Errore] Impossibile connettersi al Nodo {porta_target}.")

        elif scelta == '4':
            porta_target = input("A quale nodo vuoi chiedere il saldo? (es. 5003): ")
            utente = input("Di quale utente vuoi sapere il saldo? (es. Tommaso): ")
            
            try:
                res = requests.get(f"http://localhost:{porta_target}/balance/{utente}")
                if res.status_code == 200:
                    data = res.json()
                    print(f"\n💰 Saldo di {utente} (secondo il Nodo {porta_target}): {data['balance']} {data['currency']}")
            except requests.exceptions.ConnectionError:
                print(f"\n[Errore] Impossibile connettersi al Nodo {porta_target}.")

        elif scelta == '5':
            porta_target = input("A quale nodo vuoi chiedere la blockchain? (es. 5001): ")
            try:
                res = requests.get(f"http://localhost:{porta_target}/chain")
                if res.status_code == 200:
                    data = res.json()
                    print(f"\n🔗 Il Nodo {porta_target} ha una catena di {data['length']} blocchi.")
            except requests.exceptions.ConnectionError:
                print(f"\n[Errore] Impossibile connettersi al Nodo {porta_target}.")

        elif scelta == '6':
            porta_target = input("Verso quale nodo vuoi lanciare l'attacco? (es. 5001): ")
            print("Preparazione del blocco falso (hackeraggio in corso... 😈)")
            blocco_falso = {
                "index": 999,
                "timestamp": 123456789.0,
                "transactions": [{"from": "Luca", "to": "Hacker", "amount": 1000}],
                "previous_hash": "0000_falso_hash_inventato",
                "nonce": 0,
                "hash": "0000_super_hash_falso_ma_sembra_vero"
            }
            try:
                res = requests.post(f"http://localhost:{porta_target}/blocks/receive", json={"block": blocco_falso})
                print(f"\n🛡️ [Risposta del Nodo {porta_target}]: Stato {res.status_code} - {res.json()['message']}")
                if res.status_code == 400 or res.status_code == 409:
                    print("L'attacco è fallito! Il nodo ha rifiutato il blocco. La rete è sicura. ✅")
            except requests.exceptions.ConnectionError:
                print(f"\n[Errore] Impossibile connettersi al Nodo {porta_target}.")

        else:
            print("Opzione non valida, riprova.")

if __name__ == "__main__":
    main()