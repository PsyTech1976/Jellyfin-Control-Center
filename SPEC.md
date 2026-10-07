# SPEC.md - Specifiche Tecniche del Software
# Jellyfin Control Center (v2.3.0)

> **💡 Idea & Visione:** Concepito da **PsyTech76**  
> **Architettura & Sviluppo:** PyQt6, Python 3.10+, Architettura Modulare Asincrona con supporto IA  
> **Piattaforma Target:** Linux x86_64 (AppImage standalone, Docker & Installazioni Native)  
> **Licenza:** Open Source (GPLv3 / MIT compatibile)  
> **Repository Ufficiale:** [https://github.com/PsyTech1976/Jellyfin-Control-Center](https://github.com/PsyTech1976/Jellyfin-Control-Center)

---

## 1. INTRODUZIONE E SCOPO DEL PROGETTO (PROJECT SCOPE)

### 1.1 Descrizione Generale
**Jellyfin Control Center** è una suite grafica desktop progettata per la gestione centralizzata, il monitoraggio delle risorse a impatto zero, la diagnostica delle sessioni utente, l'automazione del ciclo di vita (installazione, manutenzione, backup/ripristino) e la configurazione avanzata dei plugin per **Jellyfin Media Server** in ambienti Linux.

### 1.2 Obiettivi Primari
- **Centralizzazione:** Riunire in un'unica interfaccia reattiva tutte le operazioni tipicamente svolte da terminale o browser.
- **Architettura a Impatto Zero (Zero-Impact):** Garantire che nessun processo di monitoraggio consumi cicli di CPU o GPU mentre l'utente guarda contenuti multimediali o utilizza altre sezioni del sistema.
- **Universalità Multi-Utente e Multi-Distro:** Funzionamento autonomo e portabile su qualsiasi distribuzione Linux senza dipendere da percorsi assoluti cablati o da specifici utenti locali.
- **Portabilità e Integrazione Desktop:** Distribuzione tramite pacchetto autonomo **AppImage** x86_64 integrabile nativamente nei menu di sistema XDG e nella barra delle applicazioni con un solo clic.

---

## 2. REQUISITI DI SISTEMA E DEPENDENCIES

### 2.1 Requisiti Software Host
- **Sistema Operativo:** Linux x86_64 (kernel >= 5.10). Supporto testato su Arch Linux / CachyOS, Debian, Ubuntu, Fedora, openSUSE.
- **Interprete:** Python >= 3.10 (pienamente compatibile con Python 3.14).
- **Display Server:** Supporto trasparente sia per **Wayland** che per **X11**.

### 2.2 Dipendenze Python (`requirements.txt`)
- `PyQt6` (>= 6.4.0): Framework GUI, gestione eventi, networking IPC locale e threading.
- `psutil` (>= 5.9.0): Acquisizione telemetrica non invasiva per CPU e memoria RAM.

### 2.3 Dipendenze Esterne di Sistema (Opzionali/Rilevate a Runtime)
- `docker` e `docker compose`: Per la gestione del container Jellyfin.
- `nvidia-smi` / driver NVIDIA: Per la telemetria GPU e transcodifica hardware NVENC/NVDEC.
- `update-desktop-database`: Per l'aggiornamento dinamico del menu delle applicazioni XDG.
- `appimagetool`: Per la compilazione del pacchetto autonomo AppImage.

---

## 3. ARCHITETTURA SOFTWARE E PATTERN DI DESIGN

```
+------------------------------------------------------------------------+
|                       Jellyfin Control Center                          |
|                             (PyQt6 GUI)                                |
+------------------------------------------------------------------------+
       |                  |                  |                  |
       v                  v                  v                  v
+--------------+   +--------------+   +--------------+   +--------------+
|  QLocalIPC   |   |   QThread    |   |     i18n     |   | XDG Desktop  |
| Single-Inst. |   | Async Workers|   | Translations |   | Integration  |
+--------------+   +--------------+   +--------------+   +--------------+
       |                  |                  |                  |
       v                  v                  v                  v
[Socket IPC]       [Docker / REST]    [5 Lingue IT/EN]  [~/.local/share]
```

### 3.1 Pattern Architetturale
- **Model-View-Controller (MVC) / Event-Driven:** L'interfaccia utente comunica con i backend operativi esclusivamente tramite segnali e slot Qt (`pyqtSignal`), evitando blocchi del thread principale (UI Thread).
- **Asincronia e Concorrenza:** Tutte le operazioni I/O pesanti (analisi librerie, download plugin, backup/ripristino compresso, installazione pacchetti) sono delegate a classi dedicate derivate da `QThread`.

### 3.2 Meccanismo a Istanza Singola (Runtime Single-Instance)
- All'avvio dell'applicazione viene interrogato il socket locale di dominio UNIX:  
  `jellyfin_control_center_single_instance_socket`
- Se un processo è già in ascolto, la nuova istanza invia il comando di risveglio `ACTIVATE\n` e termina immediatamente con codice `0`.
- L'istanza preesistente riceve l'evento, invoca `showNormal()`, `raise_()` e `activateWindow()`, portando la finestra in primo piano.
- In caso di chiusura imprevista precedente, `QLocalServer.removeServer()` bonifica automaticamente i file socket orfani.

### 3.3 Regola dei Percorsi Dinamici (Zero Hardcoding)
- Nessun percorso o utente è cablato nel sorgente.
- Risoluzione dinamica della home utente tramite `os.path.expanduser("~")`.
- Identificazione dell'ambiente tramite `$HOME`, `$USER` e `getpass.getuser()`.
- Il template `docker-compose.yml` adotta variabili d'ambiente generiche `${HOME:-~}` ed esempi espandibili.

### 3.4 Accesso ai Dati SQLite e Concorrenza
- L'interrogazione diretta dei database Jellyfin (`jellyfin.db`, `introskipper-v2.db`) avviene unicamente in modalità **sola lettura**:
  ```python
  uri = f"file:{db_path}?mode=ro"
  sqlite3.connect(uri, uri=True, timeout=1.5)
  ```
- Questo previene qualsiasi interferenza, blocco (table lock) o corruzione con i processi del demone Jellyfin in esecuzione.

---

## 4. SPECIFICHE FUNZIONALI DEI MODULI

### 4.1 Modulo 1: Controllo Server & Dashboard (`Tab 1`)
- **Badge di Stato in Tempo Reale:** Rileva se il server è `IN ESECUZIONE` (verde), `ARRESTATO` (rosso) o `IN ATTESA` (giallo).
- **Ciclo di Vita:** Pulsanti dedicati per *Avvio*, *Arresto*, *Riavvio* a caldo.
- **Connessione Web:** Pulsante diretto per lanciare `http://localhost:8096` nel browser predefinito.
- **Rilevamento IP di Rete:** Calcolo automatico dell'indirizzo IP locale (PC) e dell'IP LAN per consentire la connessione immediata da client esterni (TV, smartphone, tablet), con pulsanti di copia rapida negli appunti.
- **Scorciatoie Cartelle Multimediali:** Apertura istantanea delle cartelle multimediali utente (`~/Video`, `~/Musica`) nel gestore file predefinito.
- **Integrazione di Sistema XDG:**
  - Pulsante toggle `📌 Aggiungi al Menu di Sistema` / `🗑️ Rimuovi dal Menu di Sistema`.
  - Installazione/rimozione di `jellyfin-control-center.desktop` in `~/.local/share/applications/` e delle icone PNG in `~/.local/share/icons/hicolor/256x256/apps/`.
  - Aggiornamento dinamico del catalogo desktop tramite `update-desktop-database`.
  - Riconoscimento immediato nei launcher di sistema (KDE KRunner, Kickoff, GNOME Shell) e supporto all'ancoraggio su taskbar/dock.
  - Impostazione di `setDesktopFileName("jellyfin-control-center")` e `StartupWMClass` per il raggruppamento finestra sia sotto Wayland che X11.
- **Server Logs:** Visualizzatore integrato degli ultimi log del container Docker con pulsante di aggiornamento manuale.

### 4.2 Modulo 2: Dispositivi & Sessioni Live (`Tab 2`)
- **Monitoraggio Sessioni Attive:** Interrogazione periodica dell'endpoint REST Jellyfin `/Sessions`.
- **Dati Tracciati:** Nome utente, Dispositivo/Client (es. Jellyfin Web, Android TV, Infuse), Media in riproduzione, Durata temporale della sessione.
- **Riconoscimento Transcodifica:** Identifica se il flusso è riprodotto in `Direct Play` (nessun sovraccarico) o se è in corso una `Transcodifica Hardware` (con passthrough GPU).
- **Vista Terminale / Raw JSON:** Selettore per alternare tra la tabella grafica formattata e i dati JSON grezzi.

### 4.3 Modulo 3: Monitor Hardware a Impatto Zero (`Tab 3`)
- **Principio Zero-Overhead:** Il polling delle risorse hardware (`hw_timer`) viene attivato **esclusivamente** se l'utente sta visualizzando fisicamente la scheda Hardware ed ha abilitato la spunta di monitoraggio. Quando l'utente cambia scheda o minimizza, il consumo di risorse scende a 0%.
- **CPU & RAM:** Telemetria percentuale di utilizzo e memoria fisica allocata (`psutil`).
- **GPU Telemetry:**
  - NVIDIA: Interrogazione non bloccante via `nvidia-smi` per VRAM occupata, temperatura (°C), assorbimento energetico (Watt) e frequenze di clock.
  - Supporto predisposto per telemetria VAAPI / AMD / Intel.
- **Container Stats:** Consumo isolato del processo Jellyfin rispetto al totale di sistema.

### 4.4 Modulo 4: Gestione Installazione Multi-Distro (`Tab 4`)
- **Riconoscimento Distribuzione:** Identifica la distribuzione Linux in uso analizzando `/etc/os-release` (Arch Linux / CachyOS, Debian, Ubuntu, Fedora, openSUSE).
- **Elevazione Privilegi Sicura:** Dialogo grafico per l'immissione della password di root/sudo (`QLineEdit.EchoMode.Password`) con pre-validazione immediata (`sudo -k -S true`). La password risiede unicamente in RAM durante l'operazione.
- **Installazione Guidata da Zero:** Configurazione di Docker, avvio del demone di sistema, associazione dell'utente al gruppo `docker`, installazione del GPU Toolkit per passthrough hardware.
- **Disinstallazione Atomica a Specchio:** Rimozione completa del container, immagini Docker e repository ausiliari, con opzione per conservare o purgare i dati multimediali.

### 4.5 Modulo 5: Backup & Ripristino Compresso (.zip) (`Tab 5`)
- **Creazione Snapshot:** Generazione di archivi compressi standard `.zip` contenenti i database utenti, le impostazioni e le configurazioni di Jellyfin.
- **Modalità Veloce vs Integrale:**
  - Esclusione cartella metadata (~9 GB): genera un backup essenziale (~60 MB) in soli 2 secondi.
  - Inclusione metadata: crea uno snapshot monolitico integrale di ogni singola miniatura e locandina.
- **Monitoraggio in Streaming:** Calcolo dinamico della velocità di compressione (MB/s), percentuale e tempo residuo stimato (ETA).
- **Protocollo a Zero Residui (Zero Residue Rule):** In caso di annullamento manuale o interruzione, qualsiasi file temporaneo o parziale viene immediatamente cancellato da disco.

### 4.6 Modulo 6: Gestione Plugin - Intro Skipper & Trickplay (`Tab 6`)
Organizzato in sotto-schede specializzate con timer attivo esclusivamente durante la consultazione:

#### A. Sottoscheda Intro Skipper
- Download manifest e pacchetti ufficiali da GitHub o installazione da `.zip` locale.
- Disinstallazione sicura con opzione di conservazione database impronte (`introskipper-v2.db`).
- Controllo via REST dell'attività `IntroSkipperDetectSegmentsTask` (Avvia / Ferma analisi).
- Contatori live: File processati, file rimanenti, totale elementi e segmenti intro/crediti identificati.
- Registro eventi live con timestamp e auto-scorrimento.

#### B. Sottoscheda Trickplay (Miniature di Scorrimento & Scrubbing)
- **Verifica Preventiva:** Controlla l'esistenza del modulo in `config/plugins/` e del task prima dell'installazione per prevenire sovrascritture accidentali.
- **Controllo Task:** Avvio e interruzione manuale del task ufficiale `RefreshTrickplayImages` (`64f5f44cd30dc273cb9890205473bbcc`).
- **Reset e Ricostruzione Libreria:**
  1. Arresto sicuro dell'attività in corso.
  2. Pulizia fisica della cache miniature (`config/data/trickplay/`).
  3. Reset dei metadati nel database Jellyfin (`DELETE FROM TrickplayInfos;`).
  4. Riavvio pulito della scansione per rigenerare le miniature da zero.
- **Pannello Web:** Pulsante per aprire direttamente la configurazione Trickplay nel browser (`/web/#/trickplay`).
- **Statistiche & Log:** Conteggio media indicizzati, media rimanenti, spazio su disco occupato dalla cache (MB/GB) e parsing log in tempo reale.

### 4.7 Modulo 7: Internazionalizzazione (i18n) e Guida HTML
- **5 Lingue Supportate:** Italiano (`it`), Inglese (`en`), Francese (`fr`), Tedesco (`de`), Spagnolo (`es`).
- **Rilevamento Lingua Sistema:** Lettura del locale OS (`QLocale.system().name()`) al primo avvio, con fallback automatico in Inglese.
- **Traduzione Dinamica a Runtime:** Selettore a tendina nell'intestazione che aggiorna istantaneamente tutti i testi, tabelle, tooltip e dialoghi senza richiedere il riavvio del programma.
- **Manuale Utente HTML Integrato:** Finestra separata dedicata (`QTextBrowser`) con documentazione completa, badge visivi e spiegazione dettagliata di ogni singolo comando.
- **Dialogo Informazioni ("About"):** Attribuzione del progetto (*"Nato da un'idea e visione di PsyTech76"*), framework PyQt6 e licenza open source.

---

## 5. SICUREZZA, PRIVACY E GESTIONE DELLE CREDENZIALI

1. **Zero Credenziali Hardcoded:** Nessuna password, token privato o chiave API è memorizzata all'interno del codice sorgente o nei file di configurazione statici.
2. **Isolamento della Password di Root:**
   - La password amministrativa viene richiesta unicamente nei processi di installazione/disinstallazione di sistema.
   - Non viene mai scritta su file di log o memorizzata su disco fisso.
   - Viene convogliata direttamente allo standard input di `sudo -S` e scartata immediatamente al termine del processo.
3. **Riservatezza dei Dati Locali:**
   - Il codice sorgente e la documentazione non contengono dati identificativi personali dell'autore (nomi utente locali, etichette di dischi fissi personali, indirizzi IP privati).

---

## 6. SPECIFICHE DI COMPILAZIONE, PACKAGING E RILASCIO

### 6.1 Struttura del Repository
```
Jellyfin_Control_Center_Project/
├── desktop/
│   └── Jellyfin Control Center.desktop   # Lanciatore conforme XDG
├── dist/
│   └── Jellyfin_Control_Center-x86_64.AppImage # Binario compilato
├── docker/
│   └── docker-compose.yml                # Template Docker Compose
├── docs/
│   ├── ARCHITETTURA_E_GUIDA_SVILUPPO.txt # Documentazione tecnica
│   ├── CHANGELOG.txt                     # Cronologia versioni
│   ├── GUIDA_RAPIDA.txt                  # Guida sintetica per l'utente
│   └── NOTE_PER_LA_IA.txt                # Linee guida per futuri modelli IA
├── icons/
│   ├── jellyfin-control.png              # Icona applicazione 256x256
│   ├── jellyfin-control.svg              # Icona vettoriale
│   └── jellyfin.svg                      # Logo Jellyfin
├── scripts/
│   ├── build_appimage.sh                 # Script di packaging AppImage
│   └── publish_to_github.py              # Script di rilascio GitHub
├── src/
│   ├── jellyfin_manager.py               # Core applicativo e GUI (PyQt6)
│   └── translations.py                   # Dizionario i18n e Guida HTML
├── README.md                             # Presentazione bilingue per GitHub
├── README.txt                            # Presentazione in formato testo
├── requirements.txt                      # Dipendenze Python
└── SPEC.md                               # Questo documento di specifiche
```

### 6.2 Flusso di Generazione AppImage (`scripts/build_appimage.sh`)
1. Crea la cartella temporanea `build_tmp/AppDir`.
2. Copia i sorgenti (`src/*.py`), le icone e il file `.desktop`.
3. Integra le librerie di runtime necessarie (`PyQt6`, `psutil`).
4. Genera il lanciatore `AppRun` impostando `PYTHONPATH`, `LD_LIBRARY_PATH` e `QT_PLUGIN_PATH`.
5. Compila l'immagine squashfs compressa con `appimagetool` (architettura `x86_64`).
6. Produce il binario finale: `dist/Jellyfin_Control_Center-x86_64.AppImage` (eseguibile autonomo, chmod +x).

### 6.3 Automazione Rilascio GitHub (`scripts/publish_to_github.py`)
- Gestione autenticazione sicura tramite GitHub CLI (`gh`).
- Creazione e sincronizzazione del branch `main`.
- Creazione della Release ufficiale con note bilingue (Italiano/Inglese).
- Upload automatico degli asset di distribuzione:
  - `Jellyfin_Control_Center-x86_64.AppImage`
  - `Jellyfin_Control_Center_AppImage.zip`
  - `Jellyfin_Control_Center_Progetto_Sorgenti.zip`

---

## 7. CRONOLOGIA REVISIONI SPECIFICA

| Versione | Data | Principali Aggiunte nelle Specifiche |
|---|---|---|
| **v1.0 - v1.5** | Ottobre 2026 | Gestione Docker, monitoraggio hardware on-demand a impatto zero, rilevamento sessioni live e transcodifica. |
| **v2.0** | Ottobre 2026 | Automazione installazione multi-distro con elevazione sudo sicura, sistema di backup e ripristino compresso (.zip) con regola zero residui. |
| **v2.1** | Ottobre 2026 | Gestione plugin Intro Skipper con interfaccia REST, conteggi media e log dedicati. |
| **v2.2** | Ottobre 2026 | Esecuzione a singola istanza (IPC socket), modulo Trickplay completo (Start/Stop, reset libreria, web), localizzazione a 5 lingue e guida HTML integrata. |
| **v2.3** | Ottobre 2026 | Pulsante integrazione di sistema XDG Desktop (app menu e taskbar/dock pinning), architettura universale multi-utente senza percorsi cablati, formalizzazione documentale `SPEC.md`. |
