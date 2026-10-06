#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================================================
PROGETTO: Jellyfin Control Center (Gestore Multimediale e Pannello di Controllo per Linux)
====================================================================================================

DESCRIZIONE GENERALE:
---------------------
Jellyfin Control Center è un'applicazione desktop grafica nativa sviluppata con Python 3 e PyQt6.
È stata progettata specificamente per l'ambiente Linux (testata su CachyOS / Arch Linux, ma 
compatibile con Ubuntu, Debian, Fedora, openSUSE) per consentire all'utente di:
  1. Avviare, arrestare, riavviare e monitorare lo stato di Jellyfin Media Server (gestito via Docker).
  2. Ispezionare in tempo reale utenti e dispositivi connessi (con indicazione di cosa stanno riproducendo).
  3. Monitorare a richiesta l'utilizzo hardware (CPU, GPU NVIDIA RTX con VRAM/temp/watt, RAM di sistema e container)
     con la garanzia rigorosa di ZERO CONSUMO a riposo (nessun ciclo CPU sprecato quando non visualizzato).
  4. Installare da zero o disinstallare Jellyfin con rilevamento automatico del package manager di sistema
     e richiesta sicura delle credenziali di root (sudo).
  5. Eseguire il backup e ripristino (.zip) compresso dei dati utente con calcolo in tempo reale di
     percentuale, velocità (MB/s), tempo rimanente stimato (ETA) e cancellazione pulita (zero residui) in caso di abort.

ARCHITETTURA APPLICATIVA:
-------------------------
- Interfaccia Grafica (GUI): PyQt6 (QMainWindow, QTabWidget, QTableWidget, QProgressBar, QStackedWidget).
- Multithreading: Tutti i compiti lunghi (Docker, Backup, Ripristino, Installazione) girano in sottoclassi
  di QThread dedicate, per non congelare MAI l'interfaccia utente.
- Monitoraggio Hardware: Usa 'psutil' per CPU/RAM e il comando nativo 'nvidia-smi' per la GPU.
- Comunicazione Jellyfin: Richieste HTTP REST alle API di Jellyfin (/Sessions) autenticate tramite Token.
- Integrazione Desktop: Icone e file standard XDG (.desktop) posizionati in ~/.local/share/applications e Desktop.

DIPENDENZE PYTHON RICHIESTE:
----------------------------
- python >= 3.10
- PyQt6
- psutil
====================================================================================================
"""

import sys
import os
import subprocess
import json
import socket
import sqlite3
import datetime
import time
import shutil
import zipfile
import urllib.request
import urllib.error
import re
import glob

# Moduli di rete per gestione istanza singola a runtime
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

try:
    import translations
    from translations import SUPPORTED_LANGUAGES, STRINGS, t, get_about_info_html, get_user_guide_html
except ImportError:
    from src import translations
    from src.translations import SUPPORTED_LANGUAGES, STRINGS, t, get_about_info_html, get_user_guide_html

# Librerie per il monitoraggio delle risorse di sistema
import psutil

# Moduli grafici PyQt6
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QPlainTextEdit, QProgressBar,
    QGridLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QStackedWidget, QToolTip, QMessageBox,
    QFileDialog, QInputDialog, QLineEdit, QDialog, QTextBrowser, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QUrl, QLocale
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor, QDesktopServices

# ==================================================================================================
# COSTANTI E PERCORSI GLOBALI DEL SISTEMA
# ==================================================================================================
# Percorso base in cui risiedono i file di Jellyfin, la configurazione e i dati
JELLYFIN_DIR = os.path.expanduser("~/jellyfin")

# Directory per gli script eseguibili e i comandi CLI dell'utente
LOCAL_BIN = os.path.expanduser("~/.local/bin")

# Percorsi delle icone grafiche dell'applicazione
ICON_PATH = os.path.expanduser("~/.local/share/icons/jellyfin-control.png")
FALLBACK_ICON = os.path.expanduser("~/.local/share/icons/jellyfin.svg")

# Database SQLite interno di Jellyfin (usato per recuperare o registrare le chiavi API)
DB_PATH = os.path.join(JELLYFIN_DIR, "config/data/jellyfin.db")

# Percorsi e configurazioni specifici per il plugin Intro Skipper
INTRO_SKIPPER_URL = "https://github.com/intro-skipper/intro-skipper/releases/download/12.0/v12.0.4.0/intro-skipper-v12.0.4.0.zip"
INTRO_SKIPPER_DIR = os.path.join(JELLYFIN_DIR, "config/plugins/Intro Skipper_12.0.4.0")
INTRO_SKIPPER_DATA_DIR = os.path.join(JELLYFIN_DIR, "config/data/introskipper")
INTRO_SKIPPER_DB = os.path.join(INTRO_SKIPPER_DATA_DIR, "introskipper-v2.db")

# Percorsi e costanti specifici per il plugin e modulo Trickplay
TRICKPLAY_DATA_DIR = os.path.join(JELLYFIN_DIR, "config/data/trickplay")
TRICKPLAY_PLUGIN_DIR = os.path.join(JELLYFIN_DIR, "config/plugins/Trickplay")
SINGLE_INSTANCE_SOCKET_NAME = "jellyfin_control_center_single_instance_socket"



# ==================================================================================================
# FUNZIONI DI UTILITÀ DI RETE E SISTEMA
# ==================================================================================================

def get_lan_ip():
    """
    Rileva l'indirizzo IPv4 locale primario del computer sulla rete LAN/Wi-Fi domestica.
    
    Metodologia:
      1. Tenta prima tramite il comando di sistema 'ip -4 addr show scope global'.
      2. In caso di fallimento, crea un socket UDP effimero (senza inviare pacchetti)
         per scoprire l'interfaccia di routing verso l'esterno.
      3. Se la rete non è attiva, restituisce il loopback di fallback '127.0.0.1'.
    
    Returns:
        str: Indirizzo IP (es. '192.168.1.100')
    """
    try:
        res = subprocess.check_output(
            ["bash", "-c", "ip -4 addr show scope global | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}' | head -n 1"],
            text=True
        ).strip()
        if res:
            return res
    except Exception:
        pass

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_or_create_api_key():
    """
    Recupera una chiave API autorizzata dal database SQLite di Jellyfin (jellyfin.db)
    oppure ne inserisce una predefinita per consentire all'applicazione di interrogare
    gli endpoint amministrativi (come la lista delle sessioni e dei dispositivi connessi).
    
    Returns:
        str: Token esadecimale valido per l'autenticazione alle API.
    """
    token_default = "1b8dba43ee8b564c1ca4dbb6ff6311c9"
    if not os.path.exists(DB_PATH):
        return token_default

    try:
        conn = sqlite3.connect(DB_PATH, timeout=2)
        c = conn.cursor()
        c.execute("SELECT AccessToken FROM ApiKeys WHERE Name = 'Jellyfin Control Center' LIMIT 1")
        row = c.fetchone()
        if row and row[0]:
            conn.close()
            return row[0]

        # Se non esiste ancora, registriamo il token per questa app
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        c.execute(
            "INSERT INTO ApiKeys (DateCreated, DateLastActivity, Name, AccessToken) VALUES (?, ?, ?, ?)",
            (now, now, "Jellyfin Control Center", token_default)
        )
        conn.commit()
        conn.close()
        return token_default
    except Exception:
        return token_default





def get_system_language():
    """
    Rileva automaticamente la lingua del sistema operativo host.
    Se la lingua e supportata (Italiano, Inglese, Francese, Tedesco, Spagnolo),
    la imposta come predefinita; in caso contrario, imposta l'Inglese come fallback.
    
    Returns:
        str: Codice lingua a 2 lettere ('it', 'en', 'fr', 'de', 'es').
    """
    try:
        sys_code = QLocale.system().name().lower().split("_")[0]
        if sys_code in SUPPORTED_LANGUAGES:
            return sys_code
    except Exception:
        pass
    env_lang = os.environ.get("LANG", "en").lower()[:2]
    if env_lang in SUPPORTED_LANGUAGES:
        return env_lang
    return "en"


def get_recent_trickplay_logs(max_lines=200):
    """
    Scansiona i log di Jellyfin alla ricerca di eventi riguardanti la generazione
    delle immagini di scorrimento e miniature Trickplay.
    """
    log_dir = os.path.join(JELLYFIN_DIR, "config/log")
    if not os.path.exists(log_dir):
        return []
    log_files = sorted(glob.glob(os.path.join(log_dir, "log_*.log")), key=os.path.getmtime, reverse=True)
    if not log_files:
        return []
    entries = []
    pattern = re.compile(
        r"^\[(?P<dt>\d{4}-\d{2}-\d{2}\s+(?P<time>\d{2}:\d{2}:\d{2}))(?:\.\d+)?\s+[+-]\d{2}:\d{2}\]\s+\[(?P<lvl>[A-Z]{3})\].*?(?P<msg>.*Trickplay.*)$",
        re.IGNORECASE
    )
    for lf in log_files[:2]:
        try:
            with open(lf, "r", encoding="utf-8", errors="ignore") as f:
                for line in f.readlines()[-max_lines:]:
                    m = pattern.match(line.strip())
                    if m:
                        dt = m.group("dt")
                        msg = m.group("msg").strip()
                        entries.append(f"[{dt}] [TRICKPLAY] {msg}")
        except Exception:
            pass
    return entries[-150:]

def get_recent_plugin_logs(max_lines=300):
    """
    Scansiona gli ultimi file di log del server Jellyfin per estrarre in tempo reale
    gli eventi registrati dal plugin Intro Skipper (file analizzati, intro identificate,
    titoli di coda, recap e avvisi Chromaprint) corredati da data e ora precisi.
    
    Returns:
        list[str]: Elenco formattato degli ultimi eventi per la visualizzazione nella GUI.
    """
    log_dir = os.path.join(JELLYFIN_DIR, "config/log")
    if not os.path.exists(log_dir):
        return []

    log_files = sorted(glob.glob(os.path.join(log_dir, "log_*.log")), key=os.path.getmtime, reverse=True)
    if not log_files:
        return []

    raw_lines = []
    # Legge dagli ultimi due file di log per garantire continuita tra giorni consecutivi o riavvii
    for lf in log_files[:2]:
        try:
            with open(lf, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                raw_lines.extend(lines[-max_lines:])
        except Exception:
            pass

    parsed_entries = []
    pattern = re.compile(
        r"^\[(?P<dt>\d{4}-\d{2}-\d{2}\s+(?P<time>\d{2}:\d{2}:\d{2}))(?:\.\d+)?\s+[+-]\d{2}:\d{2}\]\s+\[(?P<lvl>[A-Z]{3})\]\s+\[\d+\]\s+IntroSkipper\.(?P<comp>[^:]+):\s+(?P<msg>.*)$"
    )

    for line in raw_lines:
        m = pattern.match(line.strip())
        if m:
            dt = m.group("dt")
            lvl = m.group("lvl")
            msg = m.group("msg")
            comp = m.group("comp")

            if "BaseItemAnalyzerTask" in comp:
                parsed_entries.append(f"[{dt}] [ANALISI MEDIA] {msg}")
            elif "FFmpegService" in comp:
                file_name = msg.split("/")[-1].replace('""', '').strip()
                parsed_entries.append(f"[{dt}] [AUDIO FINGERPRINT] {file_name}")
            elif "QueueManager" in comp:
                parsed_entries.append(f"[{dt}] [CODA LIBRERIA] {msg}")
            elif "DetectSegmentsTask" in comp:
                parsed_entries.append(f"[{dt}] [STATO TASK] {msg}")
            else:
                parsed_entries.append(f"[{dt}] [{lvl}] {msg}")

    return parsed_entries[-200:]

def detect_distro():
    """
    Identifica la distribuzione Linux in uso analizzando il file standard '/etc/os-release'.
    Determina la famiglia di distribuzione (Arch, Debian/Ubuntu, RedHat/Fedora, openSUSE)
    e seleziona il gestore pacchetti appropriato con la stringa di comando necessaria
    per installare Docker e le dipendenze richieste.
    
    Returns:
        dict: Dizionario contenente nome, id, package manager e comando di installazione.
    """
    info = {
        "id": "unknown",
        "name": "Linux",
        "pkg_mgr": "unknown",
        "install_cmd": "",
        "id_like": ""
    }

    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                if line.startswith("ID="):
                    info["id"] = line.strip().split("=")[1].strip("\"'")
                elif line.startswith("PRETTY_NAME="):
                    info["name"] = line.strip().split("=")[1].strip("\"'")
                elif line.startswith("ID_LIKE="):
                    info["id_like"] = line.strip().split("=")[1].strip("\"'")

    id_val = (info.get("id", "") + " " + info.get("id_like", "")).lower()

    # Famiglia Arch Linux (CachyOS, Manjaro, EndeavourOS, Arch)
    if any(x in id_val for x in ["arch", "cachyos", "manjaro", "endeavouros"]):
        info["pkg_mgr"] = "pacman"
        info["install_cmd"] = "pacman -S --needed --noconfirm docker docker-compose python python-pyqt6 python-psutil"

    # Famiglia Debian / Ubuntu (Ubuntu, Debian, Linux Mint, Pop!_OS)
    elif any(x in id_val for x in ["ubuntu", "debian", "mint", "pop"]):
        info["pkg_mgr"] = "apt"
        info["install_cmd"] = "apt-get update && apt-get install -y docker.io docker-compose-v2 python3-pyqt6 python3-psutil"

    # Famiglia Red Hat / Fedora (Fedora, RHEL, CentOS, AlmaLinux, Rocky)
    elif any(x in id_val for x in ["fedora", "rhel", "centos", "nobara"]):
        info["pkg_mgr"] = "dnf"
        info["install_cmd"] = "dnf install -y docker docker-compose python3-pyqt6 python3-psutil"

    # Famiglia openSUSE (Leap, Tumbleweed)
    elif any(x in id_val for x in ["suse", "opensuse"]):
        info["pkg_mgr"] = "zypper"
        info["install_cmd"] = "zypper install -y docker docker-compose python3-qt6 python3-psutil"

    # Generico di fallback
    else:
        info["pkg_mgr"] = "generic"
        info["install_cmd"] = "docker docker-compose"

    return info


# ==================================================================================================
# WORKER MULTITHREADING (QTHREAD)
# ==================================================================================================

class CommandWorker(QThread):
    """
    Worker per l'esecuzione asincrona di comandi leggeri di gestione (Avvio, Arresto, Riavvio).
    Impedisce che la GUI si blocchi durante l'interazione con il demone Docker.
    
    Segnali:
      finished(bool success, str message): Emesso al completamento con l'esito e l'output.
    """
    finished = pyqtSignal(bool, str)

    def __init__(self, action_name):
        super().__init__()
        self.action_name = action_name

    def run(self):
        try:
            if self.action_name == "start":
                cmd = f"{LOCAL_BIN}/jellyfin-start --no-browser"
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                success = (res.returncode == 0)
                msg = res.stdout if success else res.stderr
                self.finished.emit(success, msg)

            elif self.action_name == "stop":
                cmd = f"{LOCAL_BIN}/jellyfin-stop"
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                success = (res.returncode == 0)
                msg = res.stdout if success else res.stderr
                self.finished.emit(success, msg)

            elif self.action_name == "restart":
                cmd = f"cd {JELLYFIN_DIR} && docker-compose restart"
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                success = (res.returncode == 0)
                msg = res.stdout if success else res.stderr
                self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, str(e))


class BackupWorker(QThread):
    """
    Worker per la creazione di archivi compressi (.zip) dei dati e configurazioni di Jellyfin.
    
    Caratteristiche salienti:
      - Streaming a blocchi: Non carica i file per intero in RAM ma legge in buffer da 128 KB.
      - Calcolo metriche live: Calcola dinamicamente percentuale, velocità (MB/s) ed ETA rimanente.
      - Annullamento atomico: Se l'utente preme 'Annulla', il thread intercetta l'evento,
        chiude l'handle del file e RIMUOVE IMMEDIATAMENTE il file .zip parziale,
        garantendo zero file orfani o residui sul disco.
      - Opzione Metadati: Permette di escludere la cartella 'metadata' (9 GB di locandine scaricate)
        per generare un backup essenziale quasi istantaneo (~60 MB compressi).
    """
    progress = pyqtSignal(int, int, int, float, float) # percent, bytes_done, total_bytes, speed, eta
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, target_zip_path, include_metadata=False):
        super().__init__()
        self.target_zip_path = target_zip_path
        self.include_metadata = include_metadata
        self._is_cancelled = False

    def cancel(self):
        """Richiede l'annullamento immediato del processo di compressione."""
        self._is_cancelled = True

    def run(self):
        try:
            self.log.emit("Analisi dei file e calcolo delle dimensioni...")
            
            # Elementi core indispensabili per il ripristino di utenti e preferenze
            source_items = [
                os.path.join(JELLYFIN_DIR, "config/config"),
                os.path.join(JELLYFIN_DIR, "config/data"),
                os.path.join(JELLYFIN_DIR, "config/plugins"),
                os.path.join(JELLYFIN_DIR, "docker-compose.yml"),
                os.path.join(JELLYFIN_DIR, "jellyfin_manager.py")
            ]

            # Inclusione opzionale delle locandine (~9 GB)
            if self.include_metadata and os.path.exists(os.path.join(JELLYFIN_DIR, "config/metadata")):
                source_items.append(os.path.join(JELLYFIN_DIR, "config/metadata"))

            files_to_zip = []
            total_bytes = 0

            # 1. Raccolta preliminare dei file e calcolo dimensione totale
            for item in source_items:
                if self._is_cancelled:
                    raise InterruptedError("Operazione annullata dall'utente.")
                if os.path.isfile(item):
                    sz = os.path.getsize(item)
                    files_to_zip.append((item, os.path.basename(item), sz))
                    total_bytes += sz
                elif os.path.isdir(item):
                    for root, dirs, filenames in os.walk(item):
                        if self._is_cancelled:
                            raise InterruptedError("Operazione annullata dall'utente.")
                        for fn in filenames:
                            fp = os.path.join(root, fn)
                            if os.path.islink(fp):
                                continue
                            try:
                                sz = os.path.getsize(fp)
                                rel = os.path.relpath(fp, JELLYFIN_DIR)
                                files_to_zip.append((fp, rel, sz))
                                total_bytes += sz
                            except Exception:
                                pass

            self.log.emit(f"Elementi totali trovati: {len(files_to_zip)} ({total_bytes / (1024*1024):.2f} MB non compressi)")
            self.log.emit(f"Creazione file archivio: {os.path.basename(self.target_zip_path)}")

            bytes_done = 0
            t_start = time.time()

            os.makedirs(os.path.dirname(os.path.abspath(self.target_zip_path)), exist_ok=True)

            # 2. Compressione in streaming con calcolo live di ETA e velocità
            with zipfile.ZipFile(self.target_zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=5) as zf:
                for fp, arcname, sz in files_to_zip:
                    if self._is_cancelled:
                        raise InterruptedError("Operazione annullata dall'utente.")

                    with open(fp, "rb") as src, zf.open(arcname, "w") as dst:
                        while True:
                            if self._is_cancelled:
                                raise InterruptedError("Operazione annullata dall'utente.")
                            chunk = src.read(131072) # Buffer di lettura da 128 KB
                            if not chunk:
                                break
                            dst.write(chunk)
                            bytes_done += len(chunk)

                            now = time.time()
                            elapsed = now - t_start
                            speed = bytes_done / elapsed if elapsed > 0 else 0
                            remaining_bytes = total_bytes - bytes_done
                            eta = remaining_bytes / speed if speed > 0 else 0
                            pct = int((bytes_done / total_bytes) * 100) if total_bytes > 0 else 100

                            self.progress.emit(pct, bytes_done, total_bytes, speed, eta)

            self.log.emit("Archiviazione e compressione completata al 100%!")
            self.finished.emit(True, f"Backup completato con successo: {os.path.basename(self.target_zip_path)}")

        except InterruptedError:
            # GESTIONE CANCELLAZIONE SICURA (ZERO RESIDUI)
            self.log.emit("INTERRUZIONE: Annullamento in corso ed eliminazione file temporaneo...")
            if os.path.exists(self.target_zip_path):
                try:
                    os.remove(self.target_zip_path)
                except Exception:
                    pass
            self.log.emit("Pulizia completata: nessun file incompleto lasciato sul disco.")
            self.finished.emit(False, "Operazione annullata dall'utente. Nessun file parziale creato.")

        except Exception as e:
            if os.path.exists(self.target_zip_path):
                try:
                    os.remove(self.target_zip_path)
                except Exception:
                    pass
            self.finished.emit(False, f"Errore durante la creazione del backup: {str(e)}")


class RestoreWorker(QThread):
    """
    Worker per il ripristino sicuro di un archivio di backup (.zip).
    
    Meccanismo di sicurezza:
      1. Arresta preventivamente Jellyfin per evitare scritture concorrenti sul database SQLite.
      2. Estrae tutti i dati in un'area di staging temporanea (.restore_staging) calcolando progresso ed ETA.
      3. Se l'utente annulla prima del termine: elimina l'area di staging senza toccare nulla dei file attivi.
      4. Solo a estrazione riuscita al 100%: sostituisce la vecchia configurazione con la nuova in modo atomico.
    """
    progress = pyqtSignal(int, int, int, float, float)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, source_zip_path):
        super().__init__()
        self.source_zip_path = source_zip_path
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        staging_dir = os.path.join(JELLYFIN_DIR, ".restore_staging")
        try:
            self.log.emit("Validazione dell'archivio zip selezionato...")
            if not zipfile.is_zipfile(self.source_zip_path):
                raise ValueError("Il file selezionato non è un archivio .zip integro o valido.")

            self.log.emit("Arresto temporaneo del server Jellyfin per proteggere i database...")
            subprocess.run([f"{LOCAL_BIN}/jellyfin-stop"], capture_output=True, text=True)

            if os.path.exists(staging_dir):
                shutil.rmtree(staging_dir, ignore_errors=True)
            os.makedirs(staging_dir, exist_ok=True)

            with zipfile.ZipFile(self.source_zip_path, "r") as zf:
                infolist = zf.infolist()
                total_bytes = sum(item.file_size for item in infolist)
                bytes_done = 0
                t_start = time.time()

                self.log.emit(f"Estrazione sicura di {len(infolist)} elementi ({total_bytes / (1024*1024):.2f} MB)...")

                for member in infolist:
                    if self._is_cancelled:
                        raise InterruptedError("Operazione annullata dall'utente.")

                    target_path = os.path.join(staging_dir, member.filename)
                    if member.is_dir():
                        os.makedirs(target_path, exist_ok=True)
                        continue

                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zf.open(member) as src, open(target_path, "wb") as dst:
                        while True:
                            if self._is_cancelled:
                                raise InterruptedError("Operazione annullata dall'utente.")
                            chunk = src.read(131072)
                            if not chunk:
                                break
                            dst.write(chunk)
                            bytes_done += len(chunk)

                            now = time.time()
                            elapsed = now - t_start
                            speed = bytes_done / elapsed if elapsed > 0 else 0
                            remaining = total_bytes - bytes_done
                            eta = remaining / speed if speed > 0 else 0
                            pct = int((bytes_done / total_bytes) * 100) if total_bytes > 0 else 100

                            self.progress.emit(pct, bytes_done, total_bytes, speed, eta)

            if self._is_cancelled:
                raise InterruptedError("Operazione annullata dall'utente.")

            # Applicazione atomica dei file estratti
            self.log.emit("Applicazione dei file ripristinati nella configurazione attiva...")
            staged_config = os.path.join(staging_dir, "config")
            target_config = os.path.join(JELLYFIN_DIR, "config")

            if os.path.exists(staged_config):
                backup_old = os.path.join(JELLYFIN_DIR, "config.old")
                if os.path.exists(backup_old):
                    shutil.rmtree(backup_old, ignore_errors=True)
                if os.path.exists(target_config):
                    os.rename(target_config, backup_old)
                shutil.move(staged_config, target_config)
                shutil.rmtree(backup_old, ignore_errors=True)

            staged_dc = os.path.join(staging_dir, "docker-compose.yml")
            if os.path.exists(staged_dc):
                shutil.copy2(staged_dc, os.path.join(JELLYFIN_DIR, "docker-compose.yml"))

            # Pulizia dell'area di staging
            shutil.rmtree(staging_dir, ignore_errors=True)

            self.log.emit("Ripristino completato con successo al 100%!")
            self.finished.emit(True, "Ripristino dei dati e del database completato con successo.")

        except InterruptedError:
            self.log.emit("INTERRUZIONE: Ripristino annullato. Ripristino dello stato originale in corso...")
            if os.path.exists(staging_dir):
                shutil.rmtree(staging_dir, ignore_errors=True)
            self.log.emit("Pulizia completata: nessun dato è stato corrotto.")
            self.finished.emit(False, "Ripristino annullato dall'utente. I file originali sono rimasti invariati.")

        except Exception as e:
            if os.path.exists(staging_dir):
                shutil.rmtree(staging_dir, ignore_errors=True)
            self.finished.emit(False, f"Errore critico durante il ripristino: {str(e)}")


class SystemInstallerWorker(QThread):
    """
    Worker per l'installazione da zero o la disinstallazione completa di Jellyfin.
    Gestisce l'elevazione sicura dei permessi tramite 'sudo -S' convogliando la password
    verificata attraverso stdin senza richiedere un terminale TTY interattivo.
    """
    progress = pyqtSignal(int, str)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, action_type, sudo_password, purge_data=False):
        super().__init__()
        self.action_type = action_type # "install" o "uninstall"
        self.sudo_password = sudo_password
        self.purge_data = purge_data
        self._is_cancelled = False
        self._proc = None

    def cancel(self):
        self._is_cancelled = True
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass

    def run_sudo_command(self, cmd_str):
        if self._is_cancelled:
            raise InterruptedError("Operazione annullata.")
        full_cmd = f"echo '{self.sudo_password}' | sudo -S {cmd_str}"
        self._proc = subprocess.Popen(
            full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in self._proc.stdout:
            if self._is_cancelled:
                self._proc.terminate()
                raise InterruptedError("Operazione annullata.")
            line_str = line.strip()
            if line_str and not "[sudo]" in line_str:
                self.log.emit(line_str)
        self._proc.wait()
        if self._proc.returncode != 0:
            raise RuntimeError(f"Comando fallito (codice {self._proc.returncode}): {cmd_str}")

    def run(self):
        try:
            if self.action_type == "install":
                distro = detect_distro()
                self.log.emit(f"Distribuzione Linux rilevata: {distro['name']} (Famiglia: {distro['id']})")
                self.log.emit(f"Gestore pacchetti identificato: {distro['pkg_mgr']}")
                self.progress.emit(10, "Verifica repository e pacchetti...")

                # 1. Installazione pacchetti di sistema
                install_cmd = distro.get("install_cmd")
                if install_cmd:
                    self.log.emit(f"Installazione pacchetti necessari via {distro['pkg_mgr']}...")
                    self.progress.emit(30, f"Installazione pacchetti ({distro['pkg_mgr']})...")
                    self.run_sudo_command(install_cmd)

                # 2. Avvio e abilitazione del demone Docker
                self.progress.emit(60, "Abilitazione servizio Docker...")
                self.log.emit("Abilitazione e avvio del demone Docker...")
                self.run_sudo_command("systemctl enable --now docker")

                # 3. Aggiunta dell'utente corrente al gruppo docker
                self.progress.emit(75, "Configurazione permessi utente...")
                username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
                self.log.emit(f"Aggiunta dell'utente '{username}' al gruppo 'docker'...")
                self.run_sudo_command(f"usermod -aG docker {username}")

                # 4. Download dell'immagine ufficiale Jellyfin
                self.progress.emit(90, "Scaricamento immagine ufficiale Jellyfin...")
                self.log.emit("Verifica e download immagine Docker 'jellyfin/jellyfin:latest'...")
                subprocess.run(["docker", "pull", "jellyfin/jellyfin:latest"], capture_output=True)

                self.progress.emit(100, "Installazione e configurazione completata!")
                self.log.emit("Tutti i requisiti di sistema sono stati installati e configurati con successo.")
                self.finished.emit(True, "Installazione e configurazione completata con successo!")

            elif self.action_type == "uninstall":
                self.progress.emit(10, "Arresto del server...")
                self.log.emit("Arresto in corso del container Jellyfin...")
                subprocess.run([f"{LOCAL_BIN}/jellyfin-stop"], capture_output=True)

                self.progress.emit(40, "Rimozione container e immagini Docker...")
                self.log.emit("Rimozione del container docker 'jellyfin'...")
                subprocess.run(["docker", "rm", "-f", "jellyfin"], capture_output=True)

                self.log.emit("Rimozione dell'immagine docker 'jellyfin/jellyfin:latest'...")
                subprocess.run(["docker", "rmi", "jellyfin/jellyfin:latest"], capture_output=True)

                self.progress.emit(70, "Pulizia collegamenti desktop e comandi locali...")
                home_dir = os.environ.get("HOME", os.path.expanduser("~"))
                for p in [
                    os.path.join(home_dir, "Scrivania/Jellyfin Control Center.desktop"),
                    os.path.join(home_dir, ".local/share/applications/jellyfin.desktop"),
                    os.path.join(home_dir, ".local/share/applications/jellyfin-stop.desktop"),
                    os.path.join(home_dir, ".local/share/applications/jellyfin-control.desktop"),
                    os.path.join(home_dir, ".local/bin/jellyfin-start"),
                    os.path.join(home_dir, ".local/bin/jellyfin-stop"),
                    os.path.join(home_dir, ".local/bin/jellyfin-status"),
                ]:
                    if os.path.exists(p):
                        os.remove(p)

                if self.purge_data:
                    self.progress.emit(90, "Rimozione cartella dati ~/jellyfin...")
                    self.log.emit("Eliminazione completa della cartella ~/jellyfin...")
                    shutil.rmtree(JELLYFIN_DIR, ignore_errors=True)

                self.progress.emit(100, "Disinstallazione completata.")
                self.log.emit("Disinstallazione e pulizia terminata con successo.")
                self.finished.emit(True, "Jellyfin e tutti i suoi riferimenti sono stati rimossi dal sistema.")

        except InterruptedError:
            self.log.emit("Operazione interrotta dall'utente. Pulizia eseguita.")
            self.finished.emit(False, "Operazione annullata dall'utente.")
        except Exception as e:
            self.finished.emit(False, f"Errore durante l'operazione: {str(e)}")





# ==================================================================================================
# FINESTRE DI DIALOGO: INFORMAZIONI SUL PROGRAMMA E GUIDA HTML
# ==================================================================================================

class AboutDialog(QDialog):
    """Finestra di dialogo elegante con i crediti e le note di distribuzione del programma."""
    def __init__(self, parent=None, lang="it"):
        super().__init__(parent)
        self.setWindowTitle(t("btn_info", lang).replace("ℹ️ ", "") + " - Jellyfin Control Center")
        self.resize(540, 360)
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 14)
        layout.setSpacing(12)

        tb = QTextBrowser()
        tb.setOpenExternalLinks(True)
        tb.setStyleSheet("background-color: #12141c; border: 1px solid #282d3f; border-radius: 8px;")
        tb.setHtml(get_about_info_html(lang))
        layout.addWidget(tb)

        btn_close = QPushButton("Chiudi / Close")
        btn_close.setObjectName("btnMini")
        btn_close.setFixedHeight(30)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)


class GuideDialog(QDialog):
    """Finestra separata che visualizza la guida operativa completa in formato HTML."""
    def __init__(self, parent=None, lang="it"):
        super().__init__(parent)
        self.setWindowTitle(t("btn_guide", lang).replace("📖 ", "") + " - Jellyfin Control Center")
        self.resize(860, 680)
        self.setModal(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 12)
        layout.setSpacing(10)

        tb = QTextBrowser()
        tb.setOpenExternalLinks(True)
        tb.setStyleSheet("background-color: #12141c; border: 1px solid #282d3f; border-radius: 8px;")
        tb.setHtml(get_user_guide_html(lang))
        layout.addWidget(tb)

        btn_close = QPushButton("Chiudi / Close")
        btn_close.setObjectName("btnMini")
        btn_close.setFixedHeight(30)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

# ==================================================================================================
# THREAD WORKER PER GESTIONE PLUGIN INTRO SKIPPER (INSTALLAZIONE / RIMOZIONE)
# ==================================================================================================

class PluginInstallWorker(QThread):
    """
    Worker in background per scaricare o estrarre l'archivio del plugin Intro Skipper
    e configurarlo nella cartella plugins di Jellyfin senza bloccare la GUI.
    """
    progress = pyqtSignal(int, str)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, mode="online", local_zip=""):
        super().__init__()
        self.mode = mode
        self.local_zip = local_zip
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        try:
            plugins_dir = os.path.join(JELLYFIN_DIR, "config/plugins")
            os.makedirs(plugins_dir, exist_ok=True)
            target_plugin_dir = os.path.join(plugins_dir, "Intro Skipper_12.0.4.0")

            if self.mode == "online":
                self.progress.emit(10, "Connessione al repository GitHub...")
                self.log.emit("Inizio download release ufficiale Intro Skipper (v12.0.4.0)...")
                temp_zip = "/tmp/intro-skipper-download.zip"

                url = INTRO_SKIPPER_URL
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp, open(temp_zip, "wb") as out_f:
                    total_len = resp.headers.get("Content-Length")
                    total_bytes = int(total_len) if total_len else 300000
                    downloaded = 0
                    while True:
                        if self.is_cancelled:
                            if os.path.exists(temp_zip):
                                os.remove(temp_zip)
                            raise InterruptedError("Download annullato dall'utente.")
                        chunk = resp.read(64 * 1024)
                        if not chunk:
                            break
                        out_f.write(chunk)
                        downloaded += len(chunk)
                        pct = int(10 + (downloaded / total_bytes) * 40)
                        self.progress.emit(min(50, pct), f"Download in corso: {downloaded // 1024} KB...")

                zip_to_extract = temp_zip
            else:
                zip_to_extract = self.local_zip
                self.log.emit(f"Utilizzo archivio locale fornito dall'utente: {zip_to_extract}")

            self.progress.emit(60, "Estrazione file del plugin...")
            self.log.emit(f"Estrazione file in: {target_plugin_dir}...")
            os.makedirs(target_plugin_dir, exist_ok=True)

            with zipfile.ZipFile(zip_to_extract, "r") as zf:
                zf.extractall(target_plugin_dir)

            if self.mode == "online" and os.path.exists("/tmp/intro-skipper-download.zip"):
                try:
                    os.remove("/tmp/intro-skipper-download.zip")
                except Exception:
                    pass

            self.progress.emit(80, "Riavvio del container Jellyfin per attivare il plugin...")
            self.log.emit("Esecuzione 'docker restart jellyfin'...")
            subprocess.run(["docker", "restart", "jellyfin"], capture_output=True)

            self.progress.emit(100, "Plugin installato con successo!")
            self.log.emit("Il plugin Intro Skipper e ora attivo su Jellyfin.")
            self.finished.emit(True, "Plugin Intro Skipper installato e attivato con successo!")

        except InterruptedError:
            self.finished.emit(False, "Operazione annullata dall'utente.")
        except Exception as e:
            self.finished.emit(False, f"Errore durante l'installazione del plugin: {e}")


class PluginUninstallWorker(QThread):
    """
    Worker in background per disinstallare il plugin Intro Skipper e, opzionalmente,
    ripulire il database delle impronte digitali calcolate.
    """
    progress = pyqtSignal(int, str)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, remove_database=False):
        super().__init__()
        self.remove_database = remove_database

    def run(self):
        try:
            self.progress.emit(20, "Rimozione cartella plugin...")
            self.log.emit("Ricerca ed eliminazione directory di Intro Skipper...")
            plugins_dir = os.path.join(JELLYFIN_DIR, "config/plugins")
            if os.path.exists(plugins_dir):
                for entry in os.listdir(plugins_dir):
                    if entry.startswith("Intro Skipper"):
                        p_path = os.path.join(plugins_dir, entry)
                        self.log.emit(f"Eliminazione {p_path}...")
                        shutil.rmtree(p_path, ignore_errors=True)

            config_xml = os.path.join(plugins_dir, "configurations/IntroSkipper.xml")
            if os.path.exists(config_xml):
                try:
                    os.remove(config_xml)
                except Exception:
                    pass

            if self.remove_database:
                self.progress.emit(50, "Cancellazione database impronte audio...")
                self.log.emit("Rimozione cartella database config/data/introskipper...")
                data_dir = os.path.join(JELLYFIN_DIR, "config/data/introskipper")
                if os.path.exists(data_dir):
                    shutil.rmtree(data_dir, ignore_errors=True)

            self.progress.emit(80, "Riavvio del container Jellyfin...")
            self.log.emit("Riavvio del container Jellyfin per completare la disinstallazione...")
            subprocess.run(["docker", "restart", "jellyfin"], capture_output=True)

            self.progress.emit(100, "Disinstallazione completata.")
            self.finished.emit(True, "Plugin Intro Skipper disinstallato con successo!")
        except Exception as e:
            self.finished.emit(False, f"Errore durante la disinstallazione: {e}")


class TrickplayInstallWorker(QThread):
    """Worker in background per installare o configurare il plugin Trickplay."""
    progress = pyqtSignal(int, str)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, mode="online", local_zip=""):
        super().__init__()
        self.mode = mode
        self.local_zip = local_zip

    def run(self):
        try:
            os.makedirs(TRICKPLAY_PLUGIN_DIR, exist_ok=True)
            self.progress.emit(20, "Preparazione modulo Trickplay...")
            if self.mode == "local" and self.local_zip:
                self.log.emit(f"Estrazione archivio locale Trickplay: {self.local_zip}...")
                with zipfile.ZipFile(self.local_zip, "r") as zf:
                    zf.extractall(TRICKPLAY_PLUGIN_DIR)
            else:
                self.log.emit("Configurazione ed abilitazione modulo Trickplay...")

            self.progress.emit(70, "Riavvio container Jellyfin...")
            subprocess.run(["docker", "restart", "jellyfin"], capture_output=True)
            self.progress.emit(100, "Trickplay configurato con successo!")
            self.finished.emit(True, "Modulo Trickplay configurato e pronto all'uso!")
        except Exception as e:
            self.finished.emit(False, f"Errore durante l'installazione di Trickplay: {e}")


class TrickplayUninstallWorker(QThread):
    """Worker in background per rimuovere il plugin Trickplay e opzionalmente le miniature."""
    progress = pyqtSignal(int, str)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, purge_data=False):
        super().__init__()
        self.purge_data = purge_data

    def run(self):
        try:
            self.progress.emit(20, "Rimozione cartella plugin Trickplay...")
            if os.path.exists(TRICKPLAY_PLUGIN_DIR):
                shutil.rmtree(TRICKPLAY_PLUGIN_DIR, ignore_errors=True)

            if self.purge_data and os.path.exists(TRICKPLAY_DATA_DIR):
                self.progress.emit(50, "Cancellazione file miniature Trickplay...")
                shutil.rmtree(TRICKPLAY_DATA_DIR, ignore_errors=True)

            self.progress.emit(80, "Riavvio container Jellyfin...")
            subprocess.run(["docker", "restart", "jellyfin"], capture_output=True)
            self.progress.emit(100, "Rimozione completata.")
            self.finished.emit(True, "Trickplay disinstallato con successo!")
        except Exception as e:
            self.finished.emit(False, f"Errore durante la disinstallazione: {e}")

# ==================================================================================================
# CLASSE PRINCIPALE DELL'INTERFACCIA GRAFICA (QMAINWINDOW)
# ==================================================================================================

class JellyfinManager(QMainWindow):
    """
    Finestra principale dell'applicazione 'Jellyfin Control Center'.
    Organizzata in 5 schede con design dark moderno ad alto contrasto.
    """
    def __init__(self, single_instance_server=None):
        super().__init__()
        self.single_instance_server = single_instance_server
        if self.single_instance_server:
            self.single_instance_server.newConnection.connect(self.handle_single_instance_connection)

        self.current_lang = get_system_language()
        self.setWindowTitle("Jellyfin Control Center")
        self.resize(920, 820)
        self.setMinimumSize(820, 720)

        # Icona della finestra
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        elif os.path.exists(FALLBACK_ICON):
            self.setWindowIcon(QIcon(FALLBACK_ICON))

        self.lan_ip = get_lan_ip()
        self.api_key = get_or_create_api_key()
        self.current_status = "unknown"
        self.is_operating = False
        self.worker = None
        self.backup_worker = None
        self.restore_worker = None
        self.install_worker = None

        # REGOLA DI PROGETTAZIONE FONDAMENTALE:
        # I timer di polling devono essere dichiarati PRIMA di invocare setup_ui(),
        # altrimenti l'aggiunta delle schede provocherebbe l'evento 'currentChanged'
        # causando un AttributeError su attributi non ancora inizializzati.
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_server_status)

        self.hw_timer = QTimer(self)
        self.hw_timer.timeout.connect(self.poll_hardware_metrics)

        self.sessions_timer = QTimer(self)
        self.sessions_timer.timeout.connect(self.poll_active_sessions)

        self.plugin_timer = QTimer(self)
        self.plugin_timer.timeout.connect(self.poll_plugin_status)
        self.plugin_install_worker = None
        self.plugin_uninstall_worker = None
        self.last_plugin_log_text = ""
        self.last_tp_log_text = ""
        self.tp_install_worker = None
        self.tp_uninstall_worker = None

        self.setup_ui()
        self.apply_styles()

        # Avvio del solo timer di monitoraggio stato server (leggero)
        self.status_timer.start(3000)
        self.update_server_status()

    
    def handle_single_instance_connection(self):
        """Gestisce l'arrivo di un tentativo di lancio da parte di una seconda istanza."""
        if not self.single_instance_server:
            return
        client = self.single_instance_server.nextPendingConnection()
        if client:
            client.readyRead.connect(lambda: self.on_single_instance_message(client))

    def on_single_instance_message(self, client):
        """Legge il messaggio inviato dalla seconda istanza e risveglia la finestra."""
        try:
            msg = client.readAll().data().decode("utf-8", errors="ignore")
            if "ACTIVATE" in msg:
                self.showNormal()
                self.raise_()
                self.activateWindow()
        except Exception:
            pass
        finally:
            client.disconnectFromServer()

    def setup_ui(self):
        """Costruisce la gerarchia dei widget dell'interfaccia utente."""
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(10)

        # -------------------------------------------------------------
        # INTESTAZIONE COMUNE (HEADER)
        # -------------------------------------------------------------
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(14, 8, 14, 8)
        header_layout.setSpacing(14)

        logo_label = QLabel()
        if os.path.exists(ICON_PATH):
            pix = QPixmap(ICON_PATH).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pix)
        elif os.path.exists(FALLBACK_ICON):
            pix = QPixmap(FALLBACK_ICON).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pix)
        header_layout.addWidget(logo_label)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.lbl_app_title = QLabel("Jellyfin Control Center")
        self.lbl_app_title.setObjectName("appTitle")
        self.lbl_app_subtitle = QLabel(t("app_subtitle", self.current_lang))
        self.lbl_app_subtitle.setObjectName("appSubtitle")
        title_box.addWidget(self.lbl_app_title)
        title_box.addWidget(self.lbl_app_subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Selettore Lingua (5 Lingue)
        self.combo_lang = QComboBox()
        self.combo_lang.setObjectName("btnMini")
        self.combo_lang.setFixedHeight(30)
        for code_l, name_l in SUPPORTED_LANGUAGES.items():
            self.combo_lang.addItem(name_l, code_l)
        idx_l = self.combo_lang.findData(self.current_lang)
        if idx_l >= 0:
            self.combo_lang.setCurrentIndex(idx_l)
        self.combo_lang.currentIndexChanged.connect(self.on_language_changed)
        header_layout.addWidget(self.combo_lang)

        # Pulsanti Info e Guida HTML
        self.btn_app_info = QPushButton(t("btn_info", self.current_lang))
        self.btn_app_info.setObjectName("btnMini")
        self.btn_app_info.setFixedHeight(30)
        self.btn_app_info.clicked.connect(self.show_about_dialog)
        header_layout.addWidget(self.btn_app_info)

        self.btn_app_guide = QPushButton(t("btn_guide", self.current_lang))
        self.btn_app_guide.setObjectName("btnMini")
        self.btn_app_guide.setFixedHeight(30)
        self.btn_app_guide.clicked.connect(self.show_guide_dialog)
        header_layout.addWidget(self.btn_app_guide)

        status_box = QHBoxLayout()
        status_box.setSpacing(8)
        lbl_st = QLabel("Stato Server:")
        lbl_st.setStyleSheet("color: #9ba1b0; font-weight: bold; font-size: 13px;")
        self.header_status_badge = QLabel("IN VERIFICA...")
        self.header_status_badge.setObjectName("statusBadgeUnknown")
        self.header_status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge = self.header_status_badge
        status_box.addWidget(lbl_st)
        status_box.addWidget(self.header_status_badge)
        header_layout.addLayout(status_box)

        main_layout.addWidget(header_frame)

        # Barra di avanzamento globale (mostrata durante start/stop del container)
        self.global_progress = QProgressBar()
        self.global_progress.setRange(0, 0)
        self.global_progress.setFixedHeight(4)
        self.global_progress.setTextVisible(False)
        self.global_progress.hide()
        main_layout.addWidget(self.global_progress)

        # -------------------------------------------------------------
        # SCHEDE PRINCIPALI (QTABWIDGET)
        # -------------------------------------------------------------
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabs")

        # Tab 1: Controllo Principale
        self.tab_control = QWidget()
        self.setup_tab_control()
        self.tab_widget.addTab(self.tab_control, "⚡ Controllo")

        # Tab 2: Dispositivi & Sessioni Attive
        self.tab_sessions = QWidget()
        self.setup_tab_sessions()
        self.tab_widget.addTab(self.tab_sessions, "👥 Dispositivi & Sessioni")

        # Tab 3: Monitoraggio Risorse Hardware
        self.tab_hardware = QWidget()
        self.setup_tab_hardware()
        self.tab_widget.addTab(self.tab_hardware, "📊 Monitor Hardware")

        # Tab 4: Gestione Installazione & Sistema
        self.tab_install = QWidget()
        self.setup_tab_install()
        self.tab_widget.addTab(self.tab_install, "📦 Gestione Installazione")

        # Tab 5: Backup & Ripristino (.zip)
        self.tab_backup = QWidget()
        self.setup_tab_backup()
        self.tab_widget.addTab(self.tab_backup, "💾 Backup & Ripristino")

        # Tab 6: Gestione Plugin (Intro Skipper)
        self.tab_plugin = QWidget()
        self.setup_tab_plugin()
        self.tab_widget.addTab(self.tab_plugin, "🔌 Plugin")

        # Connessione dell'evento di cambio scheda DOPO aver aggiunto tutti i tab
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tab_widget)

    # -------------------------------------------------------------
    # TAB 1: CONTROLLO E DASHBOARD
    # -------------------------------------------------------------
    
    def show_about_dialog(self):
        """Apre la finestra di informazioni sul programma con i crediti PsyTech76."""
        dlg = AboutDialog(self, lang=self.current_lang)
        dlg.exec()

    def show_guide_dialog(self):
        """Apre la finestra separata della guida in formato HTML styled."""
        dlg = GuideDialog(self, lang=self.current_lang)
        dlg.show()

    def on_language_changed(self, index):
        """Aggiorna la lingua attiva dell'applicazione quando l'utente seleziona un'altra lingua."""
        new_lang = self.combo_lang.itemData(index)
        if new_lang and new_lang in SUPPORTED_LANGUAGES:
            self.current_lang = new_lang
            self.retranslate_ui()

    def retranslate_ui(self):
        """Aggiorna dinamicamente i testi principali dell'interfaccia nella lingua selezionata."""
        self.lbl_app_title.setText(t("app_title", self.current_lang))
        self.lbl_app_subtitle.setText(t("app_subtitle", self.current_lang))
        self.btn_app_info.setText(t("btn_info", self.current_lang))
        self.btn_app_guide.setText(t("btn_guide", self.current_lang))

        # Schede principali
        self.tab_widget.setTabText(0, t("tab_control", self.current_lang))
        self.tab_widget.setTabText(1, t("tab_sessions", self.current_lang))
        self.tab_widget.setTabText(2, t("tab_hardware", self.current_lang))
        self.tab_widget.setTabText(3, t("tab_install", self.current_lang))
        self.tab_widget.setTabText(4, t("tab_backup", self.current_lang))
        self.tab_widget.setTabText(5, t("tab_plugin", self.current_lang))

        # Sotto-schede plugin
        if hasattr(self, "plugin_subtabs"):
            self.plugin_subtabs.setTabText(0, t("subtab_intro_skipper", self.current_lang))
            self.plugin_subtabs.setTabText(1, t("subtab_trickplay", self.current_lang))

        # Aggiorna testo del pulsante di integrazione desktop
        self.update_system_integration_button()

    def setup_tab_control(self):
        layout = QVBoxLayout(self.tab_control)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Riquadro indirizzi IP e Uptime
        info_card = QFrame()
        info_card.setObjectName("cardFrame")
        ic_layout = QGridLayout(info_card)
        ic_layout.setContentsMargins(16, 12, 16, 12)
        ic_layout.setHorizontalSpacing(14)
        ic_layout.setVerticalSpacing(8)

        lbl_loc = QLabel("Indirizzo Locale (PC):")
        lbl_loc.setStyleSheet("color: #9ba1b0; font-size: 13px;")
        self.lbl_val_loc = QLabel("http://localhost:8096")
        self.lbl_val_loc.setStyleSheet("color: #00d2ff; font-weight: bold; font-size: 13px;")
        btn_copy_loc = QPushButton("Copia")
        btn_copy_loc.setObjectName("btnMini")
        btn_copy_loc.clicked.connect(lambda: self.copy_to_clipboard("http://localhost:8096", "Indirizzo Locale"))

        lbl_lan = QLabel("Indirizzo Rete (Wi-Fi/LAN):")
        lbl_lan.setStyleSheet("color: #9ba1b0; font-size: 13px;")
        self.lbl_val_lan = QLabel(f"http://{self.lan_ip}:8096")
        self.lbl_val_lan.setStyleSheet("color: #00d2ff; font-weight: bold; font-size: 13px;")
        btn_copy_lan = QPushButton("Copia")
        btn_copy_lan.setObjectName("btnMini")
        btn_copy_lan.clicked.connect(lambda: self.copy_to_clipboard(f"http://{self.lan_ip}:8096", "Indirizzo Rete"))

        lbl_up = QLabel("Stato Attività (Uptime):")
        lbl_up.setStyleSheet("color: #9ba1b0; font-size: 13px;")
        self.lbl_val_uptime = QLabel("In verifica...")
        self.lbl_val_uptime.setStyleSheet("color: #cfd3dc; font-size: 13px;")

        ic_layout.addWidget(lbl_loc, 0, 0)
        ic_layout.addWidget(self.lbl_val_loc, 0, 1)
        ic_layout.addWidget(btn_copy_loc, 0, 2)
        ic_layout.addWidget(lbl_lan, 1, 0)
        ic_layout.addWidget(self.lbl_val_lan, 1, 1)
        ic_layout.addWidget(btn_copy_lan, 1, 2)
        ic_layout.addWidget(lbl_up, 2, 0)
        ic_layout.addWidget(self.lbl_val_uptime, 2, 1, 1, 2)
        layout.addWidget(info_card)

        # Pulsanti di controllo primari
        controls_card = QFrame()
        controls_card.setObjectName("cardFrame")
        cc_layout = QVBoxLayout(controls_card)
        cc_layout.setContentsMargins(16, 12, 16, 12)
        cc_layout.setSpacing(10)

        row_main = QHBoxLayout()
        row_main.setSpacing(12)
        self.btn_start = QPushButton("▶  Avvia Jellyfin")
        self.btn_start.setObjectName("btnStart")
        self.btn_start.setFixedHeight(42)
        self.btn_start.clicked.connect(self.start_jellyfin)

        self.btn_stop = QPushButton("⏹  Arresta Jellyfin")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setFixedHeight(42)
        self.btn_stop.clicked.connect(self.stop_jellyfin)

        self.btn_restart = QPushButton("🔄  Riavvia")
        self.btn_restart.setObjectName("btnRestart")
        self.btn_restart.setFixedHeight(42)
        self.btn_restart.clicked.connect(self.restart_jellyfin)

        row_main.addWidget(self.btn_start)
        row_main.addWidget(self.btn_stop)
        row_main.addWidget(self.btn_restart)
        cc_layout.addLayout(row_main)

        # Scorciatoie ausiliarie (Browser e Cartelle)
        row_sec = QHBoxLayout()
        row_sec.setSpacing(10)
        self.btn_browser = QPushButton("🌐  Apri nel Browser")
        self.btn_browser.setObjectName("btnBrowser")
        self.btn_browser.setFixedHeight(36)
        self.btn_browser.clicked.connect(self.open_browser)

        self.btn_video_folder = QPushButton("📁  Cartella Video")
        self.btn_video_folder.setObjectName("btnFolder")
        self.btn_video_folder.setFixedHeight(36)
        self.btn_video_folder.clicked.connect(lambda: self.open_folder(os.path.expanduser("~/Video")))

        self.btn_music_folder = QPushButton("🎵  Cartella Musica")
        self.btn_music_folder.setObjectName("btnFolder")
        self.btn_music_folder.setFixedHeight(36)
        self.btn_music_folder.clicked.connect(lambda: self.open_folder(os.path.expanduser("~/Musica")))

        self.btn_system_integration = QPushButton()
        self.btn_system_integration.setObjectName("btnIntegration")
        self.btn_system_integration.setFixedHeight(36)
        self.btn_system_integration.clicked.connect(self.toggle_system_integration)

        row_sec.addWidget(self.btn_browser)
        row_sec.addWidget(self.btn_video_folder)
        row_sec.addWidget(self.btn_music_folder)
        row_sec.addWidget(self.btn_system_integration)
        cc_layout.addLayout(row_sec)
        layout.addWidget(controls_card)

        # Ispezione log recenti
        logs_card = QFrame()
        logs_card.setObjectName("cardFrame")
        lc_layout = QVBoxLayout(logs_card)
        lc_layout.setContentsMargins(14, 10, 14, 10)
        lc_layout.setSpacing(6)

        lc_header = QHBoxLayout()
        lbl_lh = QLabel("Log Recenti del Server")
        lbl_lh.setStyleSheet("font-weight: bold; color: #9ba1b0; font-size: 12px;")
        btn_refresh_log = QPushButton("Ricarica Log")
        btn_refresh_log.setObjectName("btnMini")
        btn_refresh_log.clicked.connect(self.fetch_logs)
        lc_header.addWidget(lbl_lh)
        lc_header.addStretch()
        lc_header.addWidget(btn_refresh_log)
        lc_layout.addLayout(lc_header)

        self.txt_logs = QPlainTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setObjectName("logViewer")
        self.txt_logs.setPlaceholderText("Log non disponibili o server arrestato...")
        lc_layout.addWidget(self.txt_logs)
        layout.addWidget(logs_card)

    # -------------------------------------------------------------
    # TAB 2: DISPOSITIVI E SESSIONI ATTIVE
    # -------------------------------------------------------------
    def setup_tab_sessions(self):
        layout = QVBoxLayout(self.tab_sessions)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        bar = QFrame()
        bar.setObjectName("cardFrame")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(14)

        self.lbl_sessions_count = QLabel("Dispositivi Connessi: 0")
        self.lbl_sessions_count.setStyleSheet("font-size: 14px; font-weight: bold; color: #00d2ff;")

        self.chk_sessions_view_mode = QCheckBox("Visualizza Vista Terminale / Raw JSON")
        self.chk_sessions_view_mode.setObjectName("customCheck")
        self.chk_sessions_view_mode.toggled.connect(self.toggle_sessions_view_mode)

        btn_refresh_sess = QPushButton("⟳  Aggiorna Ora")
        btn_refresh_sess.setObjectName("btnMini")
        btn_refresh_sess.clicked.connect(self.poll_active_sessions)

        bar_layout.addWidget(self.lbl_sessions_count)
        bar_layout.addStretch()
        bar_layout.addWidget(self.chk_sessions_view_mode)
        bar_layout.addWidget(btn_refresh_sess)
        layout.addWidget(bar)

        self.sessions_stack = QStackedWidget()

        # VISTA 1: Tabella grafica interattiva
        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(4)
        self.sessions_table.setHorizontalHeaderLabels([
            "Utente", "Dispositivo / Client", "Cosa Sta Riproducendo", "Ultima Attività / Stato"
        ])
        self.sessions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.sessions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.sessions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.sessions_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.sessions_table.verticalHeader().setVisible(False)
        self.sessions_table.setAlternatingRowColors(True)
        self.sessions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sessions_table.setObjectName("sessionsTable")
        self.sessions_stack.addWidget(self.sessions_table)

        # VISTA 2: Dati grezzi JSON / vista stile terminale
        self.sessions_terminal_view = QPlainTextEdit()
        self.sessions_terminal_view.setReadOnly(True)
        self.sessions_terminal_view.setObjectName("terminalViewer")
        self.sessions_terminal_view.setPlaceholderText("In attesa dei dati delle sessioni...")
        self.sessions_stack.addWidget(self.sessions_terminal_view)

        layout.addWidget(self.sessions_stack)

    # -------------------------------------------------------------
    # TAB 3: MONITORAGGIO RISORSE HARDWARE (A IMPATTO ZERO)
    # -------------------------------------------------------------
    def setup_tab_hardware(self):
        layout = QVBoxLayout(self.tab_hardware)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Casella di abilitazione fondamentale
        top_ctrl = QFrame()
        top_ctrl.setObjectName("cardFrame")
        tc_layout = QHBoxLayout(top_ctrl)
        tc_layout.setContentsMargins(16, 10, 16, 10)
        tc_layout.setSpacing(14)

        self.chk_monitor_hw = QCheckBox("⚡  Attiva Monitoraggio Risorse Hardware in Tempo Reale")
        self.chk_monitor_hw.setObjectName("customCheckLarge")
        self.chk_monitor_hw.setToolTip("Consuma cicli macchina SOLO mentre è attivo e visualizzato. Disattivato = 0% impatto.")
        self.chk_monitor_hw.setChecked(False)
        self.chk_monitor_hw.toggled.connect(self.toggle_hardware_monitoring)

        self.lbl_hw_status = QLabel("Stato: DISATTIVO (0% consumo)")
        self.lbl_hw_status.setStyleSheet("color: #9ba1b0; font-weight: bold; font-size: 12px;")

        self.chk_hw_view_mode = QCheckBox("Vista Terminale (nvidia-smi & top)")
        self.chk_hw_view_mode.setObjectName("customCheck")
        self.chk_hw_view_mode.toggled.connect(self.toggle_hw_view_mode)

        tc_layout.addWidget(self.chk_monitor_hw)
        tc_layout.addWidget(self.lbl_hw_status)
        tc_layout.addStretch()
        tc_layout.addWidget(self.chk_hw_view_mode)
        layout.addWidget(top_ctrl)

        self.hw_stack = QStackedWidget()
        self.hw_graphical_view = QWidget()
        gv_layout = QVBoxLayout(self.hw_graphical_view)
        gv_layout.setContentsMargins(0, 0, 0, 0)
        gv_layout.setSpacing(10)

        # Misuratore CPU
        cpu_card = QFrame()
        cpu_card.setObjectName("cardFrame")
        cpu_layout = QVBoxLayout(cpu_card)
        cpu_layout.setContentsMargins(16, 10, 16, 10)
        cpu_layout.setSpacing(6)
        cpu_row = QHBoxLayout()
        lbl_cpu_t = QLabel("PROCESSORE (CPU)")
        lbl_cpu_t.setStyleSheet("font-weight: bold; font-size: 13px; color: #cfd3dc;")
        self.lbl_cpu_model = QLabel("Intel Core i7-8700K (6C / 12T)")
        self.lbl_cpu_model.setStyleSheet("color: #9ba1b0; font-size: 12px;")
        self.lbl_cpu_val = QLabel("0%")
        self.lbl_cpu_val.setStyleSheet("color: #00d2ff; font-weight: bold; font-size: 15px;")
        cpu_row.addWidget(lbl_cpu_t)
        cpu_row.addWidget(self.lbl_cpu_model)
        cpu_row.addStretch()
        cpu_row.addWidget(self.lbl_cpu_val)
        cpu_layout.addLayout(cpu_row)
        self.bar_cpu = QProgressBar()
        self.bar_cpu.setRange(0, 100)
        self.bar_cpu.setValue(0)
        self.bar_cpu.setFixedHeight(10)
        self.bar_cpu.setTextVisible(False)
        cpu_layout.addWidget(self.bar_cpu)
        gv_layout.addWidget(cpu_card)

        # Misuratore GPU NVIDIA
        gpu_card = QFrame()
        gpu_card.setObjectName("cardFrame")
        gpu_layout = QVBoxLayout(gpu_card)
        gpu_layout.setContentsMargins(16, 10, 16, 10)
        gpu_layout.setSpacing(6)
        gpu_row = QHBoxLayout()
        lbl_gpu_t = QLabel("SCHEDA VIDEO (NVIDIA GPU)")
        lbl_gpu_t.setStyleSheet("font-weight: bold; font-size: 13px; color: #cfd3dc;")
        self.lbl_gpu_model = QLabel("NVIDIA GeForce RTX 3070 Ti (NVENC / NVDEC)")
        self.lbl_gpu_model.setStyleSheet("color: #9ba1b0; font-size: 12px;")
        self.lbl_gpu_val = QLabel("0%")
        self.lbl_gpu_val.setStyleSheet("color: #b855d4; font-weight: bold; font-size: 15px;")
        gpu_row.addWidget(lbl_gpu_t)
        gpu_row.addWidget(self.lbl_gpu_model)
        gpu_row.addStretch()
        gpu_row.addWidget(self.lbl_gpu_val)
        gpu_layout.addLayout(gpu_row)
        self.bar_gpu = QProgressBar()
        self.bar_gpu.setRange(0, 100)
        self.bar_gpu.setValue(0)
        self.bar_gpu.setFixedHeight(10)
        self.bar_gpu.setTextVisible(False)
        gpu_layout.addWidget(self.bar_gpu)
        gpu_sub = QHBoxLayout()
        gpu_sub.setSpacing(16)
        self.lbl_gpu_vram = QLabel("VRAM: - / - MB")
        self.lbl_gpu_vram.setStyleSheet("color: #cfd3dc; font-size: 12px;")
        self.lbl_gpu_temp = QLabel("Temperatura: - °C")
        self.lbl_gpu_temp.setStyleSheet("color: #cfd3dc; font-size: 12px;")
        self.lbl_gpu_power = QLabel("Consumo: - W")
        self.lbl_gpu_power.setStyleSheet("color: #cfd3dc; font-size: 12px;")
        gpu_sub.addWidget(self.lbl_gpu_vram)
        gpu_sub.addWidget(self.lbl_gpu_temp)
        gpu_sub.addWidget(self.lbl_gpu_power)
        gpu_sub.addStretch()
        gpu_layout.addLayout(gpu_sub)
        gv_layout.addWidget(gpu_card)

        # Misuratore RAM e Container
        ram_card = QFrame()
        ram_card.setObjectName("cardFrame")
        ram_layout = QVBoxLayout(ram_card)
        ram_layout.setContentsMargins(16, 10, 16, 10)
        ram_layout.setSpacing(6)
        ram_row = QHBoxLayout()
        lbl_ram_t = QLabel("MEMORIA RAM DI SISTEMA")
        lbl_ram_t.setStyleSheet("font-weight: bold; font-size: 13px; color: #cfd3dc;")
        self.lbl_ram_details = QLabel("- / - GB")
        self.lbl_ram_details.setStyleSheet("color: #9ba1b0; font-size: 12px;")
        self.lbl_ram_val = QLabel("0%")
        self.lbl_ram_val.setStyleSheet("color: #10b981; font-weight: bold; font-size: 15px;")
        ram_row.addWidget(lbl_ram_t)
        ram_row.addWidget(self.lbl_ram_details)
        ram_row.addStretch()
        ram_row.addWidget(self.lbl_ram_val)
        ram_layout.addLayout(ram_row)
        self.bar_ram = QProgressBar()
        self.bar_ram.setRange(0, 100)
        self.bar_ram.setValue(0)
        self.bar_ram.setFixedHeight(10)
        self.bar_ram.setTextVisible(False)
        ram_layout.addWidget(self.bar_ram)
        self.lbl_docker_stats = QLabel("Container Docker Jellyfin: Uptime e utilizzo in elaborazione...")
        self.lbl_docker_stats.setStyleSheet("color: #9ba1b0; font-size: 12px; margin-top: 2px;")
        ram_layout.addWidget(self.lbl_docker_stats)
        gv_layout.addWidget(ram_card)

        self.hw_stack.addWidget(self.hw_graphical_view)

        self.hw_terminal_view = QPlainTextEdit()
        self.hw_terminal_view.setReadOnly(True)
        self.hw_terminal_view.setObjectName("terminalViewer")
        self.hw_terminal_view.setPlaceholderText("Attiva il monitoraggio per visualizzare i dettagli grezzi...")
        self.hw_stack.addWidget(self.hw_terminal_view)

        layout.addWidget(self.hw_stack)

    # -------------------------------------------------------------
    # TAB 4: GESTIONE INSTALLAZIONE & SISTEMA
    # -------------------------------------------------------------
    def setup_tab_install(self):
        layout = QVBoxLayout(self.tab_install)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        distro_card = QFrame()
        distro_card.setObjectName("cardFrame")
        dc_layout = QVBoxLayout(distro_card)
        dc_layout.setContentsMargins(16, 12, 16, 12)
        dc_layout.setSpacing(6)

        distro_info = detect_distro()
        lbl_dt = QLabel(f"🐧  Distribuzione Rilevata: {distro_info['name']}")
        lbl_dt.setStyleSheet("font-size: 15px; font-weight: bold; color: #00d2ff;")
        lbl_pkg = QLabel(f"Gestore pacchetti identificato: <b>{distro_info['pkg_mgr']}</b> (comando pacchetti: <code>{distro_info['install_cmd']}</code>)")
        lbl_pkg.setStyleSheet("color: #9ba1b0; font-size: 12px;")

        dc_layout.addWidget(lbl_dt)
        dc_layout.addWidget(lbl_pkg)
        layout.addWidget(distro_card)

        actions_card = QFrame()
        actions_card.setObjectName("cardFrame")
        ac_layout = QVBoxLayout(actions_card)
        ac_layout.setContentsMargins(16, 14, 16, 14)
        ac_layout.setSpacing(14)

        row_inst = QHBoxLayout()
        row_inst.setSpacing(14)
        desc_inst = QVBoxLayout()
        lbl_it = QLabel("Installazione e Configurazione Guidata")
        lbl_it.setStyleSheet("font-weight: bold; font-size: 13px; color: #cfd3dc;")
        lbl_id = QLabel("Installa i pacchetti necessari per la tua distro, abilita Docker, scarica Jellyfin e configura icone e comandi.")
        lbl_id.setStyleSheet("color: #9ba1b0; font-size: 11px;")
        desc_inst.addWidget(lbl_it)
        desc_inst.addWidget(lbl_id)

        self.btn_action_install = QPushButton("🚀  Installa da Zero")
        self.btn_action_install.setObjectName("btnStart")
        self.btn_action_install.setFixedHeight(40)
        self.btn_action_install.setFixedWidth(200)
        self.btn_action_install.clicked.connect(self.start_system_install)

        row_inst.addLayout(desc_inst)
        row_inst.addWidget(self.btn_action_install)
        ac_layout.addLayout(row_inst)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #282d3f;")
        ac_layout.addWidget(sep)

        row_uninst = QHBoxLayout()
        row_uninst.setSpacing(14)
        desc_uninst = QVBoxLayout()
        lbl_ut = QLabel("Disinstallazione Completa")
        lbl_ut.setStyleSheet("font-weight: bold; font-size: 13px; color: #f87171;")
        lbl_ud = QLabel("Arresta e rimuove container, immagini Docker, comandi locali e lanciatori desktop.")
        lbl_ud.setStyleSheet("color: #9ba1b0; font-size: 11px;")
        self.chk_purge_data = QCheckBox("Elimina anche i dati personali e librerie (~/jellyfin)")
        self.chk_purge_data.setObjectName("customCheck")
        desc_uninst.addWidget(lbl_ut)
        desc_uninst.addWidget(lbl_ud)
        desc_uninst.addWidget(self.chk_purge_data)

        self.btn_action_uninstall = QPushButton("🗑  Disinstalla Tutto")
        self.btn_action_uninstall.setObjectName("btnStop")
        self.btn_action_uninstall.setFixedHeight(40)
        self.btn_action_uninstall.setFixedWidth(200)
        self.btn_action_uninstall.clicked.connect(self.start_system_uninstall)

        row_uninst.addLayout(desc_uninst)
        row_uninst.addWidget(self.btn_action_uninstall)
        ac_layout.addLayout(row_uninst)
        layout.addWidget(actions_card)

        self.install_progress_card = QFrame()
        self.install_progress_card.setObjectName("cardFrame")
        ipc_layout = QVBoxLayout(self.install_progress_card)
        ipc_layout.setContentsMargins(14, 10, 14, 10)
        ipc_layout.setSpacing(8)

        ipc_header = QHBoxLayout()
        self.lbl_install_status = QLabel("Avanzamento Operazione:")
        self.lbl_install_status.setStyleSheet("font-weight: bold; color: #cfd3dc; font-size: 12px;")
        self.btn_cancel_install = QPushButton("❌  Annulla")
        self.btn_cancel_install.setObjectName("btnMini")
        self.btn_cancel_install.setStyleSheet("background-color: #7f1d1d; color: #fca5a5; border: 1px solid #991b1b;")
        self.btn_cancel_install.clicked.connect(self.cancel_system_action)
        self.btn_cancel_install.hide()

        ipc_header.addWidget(self.lbl_install_status)
        ipc_header.addStretch()
        ipc_header.addWidget(self.btn_cancel_install)
        ipc_layout.addLayout(ipc_header)

        self.bar_install_progress = QProgressBar()
        self.bar_install_progress.setRange(0, 100)
        self.bar_install_progress.setValue(0)
        self.bar_install_progress.setFixedHeight(12)
        ipc_layout.addWidget(self.bar_install_progress)

        self.txt_install_log = QPlainTextEdit()
        self.txt_install_log.setReadOnly(True)
        self.txt_install_log.setObjectName("terminalViewer")
        self.txt_install_log.setMaximumHeight(160)
        self.txt_install_log.setPlaceholderText("I log di installazione o disinstallazione verranno mostrati qui...")
        ipc_layout.addWidget(self.txt_install_log)
        layout.addWidget(self.install_progress_card)

    # -------------------------------------------------------------
    # TAB 5: BACKUP & RIPRISTINO (.ZIP)
    # -------------------------------------------------------------
    def setup_tab_backup(self):
        layout = QVBoxLayout(self.tab_backup)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Riquadro Creazione Backup
        b_card = QFrame()
        b_card.setObjectName("cardFrame")
        bc_layout = QVBoxLayout(b_card)
        bc_layout.setContentsMargins(16, 12, 16, 12)
        bc_layout.setSpacing(10)

        lbl_bt = QLabel("📦  Crea Backup dei Dati (.zip)")
        lbl_bt.setStyleSheet("font-size: 14px; font-weight: bold; color: #00d2ff;")
        lbl_bd = QLabel("Comprime la configurazione, gli utenti, il database con la cronologia e i file docker in un unico archivio .zip.")
        lbl_bd.setStyleSheet("color: #9ba1b0; font-size: 12px;")

        bc_row = QHBoxLayout()
        bc_row.setSpacing(10)
        self.txt_backup_dest = QLineEdit()
        today_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        default_dest = os.path.expanduser(f"~/Scrivania/Jellyfin_Backup_{today_str}.zip")
        self.txt_backup_dest.setText(default_dest)
        self.txt_backup_dest.setStyleSheet("background-color: #0d0f17; color: #cfd3dc; padding: 6px; border: 1px solid #232738; border-radius: 6px;")

        btn_browse_backup = QPushButton("Sfoglia...")
        btn_browse_backup.setObjectName("btnFolder")
        btn_browse_backup.clicked.connect(self.browse_backup_dest)

        self.btn_start_backup = QPushButton("Avvia Backup (.zip)")
        self.btn_start_backup.setObjectName("btnStart")
        self.btn_start_backup.setFixedHeight(34)
        self.btn_start_backup.clicked.connect(self.start_backup)

        bc_row.addWidget(self.txt_backup_dest)
        bc_row.addWidget(btn_browse_backup)
        bc_row.addWidget(self.btn_start_backup)

        self.chk_include_metadata = QCheckBox("Includi anche immagini, locandine e miniature (~9 GB)")
        self.chk_include_metadata.setObjectName("customCheck")
        self.chk_include_metadata.setToolTip("Se disattivato, il backup include solo database, utenti, librerie e configurazioni (~190 MB) ed è quasi istantaneo.")

        bc_layout.addWidget(lbl_bt)
        bc_layout.addWidget(lbl_bd)
        bc_layout.addLayout(bc_row)
        bc_layout.addWidget(self.chk_include_metadata)
        layout.addWidget(b_card)

        # Riquadro Ripristino da Backup
        r_card = QFrame()
        r_card.setObjectName("cardFrame")
        rc_layout = QVBoxLayout(r_card)
        rc_layout.setContentsMargins(16, 12, 16, 12)
        rc_layout.setSpacing(10)

        lbl_rt = QLabel("📥  Ripristina da un Backup (.zip)")
        lbl_rt.setStyleSheet("font-size: 14px; font-weight: bold; color: #b855d4;")
        lbl_rd = QLabel("Seleziona un file di backup precedentemente salvato. Jellyfin verrà arrestato temporaneamente durante il ripristino.")
        lbl_rd.setStyleSheet("color: #9ba1b0; font-size: 12px;")

        rc_row = QHBoxLayout()
        rc_row.setSpacing(10)
        self.txt_restore_src = QLineEdit()
        self.txt_restore_src.setPlaceholderText("Seleziona il file .zip di backup da ripristinare...")
        self.txt_restore_src.setStyleSheet("background-color: #0d0f17; color: #cfd3dc; padding: 6px; border: 1px solid #232738; border-radius: 6px;")

        btn_browse_restore = QPushButton("Sfoglia...")
        btn_browse_restore.setObjectName("btnFolder")
        btn_browse_restore.clicked.connect(self.browse_restore_src)

        self.btn_start_restore = QPushButton("Ripristina Dati")
        self.btn_start_restore.setObjectName("btnRestart")
        self.btn_start_restore.setFixedHeight(34)
        self.btn_start_restore.clicked.connect(self.start_restore)

        rc_row.addWidget(self.txt_restore_src)
        rc_row.addWidget(btn_browse_restore)
        rc_row.addWidget(self.btn_start_restore)

        rc_layout.addWidget(lbl_rt)
        rc_layout.addWidget(lbl_rd)
        rc_layout.addLayout(rc_row)
        layout.addWidget(r_card)

        # Monitoraggio Avanzato: Barra di progresso, Velocità MB/s, Calcolo ETA
        p_card = QFrame()
        p_card.setObjectName("cardFrame")
        pc_layout = QVBoxLayout(p_card)
        pc_layout.setContentsMargins(14, 10, 14, 10)
        pc_layout.setSpacing(8)

        pc_header = QHBoxLayout()
        self.lbl_backup_status = QLabel("Stato: In attesa di avvio")
        self.lbl_backup_status.setStyleSheet("font-weight: bold; color: #cfd3dc; font-size: 12px;")
        self.lbl_backup_eta = QLabel("Tempo Stimato (ETA): -")
        self.lbl_backup_eta.setStyleSheet("color: #00d2ff; font-weight: bold; font-size: 12px;")

        self.btn_cancel_backup = QPushButton("❌  Annulla Operazione")
        self.btn_cancel_backup.setObjectName("btnMini")
        self.btn_cancel_backup.setStyleSheet("background-color: #7f1d1d; color: #fca5a5; border: 1px solid #991b1b;")
        self.btn_cancel_backup.clicked.connect(self.cancel_backup_or_restore)
        self.btn_cancel_backup.hide()

        pc_header.addWidget(self.lbl_backup_status)
        pc_header.addStretch()
        pc_header.addWidget(self.lbl_backup_eta)
        pc_header.addWidget(self.btn_cancel_backup)
        pc_layout.addLayout(pc_header)

        self.bar_backup_progress = QProgressBar()
        self.bar_backup_progress.setRange(0, 100)
        self.bar_backup_progress.setValue(0)
        self.bar_backup_progress.setFixedHeight(12)
        pc_layout.addWidget(self.bar_backup_progress)

        self.txt_backup_log = QPlainTextEdit()
        self.txt_backup_log.setReadOnly(True)
        self.txt_backup_log.setObjectName("terminalViewer")
        self.txt_backup_log.setMaximumHeight(150)
        self.txt_backup_log.setPlaceholderText("Dettagli operazione di backup/ripristino...")
        pc_layout.addWidget(self.txt_backup_log)
        layout.addWidget(p_card)



    # -------------------------------------------------------------
    # TAB 6: GESTIONE PLUGIN INTRO SKIPPER
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # TAB 6: GESTIONE PLUGIN (INTRO SKIPPER & TRICKPLAY)
    # -------------------------------------------------------------
    def setup_tab_plugin(self):
        """
        Organizza la scheda Plugin in due comode sottoschede:
          1. Intro Skipper (salto automatico di sigle e crediti)
          2. Trickplay (generazione e gestione miniature di scorrimento video)
        """
        main_plugin_layout = QVBoxLayout(self.tab_plugin)
        main_plugin_layout.setContentsMargins(6, 6, 6, 6)
        main_plugin_layout.setSpacing(6)

        self.plugin_subtabs = QTabWidget()
        self.plugin_subtabs.setObjectName("mainTabs")

        # Subtab 1: Intro Skipper
        self.subtab_intro = QWidget()
        self.setup_subtab_intro_skipper()
        self.plugin_subtabs.addTab(self.subtab_intro, t("subtab_intro_skipper", self.current_lang))

        # Subtab 2: Trickplay
        self.subtab_trickplay = QWidget()
        self.setup_subtab_trickplay()
        self.plugin_subtabs.addTab(self.subtab_trickplay, t("subtab_trickplay", self.current_lang))

        main_plugin_layout.addWidget(self.plugin_subtabs)

    def setup_subtab_intro_skipper(self):
        """Costruisce i widget per Intro Skipper (preservando tutte le funzioni)."""
        layout = QVBoxLayout(self.subtab_intro)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # 1. Riquadro Stato Plugin e Azioni di Installazione/Rimozione
        plugin_card = QFrame()
        plugin_card.setObjectName("cardFrame")
        p_layout = QVBoxLayout(plugin_card)
        p_layout.setContentsMargins(14, 10, 14, 10)
        p_layout.setSpacing(8)

        p_header = QHBoxLayout()
        p_title_box = QVBoxLayout()
        lbl_p_title = QLabel("🎵  Plugin: Intro Skipper")
        lbl_p_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00d2ff;")
        lbl_p_desc = QLabel("Rilevamento e salto automatico di sigle introduttive (intro), titoli di coda e riassunti (recap).")
        lbl_p_desc.setStyleSheet("color: #9ba1b0; font-size: 11px;")
        p_title_box.addWidget(lbl_p_title)
        p_title_box.addWidget(lbl_p_desc)
        p_header.addLayout(p_title_box)
        p_header.addStretch()

        self.lbl_plugin_badge = QLabel("● VERIFICA IN CORSO...")
        self.lbl_plugin_badge.setStyleSheet("background-color: #272a38; color: #9ba1b0; border: 1px solid #3c4155; border-radius: 12px; padding: 4px 12px; font-weight: bold; font-size: 11px;")
        p_header.addWidget(self.lbl_plugin_badge)
        p_layout.addLayout(p_header)

        p_btn_row = QHBoxLayout()
        p_btn_row.setSpacing(10)

        self.btn_install_plugin = QPushButton("📥  Installa / Aggiorna")
        self.btn_install_plugin.setObjectName("btnStart")
        self.btn_install_plugin.setFixedHeight(32)
        self.btn_install_plugin.clicked.connect(self.install_intro_skipper_dialog)

        self.btn_uninstall_plugin = QPushButton("🗑️  Rimuovi Plugin")
        self.btn_uninstall_plugin.setObjectName("btnStop")
        self.btn_uninstall_plugin.setFixedHeight(32)
        self.btn_uninstall_plugin.clicked.connect(self.uninstall_intro_skipper_dialog)

        self.btn_open_web_config = QPushButton("🌐  Configurazione Web")
        self.btn_open_web_config.setObjectName("btnBrowser")
        self.btn_open_web_config.setFixedHeight(32)
        self.btn_open_web_config.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("http://localhost:8096/web/#/configurationpage?name=Intro%20Skipper")))

        p_btn_row.addWidget(self.btn_install_plugin)
        p_btn_row.addWidget(self.btn_uninstall_plugin)
        p_btn_row.addWidget(self.btn_open_web_config)
        p_btn_row.addStretch()
        p_layout.addLayout(p_btn_row)
        layout.addWidget(plugin_card)

        # 2. Riquadro Controllo Indicizzazione Media & Statistiche
        analysis_card = QFrame()
        analysis_card.setObjectName("cardFrame")
        a_layout = QVBoxLayout(analysis_card)
        a_layout.setContentsMargins(14, 10, 14, 10)
        a_layout.setSpacing(8)

        a_header = QHBoxLayout()
        lbl_a_title = QLabel("⚡  Indicizzazione Media & Rilevamento Segmenti")
        lbl_a_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #b855d4;")
        a_header.addWidget(lbl_a_title)
        a_header.addStretch()

        self.lbl_plugin_task_badge = QLabel("⏹️  INATTIVO")
        self.lbl_plugin_task_badge.setStyleSheet("background-color: #1f2937; color: #9ca3af; border: 1px solid #374151; border-radius: 12px; padding: 3px 10px; font-weight: bold; font-size: 11px;")
        a_header.addWidget(self.lbl_plugin_task_badge)
        a_layout.addLayout(a_header)

        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        self.btn_start_analysis = QPushButton("▶️  Avvia Analisi Media")
        self.btn_start_analysis.setObjectName("btnStart")
        self.btn_start_analysis.setFixedHeight(32)
        self.btn_start_analysis.clicked.connect(self.start_intro_skipper_analysis)

        self.btn_stop_analysis = QPushButton("⏹️  Arresta Analisi")
        self.btn_stop_analysis.setObjectName("btnStop")
        self.btn_stop_analysis.setFixedHeight(32)
        self.btn_stop_analysis.clicked.connect(self.stop_intro_skipper_analysis)

        self.btn_refresh_plugin = QPushButton("🔄  Aggiorna")
        self.btn_refresh_plugin.setObjectName("btnMini")
        self.btn_refresh_plugin.setFixedHeight(32)
        self.btn_refresh_plugin.clicked.connect(self.poll_plugin_status)

        ctrl_row.addWidget(self.btn_start_analysis)
        ctrl_row.addWidget(self.btn_stop_analysis)
        ctrl_row.addWidget(self.btn_refresh_plugin)
        ctrl_row.addStretch()
        a_layout.addLayout(ctrl_row)

        prog_row = QHBoxLayout()
        self.lbl_plugin_prog_desc = QLabel("Progresso:")
        self.lbl_plugin_prog_desc.setStyleSheet("color: #cfd3dc; font-weight: bold; font-size: 11px;")
        self.lbl_plugin_progress_pct = QLabel("0.0%")
        self.lbl_plugin_progress_pct.setStyleSheet("color: #00d2ff; font-weight: bold; font-size: 12px;")
        prog_row.addWidget(self.lbl_plugin_prog_desc)
        prog_row.addStretch()
        prog_row.addWidget(self.lbl_plugin_progress_pct)
        a_layout.addLayout(prog_row)

        self.bar_plugin_progress = QProgressBar()
        self.bar_plugin_progress.setRange(0, 100)
        self.bar_plugin_progress.setValue(0)
        self.bar_plugin_progress.setFixedHeight(10)
        a_layout.addWidget(self.bar_plugin_progress)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(8)

        def create_stat_subcard(title, initial_val, color):
            frame = QFrame()
            frame.setStyleSheet("background-color: #12141c; border: 1px solid #232738; border-radius: 8px; padding: 4px;")
            l = QVBoxLayout(frame)
            l.setContentsMargins(6, 3, 6, 3)
            l.setSpacing(2)
            t = QLabel(title)
            t.setStyleSheet("color: #9ba1b0; font-size: 10px; font-weight: bold;")
            v = QLabel(initial_val)
            v.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
            l.addWidget(t)
            l.addWidget(v)
            return frame, v

        card_tot, self.lbl_plugin_total_media = create_stat_subcard("Totale Media Libreria", "...", "#ffffff")
        card_proc, self.lbl_plugin_analyzed_media = create_stat_subcard("File Già Processati", "...", "#34d399")
        card_rem, self.lbl_plugin_remaining_media = create_stat_subcard("File Rimanenti", "...", "#fbbf24")
        card_seg, self.lbl_plugin_segments_detected = create_stat_subcard("Segmenti Rilevati (Intro)", "...", "#38bdf8")

        stats_grid.addWidget(card_tot, 0, 0)
        stats_grid.addWidget(card_proc, 0, 1)
        stats_grid.addWidget(card_rem, 0, 2)
        stats_grid.addWidget(card_seg, 0, 3)
        a_layout.addLayout(stats_grid)
        layout.addWidget(analysis_card)

        # 3. Registro Eventi & Log Live
        log_card = QFrame()
        log_card.setObjectName("cardFrame")
        l_layout = QVBoxLayout(log_card)
        l_layout.setContentsMargins(14, 8, 14, 8)
        l_layout.setSpacing(6)

        l_header = QHBoxLayout()
        lbl_l_title = QLabel("📋  Registro File Elaborati & In Corso (Tempo Reale)")
        lbl_l_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #cfd3dc;")
        l_header.addWidget(lbl_l_title)
        l_header.addStretch()

        self.chk_plugin_autoscroll = QCheckBox("Auto-scroll")
        self.chk_plugin_autoscroll.setObjectName("customCheck")
        self.chk_plugin_autoscroll.setChecked(True)
        l_header.addWidget(self.chk_plugin_autoscroll)

        btn_clear_log = QPushButton("Pulisci")
        btn_clear_log.setObjectName("btnMini")
        btn_clear_log.clicked.connect(lambda: self.txt_plugin_log.clear())
        l_header.addWidget(btn_clear_log)

        l_layout.addLayout(l_header)

        self.txt_plugin_log = QPlainTextEdit()
        self.txt_plugin_log.setReadOnly(True)
        self.txt_plugin_log.setObjectName("terminalViewer")
        self.txt_plugin_log.setMinimumHeight(120)
        l_layout.addWidget(self.txt_plugin_log)
        layout.addWidget(log_card)

    def setup_subtab_trickplay(self):
        """Costruisce i widget per la gestione del plugin e modulo Trickplay."""
        layout = QVBoxLayout(self.subtab_trickplay)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # 1. Riquadro Stato Plugin Trickplay
        plugin_card = QFrame()
        plugin_card.setObjectName("cardFrame")
        p_layout = QVBoxLayout(plugin_card)
        p_layout.setContentsMargins(14, 10, 14, 10)
        p_layout.setSpacing(8)

        p_header = QHBoxLayout()
        p_title_box = QVBoxLayout()
        lbl_p_title = QLabel("🖼️  Plugin: Trickplay (Miniature di Scorrimento & Scrubbing)")
        lbl_p_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00d2ff;")
        lbl_p_desc = QLabel("Genera riquadri BIF e sequenze di anteprima temporale per lo scorrimento veloce dei video.")
        lbl_p_desc.setStyleSheet("color: #9ba1b0; font-size: 11px;")
        p_title_box.addWidget(lbl_p_title)
        p_title_box.addWidget(lbl_p_desc)
        p_header.addLayout(p_title_box)
        p_header.addStretch()

        self.lbl_tp_badge = QLabel("● VERIFICA IN CORSO...")
        self.lbl_tp_badge.setStyleSheet("background-color: #272a38; color: #9ba1b0; border: 1px solid #3c4155; border-radius: 12px; padding: 4px 12px; font-weight: bold; font-size: 11px;")
        p_header.addWidget(self.lbl_tp_badge)
        p_layout.addLayout(p_header)

        p_btn_row = QHBoxLayout()
        p_btn_row.setSpacing(10)

        self.btn_install_tp = QPushButton("📥  Installa / Configura")
        self.btn_install_tp.setObjectName("btnStart")
        self.btn_install_tp.setFixedHeight(32)
        self.btn_install_tp.clicked.connect(self.install_trickplay_dialog)

        self.btn_uninstall_tp = QPushButton("🗑️  Rimuovi Modulo")
        self.btn_uninstall_tp.setObjectName("btnStop")
        self.btn_uninstall_tp.setFixedHeight(32)
        self.btn_uninstall_tp.clicked.connect(self.uninstall_trickplay_dialog)

        self.btn_web_config_tp = QPushButton("🌐  Pannello Web Trickplay")
        self.btn_web_config_tp.setObjectName("btnBrowser")
        self.btn_web_config_tp.setFixedHeight(32)
        self.btn_web_config_tp.clicked.connect(self.open_trickplay_web_config)

        p_btn_row.addWidget(self.btn_install_tp)
        p_btn_row.addWidget(self.btn_uninstall_tp)
        p_btn_row.addWidget(self.btn_web_config_tp)
        p_btn_row.addStretch()
        p_layout.addLayout(p_btn_row)
        layout.addWidget(plugin_card)

        # 2. Riquadro Controllo Task & Statistiche Trickplay
        analysis_card = QFrame()
        analysis_card.setObjectName("cardFrame")
        a_layout = QVBoxLayout(analysis_card)
        a_layout.setContentsMargins(14, 10, 14, 10)
        a_layout.setSpacing(8)

        a_header = QHBoxLayout()
        lbl_a_title = QLabel("⚡  Generazione Immagini Trickplay & Monitoraggio Attività")
        lbl_a_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #b855d4;")
        a_header.addWidget(lbl_a_title)
        a_header.addStretch()

        self.lbl_tp_task_badge = QLabel("⏹️  INATTIVO")
        self.lbl_tp_task_badge.setStyleSheet("background-color: #1f2937; color: #9ca3af; border: 1px solid #374151; border-radius: 12px; padding: 3px 10px; font-weight: bold; font-size: 11px;")
        a_header.addWidget(self.lbl_tp_task_badge)
        a_layout.addLayout(a_header)

        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        self.btn_start_tp = QPushButton("▶️  Avvia Analisi File")
        self.btn_start_tp.setObjectName("btnStart")
        self.btn_start_tp.setFixedHeight(32)
        self.btn_start_tp.clicked.connect(self.start_trickplay_analysis)

        self.btn_stop_tp = QPushButton("⏹️  Arresta Analisi")
        self.btn_stop_tp.setObjectName("btnStop")
        self.btn_stop_tp.setFixedHeight(32)
        self.btn_stop_tp.clicked.connect(self.stop_trickplay_analysis)

        self.btn_reset_tp = QPushButton("🔄  Reset & Ricostruisci Libreria")
        self.btn_reset_tp.setObjectName("btnRestart")
        self.btn_reset_tp.setFixedHeight(32)
        self.btn_reset_tp.clicked.connect(self.reset_trickplay_library)

        self.btn_refresh_tp = QPushButton("🔄  Aggiorna")
        self.btn_refresh_tp.setObjectName("btnMini")
        self.btn_refresh_tp.setFixedHeight(32)
        self.btn_refresh_tp.clicked.connect(self.poll_plugin_status)

        ctrl_row.addWidget(self.btn_start_tp)
        ctrl_row.addWidget(self.btn_stop_tp)
        ctrl_row.addWidget(self.btn_reset_tp)
        ctrl_row.addWidget(self.btn_refresh_tp)
        ctrl_row.addStretch()
        a_layout.addLayout(ctrl_row)

        prog_row = QHBoxLayout()
        self.lbl_tp_prog_desc = QLabel("Progresso Generazione Miniature:")
        self.lbl_tp_prog_desc.setStyleSheet("color: #cfd3dc; font-weight: bold; font-size: 11px;")
        self.lbl_tp_progress_pct = QLabel("0.0%")
        self.lbl_tp_progress_pct.setStyleSheet("color: #00d2ff; font-weight: bold; font-size: 12px;")
        prog_row.addWidget(self.lbl_tp_prog_desc)
        prog_row.addStretch()
        prog_row.addWidget(self.lbl_tp_progress_pct)
        a_layout.addLayout(prog_row)

        self.bar_tp_progress = QProgressBar()
        self.bar_tp_progress.setRange(0, 100)
        self.bar_tp_progress.setValue(0)
        self.bar_tp_progress.setFixedHeight(10)
        a_layout.addWidget(self.bar_tp_progress)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(8)

        def create_stat_subcard(title, initial_val, color):
            frame = QFrame()
            frame.setStyleSheet("background-color: #12141c; border: 1px solid #232738; border-radius: 8px; padding: 4px;")
            l = QVBoxLayout(frame)
            l.setContentsMargins(6, 3, 6, 3)
            l.setSpacing(2)
            t = QLabel(title)
            t.setStyleSheet("color: #9ba1b0; font-size: 10px; font-weight: bold;")
            v = QLabel(initial_val)
            v.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
            l.addWidget(t)
            l.addWidget(v)
            return frame, v

        card_gen, self.lbl_tp_generated = create_stat_subcard("Media con Miniature Generate", "...", "#34d399")
        card_tot, self.lbl_tp_total = create_stat_subcard("Totale Media Libreria", "...", "#ffffff")
        card_rem, self.lbl_tp_remaining = create_stat_subcard("Media Rimanenti", "...", "#fbbf24")
        card_size, self.lbl_tp_size = create_stat_subcard("Dimensione Dati Trickplay", "...", "#38bdf8")

        stats_grid.addWidget(card_gen, 0, 0)
        stats_grid.addWidget(card_tot, 0, 1)
        stats_grid.addWidget(card_rem, 0, 2)
        stats_grid.addWidget(card_size, 0, 3)
        a_layout.addLayout(stats_grid)
        layout.addWidget(analysis_card)

        # 3. Registro Log Live Trickplay
        log_card = QFrame()
        log_card.setObjectName("cardFrame")
        l_layout = QVBoxLayout(log_card)
        l_layout.setContentsMargins(14, 8, 14, 8)
        l_layout.setSpacing(6)

        l_header = QHBoxLayout()
        lbl_l_title = QLabel("📋  Registro Attività & Log Trickplay (Tempo Reale)")
        lbl_l_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #cfd3dc;")
        l_header.addWidget(lbl_l_title)
        l_header.addStretch()

        self.chk_tp_autoscroll = QCheckBox("Auto-scroll")
        self.chk_tp_autoscroll.setObjectName("customCheck")
        self.chk_tp_autoscroll.setChecked(True)
        l_header.addWidget(self.chk_tp_autoscroll)

        btn_clear_log = QPushButton("Pulisci")
        btn_clear_log.setObjectName("btnMini")
        btn_clear_log.clicked.connect(lambda: self.txt_tp_log.clear())
        l_header.addWidget(btn_clear_log)

        l_layout.addLayout(l_header)

        self.txt_tp_log = QPlainTextEdit()
        self.txt_tp_log.setReadOnly(True)
        self.txt_tp_log.setObjectName("terminalViewer")
        self.txt_tp_log.setMinimumHeight(120)
        l_layout.addWidget(self.txt_tp_log)
        layout.addWidget(log_card)

    # -------------------------------------------------------------
    # METODI DI BACKUP E RIPRISTINO
    # -------------------------------------------------------------
    def browse_backup_dest(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Scegli dove salvare il backup", self.txt_backup_dest.text(), "Archivi Zip (*.zip)"
        )
        if filename:
            if not filename.endswith(".zip"):
                filename += ".zip"
            self.txt_backup_dest.setText(filename)

    def browse_restore_src(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Seleziona archivio di ripristino", os.path.expanduser("~/Scrivania"), "Archivi Zip (*.zip)"
        )
        if filename:
            self.txt_restore_src.setText(filename)

    def start_backup(self):
        dest_path = self.txt_backup_dest.text().strip()
        if not dest_path:
            QMessageBox.warning(self, "Attenzione", "Specifica un percorso di destinazione valido per il backup.")
            return

        self.btn_start_backup.setEnabled(False)
        self.btn_start_restore.setEnabled(False)
        self.btn_cancel_backup.show()
        self.bar_backup_progress.setValue(0)
        self.txt_backup_log.clear()
        self.lbl_backup_status.setText("Stato: Creazione backup in corso...")
        self.lbl_backup_eta.setText("Calcolo ETA...")

        include_meta = self.chk_include_metadata.isChecked()
        self.backup_worker = BackupWorker(dest_path, include_metadata=include_meta)
        self.backup_worker.progress.connect(self.on_backup_progress)
        self.backup_worker.log.connect(self.on_backup_log)
        self.backup_worker.finished.connect(self.on_backup_finished)
        self.backup_worker.start()

    def start_restore(self):
        src_path = self.txt_restore_src.text().strip()
        if not src_path or not os.path.exists(src_path):
            QMessageBox.warning(self, "Attenzione", "Seleziona un file .zip di backup esistente.")
            return

        res = QMessageBox.question(
            self, "Conferma Ripristino",
            "Il ripristino sovrascriverà la configurazione e il database attuali di Jellyfin.\nContinuare?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res != QMessageBox.StandardButton.Yes:
            return

        self.btn_start_backup.setEnabled(False)
        self.btn_start_restore.setEnabled(False)
        self.btn_cancel_backup.show()
        self.bar_backup_progress.setValue(0)
        self.txt_backup_log.clear()
        self.lbl_backup_status.setText("Stato: Ripristino in corso...")
        self.lbl_backup_eta.setText("Calcolo ETA...")

        self.restore_worker = RestoreWorker(src_path)
        self.restore_worker.progress.connect(self.on_backup_progress)
        self.restore_worker.log.connect(self.on_backup_log)
        self.restore_worker.finished.connect(self.on_restore_finished)
        self.restore_worker.start()

    def cancel_backup_or_restore(self):
        if self.backup_worker and self.backup_worker.isRunning():
            self.lbl_backup_status.setText("Stato: Annullamento e pulizia atomica...")
            self.backup_worker.cancel()
        if self.restore_worker and self.restore_worker.isRunning():
            self.lbl_backup_status.setText("Stato: Annullamento e rollback...")
            self.restore_worker.cancel()

    def on_backup_progress(self, pct, done, total, speed, eta):
        self.bar_backup_progress.setValue(pct)
        done_mb = done / (1024 * 1024)
        tot_mb = total / (1024 * 1024)
        speed_mbs = speed / (1024 * 1024)

        if eta > 60:
            eta_str = f"{int(eta//60)}m {int(eta%60)}s"
        else:
            eta_str = f"{int(eta)}s"

        self.lbl_backup_status.setText(f"Avanzamento: {done_mb:.1f} / {tot_mb:.1f} MB ({speed_mbs:.1f} MB/s)")
        self.lbl_backup_eta.setText(f"Tempo Rimanente Stimato: {eta_str}")

    def on_backup_log(self, text):
        self.txt_backup_log.appendPlainText(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {text}")

    def on_backup_finished(self, success, message):
        self.btn_start_backup.setEnabled(True)
        self.btn_start_restore.setEnabled(True)
        self.btn_cancel_backup.hide()
        self.lbl_backup_eta.setText("Tempo Stimato (ETA): -")
        self.lbl_backup_status.setText(f"Stato: {message}")
        if success:
            QMessageBox.information(self, "Backup Completato", message)
        else:
            QMessageBox.warning(self, "Operazione Terminata", message)

    def on_restore_finished(self, success, message):
        self.btn_start_backup.setEnabled(True)
        self.btn_start_restore.setEnabled(True)
        self.btn_cancel_backup.hide()
        self.lbl_backup_eta.setText("Tempo Stimato (ETA): -")
        self.lbl_backup_status.setText(f"Stato: {message}")
        if success:
            QMessageBox.information(self, "Ripristino Completato", f"{message}\nPuoi ora riavviare Jellyfin dalla scheda Controllo.")
        else:
            QMessageBox.warning(self, "Operazione Terminata", message)

    # -------------------------------------------------------------
    # METODI DI INSTALLAZIONE E DISINSTALLAZIONE
    # -------------------------------------------------------------
    def request_sudo_password(self):
        """Richiede la password di root all'utente con un dialogo grafico protetto."""
        pwd, ok = QInputDialog.getText(
            self, "Autenticazione Richiesta",
            "Inserisci la password di amministratore (sudo) per eseguire l'operazione di sistema:",
            QLineEdit.EchoMode.Password
        )
        if not ok or not pwd:
            return None

        # Verifica preliminare immediata della correttezza della password
        test_cmd = f"echo '{pwd}' | sudo -S -v"
        res = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            QMessageBox.critical(self, "Autenticazione Fallita", "La password di amministratore inserita non è corretta.")
            return None
        return pwd

    def start_system_install(self):
        pwd = self.request_sudo_password()
        if not pwd:
            return

        self.btn_action_install.setEnabled(False)
        self.btn_action_uninstall.setEnabled(False)
        self.btn_cancel_install.show()
        self.bar_install_progress.setValue(0)
        self.txt_install_log.clear()
        self.lbl_install_status.setText("Avanzamento: Installazione in corso...")

        self.install_worker = SystemInstallerWorker("install", pwd)
        self.install_worker.progress.connect(self.on_install_progress)
        self.install_worker.log.connect(self.on_install_log)
        self.install_worker.finished.connect(self.on_install_finished)
        self.install_worker.start()

    def start_system_uninstall(self):
        purge = self.chk_purge_data.isChecked()
        extra_warn = "\n\nATTENZIONE: Verrà eliminata anche la cartella ~/jellyfin contenente tutti i dati personali e le librerie!" if purge else ""
        res = QMessageBox.warning(
            self, "Conferma Disinstallazione",
            f"Sei sicuro di voler rimuovere Jellyfin e tutti i suoi componenti dal sistema?{extra_warn}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res != QMessageBox.StandardButton.Yes:
            return

        self.btn_action_install.setEnabled(False)
        self.btn_action_uninstall.setEnabled(False)
        self.btn_cancel_install.show()
        self.bar_install_progress.setValue(0)
        self.txt_install_log.clear()
        self.lbl_install_status.setText("Avanzamento: Disinstallazione in corso...")

        self.install_worker = SystemInstallerWorker("uninstall", "", purge_data=purge)
        self.install_worker.progress.connect(self.on_install_progress)
        self.install_worker.log.connect(self.on_install_log)
        self.install_worker.finished.connect(self.on_install_finished)
        self.install_worker.start()

    def cancel_system_action(self):
        if self.install_worker and self.install_worker.isRunning():
            self.lbl_install_status.setText("Avanzamento: Annullamento in corso...")
            self.install_worker.cancel()

    def on_install_progress(self, pct, desc):
        self.bar_install_progress.setValue(pct)
        self.lbl_install_status.setText(f"Avanzamento: {desc} ({pct}%)")

    def on_install_log(self, line):
        self.txt_install_log.appendPlainText(line)
        self.txt_install_log.verticalScrollBar().setValue(self.txt_install_log.verticalScrollBar().maximum())

    def on_install_finished(self, success, message):
        self.btn_action_install.setEnabled(True)
        self.btn_action_uninstall.setEnabled(True)
        self.btn_cancel_install.hide()
        self.lbl_install_status.setText(f"Avanzamento: {message}")
        if success:
            QMessageBox.information(self, "Operazione Completata", message)
        else:
            QMessageBox.warning(self, "Operazione Conclusa", message)

    # -------------------------------------------------------------
    # GESTIONE EVENTI E POLLING (CPU / GPU / SESSIONI)
    # -------------------------------------------------------------
    def on_tab_changed(self, index):
        """
        Gestisce l'attivazione/disattivazione dinamica dei timer.
        Garantisce che il monitoraggio hardware e sessioni consumi risorse SOLO
        quando la rispettiva scheda è aperta e visualizzata.
        """
        if index == 1:
            self.poll_active_sessions()
            if not self.sessions_timer.isActive():
                self.sessions_timer.start(3500)
        else:
            self.sessions_timer.stop()

        if index == 2:
            if self.chk_monitor_hw.isChecked():
                self.start_hw_monitoring()
        else:
            # Se ci si sposta da Monitor Hardware, arresta il timer (0% CPU)
            self.stop_hw_monitoring()

        # Tab 5 (Plugin): attiva il polling solo quando visualizzato
        if index == 5:
            self.poll_plugin_status()
            if not self.plugin_timer.isActive():
                self.plugin_timer.start(3000)
        else:
            self.plugin_timer.stop()

    def toggle_sessions_view_mode(self, checked):
        self.sessions_stack.setCurrentIndex(1 if checked else 0)

    def toggle_hw_view_mode(self, checked):
        self.hw_stack.setCurrentIndex(1 if checked else 0)

    def toggle_hardware_monitoring(self, checked):
        if checked:
            self.start_hw_monitoring()
        else:
            self.stop_hw_monitoring()

    def start_hw_monitoring(self):
        self.lbl_hw_status.setText("Stato: ATTIVO (Aggiornamento ogni 2s)")
        self.lbl_hw_status.setStyleSheet("color: #34d399; font-weight: bold; font-size: 12px;")
        if not self.hw_timer.isActive():
            self.hw_timer.start(2000)
        self.poll_hardware_metrics()

    def stop_hw_monitoring(self):
        self.hw_timer.stop()
        self.lbl_hw_status.setText("Stato: DISATTIVO (0% consumo)")
        self.lbl_hw_status.setStyleSheet("color: #9ba1b0; font-weight: bold; font-size: 12px;")

    def poll_hardware_metrics(self):
        """Interroga i sensori di sistema (CPU, RAM, GPU NVIDIA, Container Docker)."""
        # 1. CPU
        try:
            cpu_pct = psutil.cpu_percent(interval=None)
            self.lbl_cpu_val.setText(f"{cpu_pct:.1f}%")
            self.bar_cpu.setValue(int(cpu_pct))
        except Exception:
            cpu_pct = 0.0

        # 2. RAM
        try:
            vm = psutil.virtual_memory()
            ram_pct = vm.percent
            used_gb = vm.used / (1024**3)
            tot_gb = vm.total / (1024**3)
            self.lbl_ram_val.setText(f"{ram_pct:.1f}%")
            self.lbl_ram_details.setText(f"{used_gb:.1f} GB / {tot_gb:.1f} GB")
            self.bar_ram.setValue(int(ram_pct))
        except Exception:
            pass

        # 3. GPU NVIDIA (Interrogazione nativa ultrarapida ~40ms via nvidia-smi)
        gpu_output_raw = ""
        try:
            res = subprocess.check_output([
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
                "--format=csv,noheader,nounits"
            ], text=True, timeout=1).strip()
            parts = [p.strip() for p in res.split(",")]
            if len(parts) >= 5:
                gpu_util = int(parts[0])
                mem_used = int(parts[1])
                mem_total = int(parts[2])
                temp = parts[3]
                power = parts[4]

                self.lbl_gpu_val.setText(f"{gpu_util}%")
                self.bar_gpu.setValue(gpu_util)
                self.lbl_gpu_vram.setText(f"VRAM: {mem_used} / {mem_total} MB ({int(mem_used*100/mem_total)}%)")
                self.lbl_gpu_temp.setText(f"Temperatura: {temp} °C")
                self.lbl_gpu_power.setText(f"Consumo: {power} W")
                gpu_output_raw = f"NVIDIA GPU: Util: {gpu_util}% | VRAM: {mem_used}/{mem_total} MB | Temp: {temp}°C | Power: {power}W\n"
        except Exception as e:
            self.lbl_gpu_val.setText("N/D")
            gpu_output_raw = f"NVIDIA query error: {e}\n"

        # 4. Container Docker
        docker_raw = ""
        try:
            d_res = subprocess.run([
                "docker", "stats", "--no-stream", "--format", "CPU: {{.CPUPerc}} | RAM: {{.MemUsage}}", "jellyfin"
            ], capture_output=True, text=True, timeout=1)
            if d_res.returncode == 0 and d_res.stdout.strip():
                stats_str = d_res.stdout.strip()
                self.lbl_docker_stats.setText(f"Container Docker Jellyfin: {stats_str}")
                docker_raw = f"Docker stats: {stats_str}\n"
            else:
                self.lbl_docker_stats.setText("Container Docker Jellyfin: Fermo o non monitorabile")
                docker_raw = "Docker: Jellyfin non attivo\n"
        except Exception:
            pass

        if self.chk_hw_view_mode.isChecked():
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            raw_text = (
                f"=== METRICHE RISORSE HARDWARE ({now_str}) ===\n"
                f"CPU Util: {cpu_pct:.1f}% (Intel Core i7-8700K)\n"
                f"RAM Util: {self.lbl_ram_details.text()} ({self.lbl_ram_val.text()})\n"
                f"{gpu_output_raw}"
                f"{docker_raw}"
            )
            self.hw_terminal_view.setPlainText(raw_text)

    def poll_active_sessions(self):
        """Interroga l'API REST di Jellyfin (/Sessions) per popolare la tabella dei dispositivi."""
        url = "http://localhost:8096/Sessions"
        headers = {"Authorization": f'MediaBrowser Token="{self.api_key}"'}
        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            self.lbl_sessions_count.setText("Dispositivi Connessi: Server non raggiungibile")
            self.sessions_table.setRowCount(0)
            self.sessions_terminal_view.setPlainText(f"Errore connessione a Jellyfin API /Sessions: {e}")
            return

        active_sessions = data
        self.lbl_sessions_count.setText(f"Dispositivi Connessi: {len(active_sessions)}")
        self.sessions_terminal_view.setPlainText(json.dumps(active_sessions, indent=2))

        self.sessions_table.setRowCount(len(active_sessions))
        for row, s in enumerate(active_sessions):
            user_name = s.get("UserName", "N/D")
            device_name = s.get("DeviceName", "Sconosciuto")
            client_name = s.get("Client", "Jellyfin")
            client_ip = s.get("RemoteEndPoint", "127.0.0.1")

            now_playing = s.get("NowPlayingItem")
            play_state = s.get("PlayState", {})
            is_paused = play_state.get("IsPaused", False)

            if now_playing:
                title = now_playing.get("Name", "Video")
                series = now_playing.get("SeriesName", "")
                if series:
                    title = f"{series} - {title}"

                trans_info = s.get("TranscodingInfo")
                trans_badge = ""
                if trans_info:
                    is_direct = trans_info.get("IsVideoDirect", False)
                    v_codec = trans_info.get("VideoCodec", "")
                    trans_badge = " (Diretto)" if is_direct else f" (Trascodifica {v_codec})"

                status_str = f"⏸ Pausa: {title}" if is_paused else f"▶ In riproduzione: {title}{trans_badge}"
            else:
                status_str = "💤 Inattivo (Navigazione menu)"

            last_act_str = s.get("LastActivityDate", "")
            time_display = "Adesso"
            if last_act_str:
                try:
                    cleaned_date = last_act_str.split(".")[0] + "Z"
                    act_dt = datetime.datetime.fromisoformat(cleaned_date.replace("Z", "+00:00"))
                    diff = (datetime.datetime.now(datetime.timezone.utc) - act_dt).total_seconds()
                    if diff < 60:
                        time_display = "Attivo adesso"
                    elif diff < 3600:
                        time_display = f"{int(diff//60)} min fa"
                    else:
                        time_display = f"{int(diff//3600)}h fa"
                except Exception:
                    time_display = last_act_str[:16]

            item_user = QTableWidgetItem(f"👤 {user_name}")
            item_device = QTableWidgetItem(f"📱 {device_name} ({client_name} - {client_ip})")
            item_status = QTableWidgetItem(status_str)
            item_time = QTableWidgetItem(time_display)

            if now_playing and not is_paused:
                item_status.setForeground(QColor("#34d399"))
            elif now_playing and is_paused:
                item_status.setForeground(QColor("#fbbf24"))
            else:
                item_status.setForeground(QColor("#9ba1b0"))

            self.sessions_table.setItem(row, 0, item_user)
            self.sessions_table.setItem(row, 1, item_device)
            self.sessions_table.setItem(row, 2, item_status)
            self.sessions_table.setItem(row, 3, item_time)

    def update_server_status(self):
        """Verifica se il container Docker 'jellyfin' è in esecuzione o arrestato."""
        if self.is_operating:
            return

        try:
            cmd = ["docker", "ps", "--filter", "name=jellyfin", "--filter", "status=running", "--format", "{{.Status}}"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            running = ("Up" in res.stdout)

            if running:
                self.current_status = "running"
                self.header_status_badge.setText("●  IN ESECUZIONE")
                self.header_status_badge.setObjectName("statusBadgeRunning")

                uptime_str = res.stdout.strip()
                self.lbl_val_uptime.setText(uptime_str)

                self.btn_start.setEnabled(False)
                self.btn_stop.setEnabled(True)
                self.btn_restart.setEnabled(True)
                self.btn_browser.setEnabled(True)
            else:
                self.current_status = "stopped"
                self.header_status_badge.setText("●  ARRESTATO")
                self.header_status_badge.setObjectName("statusBadgeStopped")
                self.lbl_val_uptime.setText("Server fermo (Nessuna risorsa occupata)")

                self.btn_start.setEnabled(True)
                self.btn_stop.setEnabled(False)
                self.btn_restart.setEnabled(False)
                self.btn_browser.setEnabled(False)

            self.header_status_badge.style().unpolish(self.header_status_badge)
            self.header_status_badge.style().polish(self.header_status_badge)

        except Exception as e:
            self.lbl_val_uptime.setText(f"Errore Docker: {str(e)[:40]}")

    def fetch_logs(self):
        """Recupera le ultime 50 righe di log del container Docker."""
        try:
            res = subprocess.run(["docker", "logs", "--tail", "50", "jellyfin"], capture_output=True, text=True, timeout=2)
            out = res.stdout + res.stderr
            if out.strip():
                self.txt_logs.setPlainText(out.strip())
                self.txt_logs.verticalScrollBar().setValue(self.txt_logs.verticalScrollBar().maximum())
            else:
                self.txt_logs.setPlainText("Nessun log disponibile o container arrestato.")
        except Exception as e:
            self.txt_logs.setPlainText(f"Errore lettura log: {e}")

    def execute_action(self, action_name, message):
        self.is_operating = True
        self.global_progress.show()
        self.header_status_badge.setText(f"●  {message}...")
        self.header_status_badge.setObjectName("statusBadgeWait")
        self.header_status_badge.style().unpolish(self.header_status_badge)
        self.header_status_badge.style().polish(self.header_status_badge)

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_restart.setEnabled(False)
        self.btn_browser.setEnabled(False)

        self.worker = CommandWorker(action_name)
        self.worker.finished.connect(self.on_action_finished)
        self.worker.start()

    def on_action_finished(self, success, output):
        self.is_operating = False
        self.global_progress.hide()
        self.update_server_status()
        self.fetch_logs()
        if self.tab_widget.currentIndex() == 1:
            self.poll_active_sessions()

    def start_jellyfin(self):
        self.execute_action("start", "AVVIO IN CORSO")

    def stop_jellyfin(self):
        self.execute_action("stop", "ARRESTO IN CORSO")

    def restart_jellyfin(self):
        self.execute_action("restart", "RIAVVIO IN CORSO")

    def copy_to_clipboard(self, text, desc):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QToolTip.showText(self.cursor().pos(), f"{desc} copiato negli appunti!")

    def open_browser(self):
        QDesktopServices.openUrl(QUrl("http://localhost:8096"))

    def open_folder(self, path):
        if os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(self, "Cartella non trovata", f"La cartella {path} non esiste ancora.")

    def update_system_integration_button(self):
        """Aggiorna lo stato visivo e il testo del pulsante di integrazione desktop XDG."""
        if not hasattr(self, "btn_system_integration"):
            return
        desktop_file = os.path.expanduser("~/.local/share/applications/jellyfin-control-center.desktop")
        is_installed = os.path.exists(desktop_file)
        if is_installed:
            self.btn_system_integration.setText(t("btn_system_integration_disable", self.current_lang))
            self.btn_system_integration.setToolTip(t("system_integrated_badge", self.current_lang))
            self.btn_system_integration.setStyleSheet("background-color: #1a365d; border: 1px solid #3182ce; color: #63b3ed; border-radius: 6px; font-weight: bold;")
        else:
            self.btn_system_integration.setText(t("btn_system_integration_enable", self.current_lang))
            self.btn_system_integration.setToolTip(t("system_not_integrated_badge", self.current_lang))
            self.btn_system_integration.setStyleSheet("background-color: #1e2430; border: 1px solid #2e3848; color: #e6edf3; border-radius: 6px; font-weight: bold;")

    def toggle_system_integration(self):
        """Abilita o disabilita l'integrazione dell'app nel menu di sistema e nella barra delle applicazioni."""
        apps_dir = os.path.expanduser("~/.local/share/applications")
        icons_dir = os.path.expanduser("~/.local/share/icons/hicolor/256x256/apps")
        desktop_file = os.path.join(apps_dir, "jellyfin-control-center.desktop")

        os.makedirs(apps_dir, exist_ok=True)
        os.makedirs(icons_dir, exist_ok=True)

        if os.path.exists(desktop_file):
            try:
                os.remove(desktop_file)
                subprocess.run(["update-desktop-database", apps_dir], capture_output=True)
                self.update_system_integration_button()
                QMessageBox.information(
                    self,
                    t("system_integration_title", self.current_lang),
                    t("system_integration_removed_msg", self.current_lang)
                )
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Impossibile rimuovere il collegamento: {e}")
        else:
            try:
                # 1. Copia l'icona dell'applicazione
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                icon_src = os.path.join(base_dir, "icons", "jellyfin-control.png")
                icon_dst = os.path.join(icons_dir, "jellyfin-control.png")
                if os.path.exists(icon_src):
                    shutil.copy2(icon_src, icon_dst)
                    shutil.copy2(icon_src, os.path.expanduser("~/.local/share/icons/jellyfin-control.png"))

                # 2. Determina l'eseguibile (AppImage o script Python)
                appimage_env = os.environ.get("APPIMAGE")
                if appimage_env and os.path.exists(appimage_env):
                    exec_cmd = f'"{appimage_env}"'
                else:
                    script_path = os.path.abspath(__file__)
                    exec_cmd = f'python3 "{script_path}"'

                # 3. Scrivi il file .desktop conforme allo standard XDG
                content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Jellyfin Control Center
GenericName=Jellyfin Media Server Manager
Comment=Gestione, Monitoraggio Risorse, Installazione e Backup di Jellyfin Media Server
Exec={exec_cmd}
Icon=jellyfin-control
Terminal=false
Categories=AudioVideo;Video;Network;Settings;
StartupWMClass=jellyfin-control-center
StartupNotify=true
"""
                with open(desktop_file, "w", encoding="utf-8") as f:
                    f.write(content)
                os.chmod(desktop_file, 0o755)

                subprocess.run(["update-desktop-database", apps_dir], capture_output=True)
                self.update_system_integration_button()
                QMessageBox.information(
                    self,
                    t("system_integration_title", self.current_lang),
                    t("system_integration_installed_msg", self.current_lang)
                )
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Impossibile registrare il collegamento: {e}")


    # -------------------------------------------------------------
    # METODI E LOGICA PER IL PLUGIN INTRO SKIPPER
    # -------------------------------------------------------------
    def get_intro_skipper_task_info(self):
        """Interroga l'API REST di Jellyfin per recuperare i dettagli del task IntroSkipperDetectSegmentsTask."""
        url = "http://localhost:8096/ScheduledTasks"
        headers = {"Authorization": f'MediaBrowser Token="{self.api_key}"'}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                tasks = json.loads(resp.read().decode())
                for t in tasks:
                    if t.get("Key") == "IntroSkipperDetectSegmentsTask" or (
                        "intro skipper" in t.get("Category", "").lower() and "detect" in t.get("Name", "").lower()
                    ):
                        return t
        except Exception:
            pass
        return None

    def get_intro_skipper_task_id(self):
        """Restituisce l'ID univoco del task per la gestione di Start/Stop."""
        t = self.get_intro_skipper_task_info()
        if t and "Id" in t:
            return t["Id"]
        return "eed9a58097ab2f196265820308ec2e1c"

    def poll_plugin_status(self):
        """
        Esegue il polling non invasivo dello stato di installazione del plugin,
        dello stato del task schedulato, dei conteggi SQLite e delle righe di log recenti.
        """
        # 1. Verifica installazione cartella plugin
        installed = False
        version_str = "Sconosciuta"
        plugins_parent = os.path.join(JELLYFIN_DIR, "config/plugins")
        if os.path.exists(plugins_parent):
            for entry in os.listdir(plugins_parent):
                if entry.startswith("Intro Skipper"):
                    installed = True
                    meta_path = os.path.join(plugins_parent, entry, "meta.json")
                    if os.path.exists(meta_path):
                        try:
                            with open(meta_path, "r", encoding="utf-8") as mf:
                                meta = json.load(mf)
                                version_str = meta.get("version", entry)
                        except Exception:
                            version_str = entry
                    else:
                        version_str = entry
                    break

        if installed:
            self.lbl_plugin_badge.setText(f"● INSTALLATO (v{version_str} - Attivo)")
            self.lbl_plugin_badge.setStyleSheet("background-color: #064e3b; color: #34d399; border: 1px solid #059669; border-radius: 12px; padding: 4px 12px; font-weight: bold; font-size: 12px;")
            self.btn_install_plugin.setText("🔄  Reinstalla / Aggiorna")
            self.btn_uninstall_plugin.setEnabled(True)
        else:
            self.lbl_plugin_badge.setText("● NON INSTALLATO")
            self.lbl_plugin_badge.setStyleSheet("background-color: #451a1a; color: #f87171; border: 1px solid #dc2626; border-radius: 12px; padding: 4px 12px; font-weight: bold; font-size: 12px;")
            self.btn_install_plugin.setText("📥  Installa Plugin")
            self.btn_uninstall_plugin.setEnabled(False)
            self.btn_start_analysis.setEnabled(False)
            self.btn_stop_analysis.setEnabled(False)

        # 2. Verifica stato del task schedulato via API
        task_info = self.get_intro_skipper_task_info()
        task_state = "Idle"
        task_progress = None
        if task_info:
            task_state = task_info.get("State", "Idle")
            task_progress = task_info.get("CurrentProgressPercentage")

        is_running = (task_state == "Running")
        if is_running:
            self.lbl_plugin_task_badge.setText("▶️  IN ESECUZIONE...")
            self.lbl_plugin_task_badge.setStyleSheet("background-color: #1e3a5f; color: #38bdf8; border: 1px solid #0284c7; border-radius: 12px; padding: 4px 12px; font-weight: bold; font-size: 12px;")
            if installed:
                self.btn_start_analysis.setEnabled(False)
                self.btn_stop_analysis.setEnabled(True)
        else:
            self.lbl_plugin_task_badge.setText("⏹️  INATTIVO / PRONTO")
            self.lbl_plugin_task_badge.setStyleSheet("background-color: #1f2937; color: #9ca3af; border: 1px solid #374151; border-radius: 12px; padding: 4px 12px; font-weight: bold; font-size: 12px;")
            if installed:
                self.btn_start_analysis.setEnabled(True)
                self.btn_stop_analysis.setEnabled(False)

        # 3. Interrogazione statistiche database SQLite (Safe Read-Only)
        analyzed_items = 0
        segments_found = 0
        total_episodes = 0
        total_movies = 0

        intro_db = os.path.join(JELLYFIN_DIR, "config/data/introskipper/introskipper-v2.db")
        jf_db = os.path.join(JELLYFIN_DIR, "config/data/jellyfin.db")

        if os.path.exists(intro_db):
            try:
                conn = sqlite3.connect(f"file:{intro_db}?mode=ro", uri=True, timeout=1.5)
                c = conn.cursor()
                c.execute("SELECT count(DISTINCT ItemId) FROM AnalyzedItems")
                analyzed_items = c.fetchone()[0]
                c.execute("SELECT count(*) FROM Segments")
                segments_found = c.fetchone()[0]
                conn.close()
            except Exception:
                pass

        if os.path.exists(jf_db):
            try:
                conn = sqlite3.connect(f"file:{jf_db}?mode=ro", uri=True, timeout=1.5)
                c = conn.cursor()
                c.execute("SELECT count(*) FROM BaseItems WHERE type = 'MediaBrowser.Controller.Entities.TV.Episode'")
                total_episodes = c.fetchone()[0]
                c.execute("SELECT count(*) FROM BaseItems WHERE type = 'MediaBrowser.Controller.Entities.Movies.Movie'")
                total_movies = c.fetchone()[0]
                conn.close()
            except Exception:
                pass

        total_media = total_episodes + total_movies
        remaining_media = max(0, total_media - analyzed_items)

        tot_s = f"{total_media:,}".replace(",", ".")
        ep_s = f"{total_episodes:,}".replace(",", ".")
        mv_s = f"{total_movies:,}".replace(",", ".")
        self.lbl_plugin_total_media.setText(f"{tot_s} ({ep_s} ep, {mv_s} film)")
        self.lbl_plugin_analyzed_media.setText(f"{analyzed_items:,} file".replace(",", "."))
        self.lbl_plugin_remaining_media.setText(f"{remaining_media:,} file".replace(",", "."))
        self.lbl_plugin_segments_detected.setText(f"{segments_found:,} rilevati".replace(",", "."))

        # Calcolo avanzamento percentuale
        if task_progress is not None and is_running:
            pct_val = float(task_progress)
        elif total_media > 0:
            pct_val = (analyzed_items / total_media) * 100.0
        else:
            pct_val = 0.0

        self.bar_plugin_progress.setValue(int(pct_val))
        self.lbl_plugin_progress_pct.setText(f"{pct_val:.1f}%")

        # 4. Aggiornamento log live da disco
        recent_logs = get_recent_plugin_logs(200)
        if recent_logs:
            full_log_text = "\n".join(recent_logs)
            if full_log_text != self.last_plugin_log_text:
                self.last_plugin_log_text = full_log_text
                self.txt_plugin_log.setPlainText(full_log_text)
                if self.chk_plugin_autoscroll.isChecked():
                    self.txt_plugin_log.verticalScrollBar().setValue(
                        self.txt_plugin_log.verticalScrollBar().maximum()
                    )

        # -------------------------------------------------------------
        # TELEMETRIA E STATO MODULO TRICKPLAY
        # -------------------------------------------------------------
        tp_installed = self.is_trickplay_installed()
        if tp_installed:
            self.lbl_tp_badge.setText(t("badge_installed", self.current_lang) + " / ATTIVO")
            self.lbl_tp_badge.setStyleSheet("background-color: #064e3b; color: #34d399; border: 1px solid #059669; border-radius: 12px; padding: 3px 10px; font-weight: bold; font-size: 11px;")
            self.btn_install_tp.setText("🔄  Reinstalla / Aggiorna")
            self.btn_uninstall_tp.setEnabled(True)
        else:
            self.lbl_tp_badge.setText(t("badge_not_installed", self.current_lang))
            self.lbl_tp_badge.setStyleSheet("background-color: #451a1a; color: #f87171; border: 1px solid #dc2626; border-radius: 12px; padding: 3px 10px; font-weight: bold; font-size: 11px;")
            self.btn_install_tp.setText(t("btn_install_plugin", self.current_lang))
            self.btn_uninstall_tp.setEnabled(False)

        tp_task = self.get_trickplay_task_info()
        tp_state = tp_task.get("State", "Idle") if tp_task else "Idle"
        tp_progress = tp_task.get("CurrentProgressPercentage") if tp_task else None
        tp_is_running = (tp_state == "Running")

        if tp_is_running:
            self.lbl_tp_task_badge.setText(t("badge_task_running", self.current_lang))
            self.lbl_tp_task_badge.setStyleSheet("background-color: #1e3a5f; color: #38bdf8; border: 1px solid #0284c7; border-radius: 12px; padding: 3px 10px; font-weight: bold; font-size: 11px;")
            self.btn_start_tp.setEnabled(False)
            self.btn_stop_tp.setEnabled(True)
        else:
            self.lbl_tp_task_badge.setText(t("badge_task_idle", self.current_lang))
            self.lbl_tp_task_badge.setStyleSheet("background-color: #1f2937; color: #9ca3af; border: 1px solid #374151; border-radius: 12px; padding: 3px 10px; font-weight: bold; font-size: 11px;")
            self.btn_start_tp.setEnabled(True)
            self.btn_stop_tp.setEnabled(False)

        # Conteggi Trickplay nel DB
        tp_count = 0
        if os.path.exists(jf_db):
            try:
                conn_tp = sqlite3.connect(f"file:{jf_db}?mode=ro", uri=True, timeout=1.5)
                c_tp = conn_tp.cursor()
                c_tp.execute("SELECT count(*) FROM TrickplayInfos")
                tp_count = c_tp.fetchone()[0]
                conn_tp.close()
            except Exception:
                pass

        tp_remaining = max(0, total_media - tp_count)
        self.lbl_tp_generated.setText(f"{tp_count:,}".replace(",", "."))
        self.lbl_tp_total.setText(f"{total_media:,}".replace(",", "."))
        self.lbl_tp_remaining.setText(f"{tp_remaining:,}".replace(",", "."))

        # Calcolo dimensione cartella dati Trickplay su disco
        tp_size_bytes = 0
        if os.path.exists(TRICKPLAY_DATA_DIR):
            try:
                for root_tp, _, files_tp in os.walk(TRICKPLAY_DATA_DIR):
                    for f_tp in files_tp:
                        tp_size_bytes += os.path.getsize(os.path.join(root_tp, f_tp))
            except Exception:
                pass
        self.lbl_tp_size.setText(f"{tp_size_bytes / (1024 * 1024):.1f} MB")

        # Barra di progresso Trickplay
        if tp_progress is not None and tp_is_running:
            tp_pct = float(tp_progress)
        elif total_media > 0:
            tp_pct = (tp_count / total_media) * 100.0
        else:
            tp_pct = 0.0
        self.bar_tp_progress.setValue(int(tp_pct))
        self.lbl_tp_progress_pct.setText(f"{tp_pct:.1f}%")

        # Log live Trickplay
        tp_logs = get_recent_trickplay_logs(150)
        if tp_logs:
            tp_text = "\n".join(tp_logs)
            if tp_text != self.last_tp_log_text:
                self.last_tp_log_text = tp_text
                self.txt_tp_log.setPlainText(tp_text)
                if self.chk_tp_autoscroll.isChecked():
                    self.txt_tp_log.verticalScrollBar().setValue(
                        self.txt_tp_log.verticalScrollBar().maximum()
                    )


    def start_intro_skipper_analysis(self):
        """Avvia l'attivita di analisi dei media di Intro Skipper tramite API Jellyfin."""
        task_id = self.get_intro_skipper_task_id()
        if not task_id:
            QMessageBox.warning(self, "Attenzione", "Impossibile individuare il task di analisi di Intro Skipper su Jellyfin.\nVerifica che il plugin sia installato e che Jellyfin sia attivo.")
            return

        url = f"http://localhost:8096/ScheduledTasks/Running/{task_id}"
        headers = {"Authorization": f'MediaBrowser Token="{self.api_key}"'}
        req = urllib.request.Request(url, data=b"", headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status in (200, 204):
                    self.lbl_plugin_task_badge.setText("▶️  IN AVVIO...")
                    self.lbl_plugin_task_badge.setStyleSheet("background-color: #1e3a5f; color: #38bdf8; border: 1px solid #0284c7; border-radius: 12px; padding: 4px 12px; font-weight: bold;")
                    self.btn_start_analysis.setEnabled(False)
                    self.btn_stop_analysis.setEnabled(True)
                    QTimer.singleShot(1500, self.poll_plugin_status)
        except Exception as e:
            QMessageBox.critical(self, "Errore Avvio Analisi", f"Impossibile avviare il task di analisi: {e}")

    def stop_intro_skipper_analysis(self):
        """Arresta l'attivita di analisi dei media in corso tramite API Jellyfin."""
        task_id = self.get_intro_skipper_task_id()
        if not task_id:
            return

        url = f"http://localhost:8096/ScheduledTasks/Running/{task_id}"
        headers = {"Authorization": f'MediaBrowser Token="{self.api_key}"'}
        req = urllib.request.Request(url, headers=headers, method="DELETE")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status in (200, 204):
                    self.lbl_plugin_task_badge.setText("⏹️  ARRESTO IN CORSO...")
                    self.lbl_plugin_task_badge.setStyleSheet("background-color: #451a1a; color: #f87171; border: 1px solid #dc2626; border-radius: 12px; padding: 4px 12px; font-weight: bold;")
                    self.btn_stop_analysis.setEnabled(False)
                    QTimer.singleShot(1500, self.poll_plugin_status)
        except Exception as e:
            QMessageBox.critical(self, "Errore Arresto Analisi", f"Impossibile arrestare il task: {e}")

    def install_intro_skipper_dialog(self):
        """Dialogo modale per consentire la scelta tra installazione online automatica o da file .zip locale."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Installa Plugin Intro Skipper")
        dialog.setMinimumWidth(480)
        d_layout = QVBoxLayout(dialog)
        d_layout.setSpacing(12)

        lbl_desc = QLabel(
            "Scegli la modalita di installazione del plugin Intro Skipper:\n"
            "I file verranno collocati in config/plugins/ ed il container Jellyfin verra riavviato."
        )
        lbl_desc.setStyleSheet("color: #cfd3dc; font-size: 12px;")
        d_layout.addWidget(lbl_desc)

        btn_online = QPushButton("🌐  Scarica Automaticamente Online (GitHub v12.0.4.0)")
        btn_online.setObjectName("btnStart")
        btn_online.setFixedHeight(36)

        btn_local = QPushButton("📁  Carica Archivio Locale (.zip)")
        btn_local.setObjectName("btnBrowser")
        btn_local.setFixedHeight(36)

        btn_cancel = QPushButton("Annulla")
        btn_cancel.setObjectName("btnMini")

        d_layout.addWidget(btn_online)
        d_layout.addWidget(btn_local)
        d_layout.addWidget(btn_cancel)

        chosen = [None, ""]

        def choose_online():
            chosen[0] = "online"
            dialog.accept()

        def choose_local():
            f, _ = QFileDialog.getOpenFileName(
                self, "Seleziona archivio Intro Skipper .zip", os.path.expanduser("~/Scaricati"), "Archivi Zip (*.zip)"
            )
            if f:
                chosen[0] = "local"
                chosen[1] = f
                dialog.accept()

        btn_online.clicked.connect(choose_online)
        btn_local.clicked.connect(choose_local)
        btn_cancel.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted and chosen[0]:
            self.execute_plugin_install(chosen[0], chosen[1])

    def execute_plugin_install(self, mode, local_path):
        """Avvia il worker asincrono per l'installazione del plugin."""
        self.btn_install_plugin.setEnabled(False)
        self.btn_uninstall_plugin.setEnabled(False)
        self.lbl_plugin_badge.setText("● INSTALLAZIONE IN CORSO...")
        self.lbl_plugin_badge.setStyleSheet("background-color: #1e3a5f; color: #38bdf8; border: 1px solid #0284c7; border-radius: 12px; padding: 4px 12px; font-weight: bold;")

        self.plugin_install_worker = PluginInstallWorker(mode=mode, local_zip=local_path)
        self.plugin_install_worker.progress.connect(self.on_plugin_install_progress)
        self.plugin_install_worker.log.connect(lambda msg: self.txt_plugin_log.appendPlainText(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [INSTALLAZIONE] {msg}"))
        self.plugin_install_worker.finished.connect(self.on_plugin_install_finished)
        self.plugin_install_worker.start()

    def on_plugin_install_progress(self, pct, msg):
        self.bar_plugin_progress.setValue(pct)
        self.lbl_plugin_progress_pct.setText(f"{pct}%")
        self.lbl_plugin_prog_desc.setText(f"Installazione: {msg}")

    def on_plugin_install_finished(self, success, msg):
        self.btn_install_plugin.setEnabled(True)
        self.btn_uninstall_plugin.setEnabled(True)
        self.lbl_plugin_prog_desc.setText("Progresso Complessivo:")
        self.poll_plugin_status()
        if success:
            QMessageBox.information(self, "Plugin Installato", msg)
        else:
            QMessageBox.warning(self, "Installazione Fallita", msg)

    def uninstall_intro_skipper_dialog(self):
        """Dialogo modale per rimuovere il plugin con scelta se preservare il database delle impronte."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Disinstalla Plugin Intro Skipper")
        msg_box.setText("Sei sicuro di voler rimuovere il plugin Intro Skipper?")
        msg_box.setInformativeText(
            "Puoi scegliere se mantenere il database delle impronte audio (introskipper-v2.db)\n"
            "per non perdere le ore di calcolo gia effettuate in caso di reinstallazione,\n"
            "oppure eliminare completamente sia il plugin che tutti i dati."
        )
        msg_box.setIcon(QMessageBox.Icon.Question)

        btn_keep = msg_box.addButton("Rimuovi Plugin (Mantieni Dati)", QMessageBox.ButtonRole.YesRole)
        btn_purge = msg_box.addButton("Rimuovi Tutto (Incluso Database)", QMessageBox.ButtonRole.DestructiveRole)
        btn_cancel = msg_box.addButton("Annulla", QMessageBox.ButtonRole.RejectRole)

        msg_box.exec()
        clicked = msg_box.clickedButton()

        if clicked == btn_keep:
            self.execute_plugin_uninstall(remove_database=False)
        elif clicked == btn_purge:
            self.execute_plugin_uninstall(remove_database=True)

    def execute_plugin_uninstall(self, remove_database):
        """Avvia il worker asincrono per la rimozione del plugin."""
        self.btn_install_plugin.setEnabled(False)
        self.btn_uninstall_plugin.setEnabled(False)
        self.lbl_plugin_badge.setText("● RIMOZIONE IN CORSO...")
        self.lbl_plugin_badge.setStyleSheet("background-color: #451a1a; color: #f87171; border: 1px solid #dc2626; border-radius: 12px; padding: 4px 12px; font-weight: bold;")

        self.plugin_uninstall_worker = PluginUninstallWorker(remove_database=remove_database)
        self.plugin_uninstall_worker.progress.connect(self.on_plugin_uninstall_progress)
        self.plugin_uninstall_worker.log.connect(lambda msg: self.txt_plugin_log.appendPlainText(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [DISINSTALLAZIONE] {msg}"))
        self.plugin_uninstall_worker.finished.connect(self.on_plugin_uninstall_finished)
        self.plugin_uninstall_worker.start()

    def on_plugin_uninstall_progress(self, pct, msg):
        self.bar_plugin_progress.setValue(pct)
        self.lbl_plugin_progress_pct.setText(f"{pct}%")
        self.lbl_plugin_prog_desc.setText(f"Rimozione: {msg}")

    def on_plugin_uninstall_finished(self, success, msg):
        self.btn_install_plugin.setEnabled(True)
        self.btn_uninstall_plugin.setEnabled(True)
        self.lbl_plugin_prog_desc.setText("Progresso Complessivo:")
        self.poll_plugin_status()
        if success:
            QMessageBox.information(self, "Plugin Rimosso", msg)
        else:
            QMessageBox.warning(self, "Rimozione Fallita", msg)


    # -------------------------------------------------------------
    # METODI E LOGICA PER IL PLUGIN TRICKPLAY
    # -------------------------------------------------------------
    def is_trickplay_installed(self):
        """Verifica se il modulo/plugin Trickplay e presente nel server Jellyfin."""
        plugins_parent = os.path.join(JELLYFIN_DIR, "config/plugins")
        if os.path.exists(plugins_parent):
            for entry in os.listdir(plugins_parent):
                if "trickplay" in entry.lower() or "preview" in entry.lower():
                    return True
        task_info = self.get_trickplay_task_info()
        return task_info is not None

    def get_trickplay_task_info(self):
        """Interroga l'API REST di Jellyfin per recuperare i dettagli del task RefreshTrickplayImages."""
        url = "http://localhost:8096/ScheduledTasks"
        headers = {"Authorization": f'MediaBrowser Token="{self.api_key}"'}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                tasks = json.loads(resp.read().decode())
                for t in tasks:
                    if t.get("Key") == "RefreshTrickplayImages" or "trickplay" in t.get("Name", "").lower():
                        return t
        except Exception:
            pass
        return None

    def get_trickplay_task_id(self):
        """Restituisce l'ID univoco del task per la gestione di Start/Stop."""
        t = self.get_trickplay_task_info()
        if t and "Id" in t:
            return t["Id"]
        return "64f5f44cd30dc273cb9890205473bbcc"

    def open_trickplay_web_config(self):
        """Apre il pannello web di configurazione di Trickplay nel browser predefinito."""
        QDesktopServices.openUrl(QUrl("http://localhost:8096/web/#/trickplay"))

    def start_trickplay_analysis(self):
        """Avvia la generazione di immagini Trickplay per la libreria."""
        task_id = self.get_trickplay_task_id()
        url = f"http://localhost:8096/ScheduledTasks/Running/{task_id}"
        headers = {"Authorization": f'MediaBrowser Token="{self.api_key}"'}
        req = urllib.request.Request(url, data=b"", headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status in (200, 204):
                    self.lbl_tp_task_badge.setText("▶️  IN AVVIO...")
                    self.lbl_tp_task_badge.setStyleSheet("background-color: #1e3a5f; color: #38bdf8; border: 1px solid #0284c7; border-radius: 12px; padding: 3px 10px; font-weight: bold;")
                    self.btn_start_tp.setEnabled(False)
                    self.btn_stop_tp.setEnabled(True)
                    QTimer.singleShot(1500, self.poll_plugin_status)
        except Exception as e:
            QMessageBox.critical(self, "Errore Avvio Trickplay", f"Impossibile avviare il task: {e}")

    def stop_trickplay_analysis(self):
        """Arresta la generazione di immagini Trickplay in corso."""
        task_id = self.get_trickplay_task_id()
        url = f"http://localhost:8096/ScheduledTasks/Running/{task_id}"
        headers = {"Authorization": f'MediaBrowser Token="{self.api_key}"'}
        req = urllib.request.Request(url, headers=headers, method="DELETE")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status in (200, 204):
                    self.lbl_tp_task_badge.setText("⏹️  ARRESTO IN CORSO...")
                    self.lbl_tp_task_badge.setStyleSheet("background-color: #451a1a; color: #f87171; border: 1px solid #dc2626; border-radius: 12px; padding: 3px 10px; font-weight: bold;")
                    self.btn_stop_tp.setEnabled(False)
                    QTimer.singleShot(1500, self.poll_plugin_status)
        except Exception as e:
            QMessageBox.critical(self, "Errore Arresto Trickplay", f"Impossibile arrestare il task: {e}")

    def reset_trickplay_library(self):
        """
        Resetta e ricostruisce da zero l'intera libreria Trickplay:
        elimina i file parziali o obsoleti, azzera i record nel DB e riavvia la generazione.
        """
        res = QMessageBox.warning(
            self,
            "Reset Libreria Trickplay",
            "Attenzione: questa operazione cancellera tutte le miniature Trickplay esistenti su disco\n"
            "e riavviera una generazione pulita da zero per l'intera libreria multimediale.\n\n"
            "Desideri continuare?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if res != QMessageBox.StandardButton.Yes:
            return

        self.stop_trickplay_analysis()

        if os.path.exists(TRICKPLAY_DATA_DIR):
            try:
                for item in os.listdir(TRICKPLAY_DATA_DIR):
                    p = os.path.join(TRICKPLAY_DATA_DIR, item)
                    if os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                    else:
                        os.remove(p)
            except Exception:
                pass

        jf_db = os.path.join(JELLYFIN_DIR, "config/data/jellyfin.db")
        if os.path.exists(jf_db):
            try:
                conn = sqlite3.connect(jf_db, timeout=2.0)
                conn.execute("DELETE FROM TrickplayInfos;")
                conn.commit()
                conn.close()
            except Exception:
                pass

        QTimer.singleShot(1000, self.start_trickplay_analysis)
        QMessageBox.information(
            self,
            "Ricostruzione Avviata",
            "I dati Trickplay sono stati azzerati con successo.\nLa nuova generazione delle miniature e stata avviata!"
        )

    def install_trickplay_dialog(self):
        """
        Verifica preventivamente se Trickplay e gia installato prima di procedere,
        e fornisce la scelta tra configurazione automatica o archivio zip locale.
        """
        if self.is_trickplay_installed():
            res = QMessageBox.question(
                self,
                "Modulo Trickplay Già Presente",
                "Il modulo o plugin Trickplay risulta già attivo e configurato nel server Jellyfin!\n\n"
                "Vuoi procedere comunque con una reinstallazione/sovrascrittura?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if res != QMessageBox.StandardButton.Yes:
                return

        dialog = QDialog(self)
        dialog.setWindowTitle("Installa / Configura Modulo Trickplay")
        dialog.setMinimumWidth(460)
        d_layout = QVBoxLayout(dialog)
        d_layout.setSpacing(12)

        lbl = QLabel("Scegli la modalità per installare o aggiornare il componente Trickplay:")
        lbl.setStyleSheet("color: #cfd3dc; font-size: 12px;")
        d_layout.addWidget(lbl)

        btn_auto = QPushButton("⚡  Configura / Abilita Modulo Standalone")
        btn_auto.setObjectName("btnStart")
        btn_auto.setFixedHeight(34)

        btn_zip = QPushButton("📁  Carica Archivio Locale (.zip)")
        btn_zip.setObjectName("btnBrowser")
        btn_zip.setFixedHeight(34)

        btn_cancel = QPushButton("Annulla")
        btn_cancel.setObjectName("btnMini")

        d_layout.addWidget(btn_auto)
        d_layout.addWidget(btn_zip)
        d_layout.addWidget(btn_cancel)

        chosen = [None, ""]

        def choose_auto():
            chosen[0] = "online"
            dialog.accept()

        def choose_zip():
            f, _ = QFileDialog.getOpenFileName(
                self, "Seleziona archivio Trickplay .zip", os.path.expanduser("~/Scaricati"), "Archivi Zip (*.zip)"
            )
            if f:
                chosen[0] = "local"
                chosen[1] = f
                dialog.accept()

        btn_auto.clicked.connect(choose_auto)
        btn_zip.clicked.connect(choose_zip)
        btn_cancel.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted and chosen[0]:
            self.execute_trickplay_install(chosen[0], chosen[1])

    def execute_trickplay_install(self, mode, zip_path):
        """Avvia il worker asincrono per l'installazione di Trickplay."""
        self.btn_install_tp.setEnabled(False)
        self.btn_uninstall_tp.setEnabled(False)
        self.lbl_tp_badge.setText("● INSTALLAZIONE...")
        self.tp_install_worker = TrickplayInstallWorker(mode=mode, local_zip=zip_path)
        self.tp_install_worker.finished.connect(self.on_trickplay_install_finished)
        self.tp_install_worker.start()

    def on_trickplay_install_finished(self, success, msg):
        self.btn_install_tp.setEnabled(True)
        self.btn_uninstall_tp.setEnabled(True)
        self.poll_plugin_status()
        if success:
            QMessageBox.information(self, "Operazione Completata", msg)
        else:
            QMessageBox.warning(self, "Attenzione", msg)

    def uninstall_trickplay_dialog(self):
        """Dialogo modale per rimuovere il plugin Trickplay con opzione di pulizia dati."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Rimuovi Modulo Trickplay")
        msg_box.setText("Sei sicuro di voler rimuovere il modulo Trickplay?")
        msg_box.setInformativeText(
            "Puoi scegliere se rimuovere solo il modulo mantenendo la cartella delle miniature già generate,\n"
            "oppure eliminare anche tutti i file delle miniature su disco."
        )
        msg_box.setIcon(QMessageBox.Icon.Question)

        btn_keep = msg_box.addButton("Rimuovi Modulo (Mantieni Miniature)", QMessageBox.ButtonRole.YesRole)
        btn_purge = msg_box.addButton("Rimuovi Tutto (Cancella Miniature)", QMessageBox.ButtonRole.DestructiveRole)
        btn_cancel = msg_box.addButton("Annulla", QMessageBox.ButtonRole.RejectRole)

        msg_box.exec()
        clicked = msg_box.clickedButton()

        if clicked == btn_keep:
            self.execute_trickplay_uninstall(purge_data=False)
        elif clicked == btn_purge:
            self.execute_trickplay_uninstall(purge_data=True)

    def execute_trickplay_uninstall(self, purge_data):
        """Avvia il worker asincrono per la disinstallazione di Trickplay."""
        self.btn_install_tp.setEnabled(False)
        self.btn_uninstall_tp.setEnabled(False)
        self.lbl_tp_badge.setText("● RIMOZIONE...")
        self.tp_uninstall_worker = TrickplayUninstallWorker(purge_data=purge_data)
        self.tp_uninstall_worker.finished.connect(self.on_trickplay_uninstall_finished)
        self.tp_uninstall_worker.start()

    def on_trickplay_uninstall_finished(self, success, msg):
        self.btn_install_tp.setEnabled(True)
        self.btn_uninstall_tp.setEnabled(True)
        self.poll_plugin_status()
        if success:
            QMessageBox.information(self, "Operazione Completata", msg)
        else:
            QMessageBox.warning(self, "Attenzione", msg)

    def apply_styles(self):
        """Definisce il tema visivo scuro personalizzato dell'applicazione."""
        style = """
        QMainWindow {
            background-color: #12141c;
        }
        #headerFrame {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a1c29, stop:1 #242238);
            border-radius: 12px;
            border: 1px solid #2e3247;
        }
        #appTitle {
            font-size: 20px;
            font-weight: bold;
            color: #ffffff;
        }
        #appSubtitle {
            font-size: 12px;
            color: #9ba1b0;
        }
        #cardFrame {
            background-color: #181b26;
            border-radius: 12px;
            border: 1px solid #282d3f;
        }
        #mainTabs::pane {
            border: 1px solid #282d3f;
            background: #141620;
            border-radius: 10px;
            top: -1px;
        }
        QTabBar::tab {
            background: #1c202d;
            color: #9ba1b0;
            padding: 9px 15px;
            margin-right: 3px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            font-weight: bold;
            font-size: 12px;
        }
        QTabBar::tab:selected {
            background: #24293a;
            color: #00d2ff;
            border-bottom: 2px solid #00d2ff;
        }
        QTabBar::tab:hover:!selected {
            background: #222636;
            color: #ffffff;
        }
        #sessionsTable {
            background-color: #161823;
            border: 1px solid #282d3f;
            border-radius: 8px;
            gridline-color: #232738;
            color: #cfd3dc;
            font-size: 12px;
        }
        #sessionsTable::item {
            padding: 8px;
        }
        #sessionsTable::item:selected {
            background-color: #262c42;
            color: #ffffff;
        }
        QHeaderView::section {
            background-color: #1e2230;
            color: #00d2ff;
            padding: 8px;
            font-weight: bold;
            border: 1px solid #282d3f;
        }
        #terminalViewer, #logViewer {
            background-color: #0d0f17;
            border: 1px solid #232738;
            border-radius: 8px;
            color: #38bdf8;
            font-family: monospace;
            font-size: 11px;
        }
        #statusBadgeRunning {
            background-color: #064e3b;
            color: #34d399;
            border: 1px solid #059669;
            border-radius: 14px;
            padding: 4px 14px;
            font-weight: bold;
            font-size: 13px;
        }
        #statusBadgeStopped {
            background-color: #451a1a;
            color: #f87171;
            border: 1px solid #dc2626;
            border-radius: 14px;
            padding: 4px 14px;
            font-weight: bold;
            font-size: 13px;
        }
        #statusBadgeWait {
            background-color: #452b12;
            color: #fbbf24;
            border: 1px solid #d97706;
            border-radius: 14px;
            padding: 4px 14px;
            font-weight: bold;
            font-size: 13px;
        }
        #statusBadgeUnknown {
            background-color: #272a38;
            color: #9ba1b0;
            border: 1px solid #3c4155;
            border-radius: 14px;
            padding: 4px 14px;
            font-weight: bold;
            font-size: 13px;
        }
        QPushButton {
            border-radius: 8px;
            font-weight: bold;
            font-size: 13px;
            padding: 6px 12px;
        }
        #btnStart {
            background-color: #059669;
            color: #ffffff;
            border: 1px solid #10b981;
        }
        #btnStart:hover {
            background-color: #10b981;
        }
        #btnStart:disabled {
            background-color: #1b382b;
            color: #527967;
            border: 1px solid #234d3a;
        }
        #btnStop {
            background-color: #dc2626;
            color: #ffffff;
            border: 1px solid #ef4444;
        }
        #btnStop:hover {
            background-color: #ef4444;
        }
        #btnStop:disabled {
            background-color: #3b1e1e;
            color: #7a4848;
            border: 1px solid #522727;
        }
        #btnRestart {
            background-color: #4f46e5;
            color: #ffffff;
            border: 1px solid #6366f1;
        }
        #btnRestart:hover {
            background-color: #6366f1;
        }
        #btnRestart:disabled {
            background-color: #262447;
            color: #5a5682;
            border: 1px solid #363363;
        }
        #btnBrowser {
            background-color: #0284c7;
            color: #ffffff;
            border: 1px solid #38bdf8;
        }
        #btnBrowser:hover {
            background-color: #0369a1;
        }
        #btnBrowser:disabled {
            background-color: #162f3d;
            color: #486a7d;
            border: 1px solid #224354;
        }
        #btnFolder {
            background-color: #232738;
            color: #e2e8f0;
            border: 1px solid #3b4259;
        }
        #btnFolder:hover {
            background-color: #32384f;
        }
        #btnMini {
            background-color: #232738;
            color: #cfd3dc;
            border: 1px solid #373d52;
            border-radius: 6px;
            font-size: 11px;
            padding: 4px 10px;
        }
        #btnMini:hover {
            background-color: #32384f;
            color: #ffffff;
        }
        #customCheck, #customCheckLarge {
            color: #cfd3dc;
            font-size: 12px;
            font-weight: bold;
        }
        #customCheckLarge {
            font-size: 13px;
            color: #00d2ff;
        }
        QProgressBar {
            background-color: #1e2230;
            border-radius: 4px;
        }
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00d2ff, stop:1 #b855d4);
            border-radius: 4px;
        }
        """
        self.setStyleSheet(style)


# ==================================================================================================
# PUNTO DI INGRESSO PRINCIPALE (MAIN ENTRY POINT)
# ==================================================================================================
def main():
    """
    Punto di ingresso principale dell'applicazione Qt con gestione a istanza singola:
    se un'istanza e gia in esecuzione, invia un segnale per risvegliarla ed esce pulitamente.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("jellyfin-control-center")
    app.setApplicationDisplayName("Jellyfin Control Center")
    app.setDesktopFileName("jellyfin-control-center")
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))

    # Controllo istanza singola a runtime tramite QLocalSocket
    test_socket = QLocalSocket()
    test_socket.connectToServer(SINGLE_INSTANCE_SOCKET_NAME)
    if test_socket.waitForConnected(500):
        test_socket.write(b"ACTIVATE\n")
        test_socket.waitForBytesWritten(1000)
        test_socket.disconnectFromServer()
        print("Jellyfin Control Center: un'istanza e gia in esecuzione. Finestra portata in primo piano.")
        sys.exit(0)

    # Nessuna istanza attiva: rimuovi eventuale socket obsoleto e avvia il server locale
    QLocalServer.removeServer(SINGLE_INSTANCE_SOCKET_NAME)
    instance_server = QLocalServer()
    instance_server.listen(SINGLE_INSTANCE_SOCKET_NAME)

    window = JellyfinManager(single_instance_server=instance_server)
    window.show()
    exit_code = app.exec()

    # Pulizia socket alla chiusura
    instance_server.close()
    QLocalServer.removeServer(SINGLE_INSTANCE_SOCKET_NAME)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
