# 🍎 SidroCoin

**Progetto per l'esame di Sistemi Distribuiti e Paralleli** *Sviluppato da: [Tuo Nome] e [Nome del Collega]*

SidroCoin è un sistema didattico di criptovaluta basato su architettura blockchain. Il progetto non è concepito come una vera criptovaluta da lanciare sul mercato, ma come una simulazione pratica per esplorare e implementare i concetti chiave dei **sistemi distribuiti** (consenso, replica, topologia P2P) e del **calcolo parallelo** (Proof-of-Work multicore).

---

## ✨ Architettura e Funzionalità Principali

Il progetto rispetta i due pilastri richiesti dall'esame:

### 1. La Componente Parallela (Mining Proof-of-Work)
L'algoritmo di consenso prevede la ricerca di un *nonce* affinché l'hash del blocco (SHA-256) rispetti una determinata difficoltà (Proof-of-Work). Poiché si tratta di un task *CPU-bound*, è stato parallelizzato:
* Utilizzo della libreria `multiprocessing` per bypassare il GIL di Python.
* Creazione di molteplici *worker* concorrenti (configurabili dal file `config.py`).
* Ogni worker esplora uno spazio di nonce differente (tramite salti temporali/interleaving) per evitare sovrapposizioni.
* Uso di `multiprocessing.Queue` per la comunicazione IPC e `Event` per interrompere i worker sconfitti non appena uno trova la soluzione.

### 2. La Componente Distribuita (Rete P2P e Consenso)
Il sistema simula una rete Peer-to-Peer dove ogni nodo è un server web Flask indipendente.
* **Isolamento dei Dati:** Ogni nodo mantiene la propria versione del ledger (`chain_<porta>.json`) e della propria mempool (`mempool_<porta>.json`).
* **Gossip Protocol (Broadcast):** Appena un nodo riceve una transazione o mina un blocco, lo inoltra immediatamente in broadcast a tutti i nodi conosciuti nella rete.
* **Risoluzione dei Conflitti (Longest Chain Rule):** Se due nodi minano contemporaneamente, il sistema gestisce la *Race Condition* scartando il blocco arrivato in ritardo (Blocco Orfano) e adottando la catena valida più lunga.
* **Resistenza agli Attacchi:** I nodi validano rigorosamente i blocchi ricevuti. I tentativi di inviare blocchi alterati o non agganciati all'hash precedente vengono rifiutati con un errore HTTP 400.

### 3. Logica Blockchain "Core"
* **Wallet e Saldi Dinamici:** Come in Bitcoin, i saldi non sono variabili statiche. Vengono calcolati "al volo" scorrendo l'intero storico della blockchain per prevenire la manomissione.
* **Mempool:** Le transazioni valide non ancora minate vengono parcheggiate in attesa di elaborazione.
* **Mining Reward:** Il sistema inietta automaticamente una transazione (di default 10 SID) dal mittente speciale `SYSTEM` al nodo che chiude il blocco, incentivando la partecipazione.

---

## 🚀 Come testare il progetto (Guida per l'esame)

Per simulare l'intera rete decentralizzata sul proprio computer, il progetto è stato dotato di un'interfaccia Client (`client.py`) che fa da telecomando universale per interagire con i nodi.

### Requisiti
Assicurati di aver installato le dipendenze necessarie:
```bash
pip install flask requests