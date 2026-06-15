
#file solo per test, forse dopo si potrà cancellare
#runnare da terminale con 3 terminali diversi node.py scrivnedo il comando "python node.py 500X" (al posto di X mettere 1/2/3)
import requests
import time

print("--- 1. CONNESSIONE DELLA RETE ---")
# Diciamo al Nodo 5001 che esistono il 5002 e il 5003
requests.post("http://localhost:5001/nodes/register", json={"nodes": ["http://localhost:5002", "http://localhost:5003"]})
# Diciamo al Nodo 5002 che esistono il 5001 e il 5003
requests.post("http://localhost:5002/nodes/register", json={"nodes": ["http://localhost:5001", "http://localhost:5003"]})
# Diciamo al Nodo 5003 che esistono il 5001 e il 5002
requests.post("http://localhost:5003/nodes/register", json={"nodes": ["http://localhost:5001", "http://localhost:5002"]})
print("Nodi registrati con successo!")
time.sleep(2)

print("\n--- 2. CREAZIONE TRANSAZIONE SUL NODO 5001 ---")
# L'utente si connette SOLO al nodo 5001 per fare la transazione
tx_data = {
    "from": "Tommaso",
    "to": "Luca",
    "amount": 15
}
res = requests.post("http://localhost:5001/transactions/new", json=tx_data)
print("Risposta dal Nodo 5001:", res.json()["message"])
print("-> Ora controlla i file mempool_5002.json e mempool_5003.json: dovrebbero avere la transazione grazie al broadcast!")
time.sleep(5) # Pausa di 5 secondi per darti il tempo di guardare i file

print("\n--- 3. MINING SUL NODO 5002 ---")
# Immaginiamo che il Miner del nodo 5002 faccia partire il calcolo
print("Il Nodo 5002 sta minando...")
res = requests.get("http://localhost:5002/mine")
print("Risposta dal Nodo 5002:", res.json()["message"])
print("-> Guarda i terminali dei nodi 5001 e 5003: dovrebbero aver stampato di aver ricevuto e accettato il blocco!")