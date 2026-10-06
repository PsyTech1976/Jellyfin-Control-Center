====================================================================================================
                        JELLYFIN CONTROL CENTER - PROGETTO COMPLETO
====================================================================================================
Pacchetto sorgente, documentazione, asset e script di compilazione per Jellyfin Control Center.
Versione: 2.3.0
Ideato da: PsyTech76
====================================================================================================

BENVENUTO!
Questo archivio contiene l'intero progetto dell'applicazione "Jellyfin Control Center", corredato
da codice sorgente completamente commentato in italiano, script per ricreare il pacchetto AppImage,
risorse grafiche e una documentazione dettagliata sia per esseri umani che per futuri modelli di IA.

NOVITÀ VERSIONE 2.3.0:
- Integrazione di Sistema con un Clic: pulsante per aggiungere o rimuovere l'applicazione dal menu
  di sistema e permetterne il fissaggio alla barra delle applicazioni / dock (conforme allo standard XDG).
- Architettura Universale Multi-Utente: codice completamente indipendente dall'ambiente o utente locale,
  con risoluzione dinamica delle cartelle home (~) e delle variabili di ambiente.
- Singola istanza a runtime (Single Instance IPC socket).
- Gestione plugin Trickplay (verifica preventiva, start/stop, reset/ricostruzione, pannello web).
- Preservazione integrale di Intro Skipper.
- Localizzazione a 5 lingue (Italiano, Inglese, Francese, Tedesco, Spagnolo) con rilevamento lingua sistema.
- Sezione Info sul programma (crediti PsyTech76, AI e Qt6).
- Guida completa in formato HTML consultabile in finestra separata.

CONTENUTO DELLE CARTELLE:
----------------------------------------------------------------------------------------------------
- src/
  * jellyfin_manager.py : Sorgente principale dell'applicazione (PyQt6).
  * translations.py     : Modulo di localizzazione i18n e guida HTML multilingua.

- docs/
  Documentazione tecnica ed esplicativa:
  * ARCHITETTURA_E_GUIDA_SVILUPPO.txt : Architettura dell'applicazione, single instance, plugin, threading.
  * NOTE_PER_LA_IA.txt                : Istruzioni speciali e vincoli critici per future IA.
  * GUIDA_RAPIDA.txt                  : Manuale utente sintetico per eseguire e usare la GUI.
  * CHANGELOG.txt                     : Storico delle versioni e delle modifiche implementate.

- scripts/
  * build_appimage.sh   : Script bash per compilare l'eseguibile autonomo .AppImage per Linux x86_64.

- docker/
  * docker-compose.yml  : Configurazione Docker con passthrough hardware GPU (NVENC/NVDEC/VAAPI).

- desktop/
  * Jellyfin Control Center.desktop : File lanciatore standard XDG.

- icons/
  * jellyfin-control.png, jellyfin-control.svg, jellyfin.svg.


COME AVVIARE L'APPLICAZIONE DAI SORGENTI:
----------------------------------------------------------------------------------------------------
1. pip install -r requirements.txt
2. python3 src/jellyfin_manager.py


COME RICOMPILARE IL PACCHETTO STANDALONE APPIMAGE:
----------------------------------------------------------------------------------------------------
Esegui:
   ./scripts/build_appimage.sh
L'AppImage aggiornata verrà generata nella cartella 'dist/'.
====================================================================================================
