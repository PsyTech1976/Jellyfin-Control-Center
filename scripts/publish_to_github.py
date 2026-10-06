#!/usr/bin/env python3
"""
Script di pubblicazione automatizzata su GitHub per Jellyfin Control Center.
Gestisce l'autenticazione browser con codice monouso, la creazione del repository,
il push dei sorgenti e la pubblicazione della release con l'AppImage v2.3.0.
"""

import pty
import os
import sys
import select
import time
import re
import subprocess
import json

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS_FILE = os.path.join(PROJECT_DIR, ".github_status.json")
APPIMAGE_PATH = os.path.join(PROJECT_DIR, "dist", "Jellyfin_Control_Center-x86_64.AppImage")

def strip_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

def write_status(data):
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[STATUS] {data.get('status')}: {data.get('message', '')}", flush=True)

def is_already_logged_in():
    res = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    return res.returncode == 0

def authenticate_via_browser():
    if is_already_logged_in():
        print("Già autenticato su GitHub!", flush=True)
        return True

    print("Avvio procedura di autenticazione GitHub CLI tramite browser...", flush=True)
    master, slave = pty.openpty()
    proc = os.fork()

    if proc == 0:
        os.close(master)
        os.dup2(slave, 0)
        os.dup2(slave, 1)
        os.dup2(slave, 2)
        os.close(slave)
        os.execlp("gh", "gh", "auth", "login", "--hostname", "github.com", "--git-protocol", "https", "--web")

    os.close(slave)
    full_output = b""
    code = None
    browser_opened = False

    write_status({"status": "starting", "message": "Avvio autenticazione..."})

    start_time = time.time()
    while time.time() - start_time < 900:
        r, _, _ = select.select([master], [], [], 0.3)
        if r:
            try:
                data = os.read(master, 1024)
            except OSError:
                break
            if not data:
                break
            full_output += data

            if b"\x1b[6n" in data:
                os.write(master, b"\x1b[1;1R")

            if b"(Y/n)" in data:
                time.sleep(0.1)
                os.write(master, b"Y\r")

            clean_text = strip_ansi(full_output.decode("utf-8", errors="ignore"))

            if not code:
                m = re.search(r"one-time code:\s*([A-Z0-9]{4}-[A-Z0-9]{4})", clean_text, re.IGNORECASE)
                if m:
                    code = m.group(1)
                    print(f"\n=======================================================", flush=True)
                    print(f" CODICE MONOUSO GITHUB: {code}", flush=True)
                    print(f" URL: https://github.com/login/device", flush=True)
                    print(f"=======================================================\n", flush=True)
                    write_status({
                        "status": "waiting_user_code",
                        "code": code,
                        "url": "https://github.com/login/device",
                        "message": f"Inserisci il codice {code} su https://github.com/login/device"
                    })

            if code and not browser_opened and ("press enter" in clean_text.lower() or "in your browser" in clean_text.lower()):
                time.sleep(0.3)
                os.write(master, b"\r")
                browser_opened = True
                subprocess.run(["xdg-open", "https://github.com/login/device"], capture_output=True)

        pid, exit_status = os.waitpid(proc, os.WNOHANG)
        if pid == proc:
            exit_code = os.waitstatus_to_exitcode(exit_status)
            if exit_code == 0:
                print("\nAutenticazione completata con successo!", flush=True)
                write_status({"status": "authenticated", "message": "Autenticazione riuscita!"})
                return True
            else:
                print(f"\nProcesso terminato con codice: {exit_code}", flush=True)
                write_status({"status": "error", "message": f"Errore autenticazione ({exit_code})"})
                return False

    return False

def publish_repo():
    print("Verifica profilo utente GitHub...", flush=True)
    res = subprocess.run(["gh", "api", "user"], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Errore nel recupero utente: {res.stderr}", flush=True)
        return False
    user_data = json.loads(res.stdout)
    username = user_data.get("login")
    name = user_data.get("name") or username
    email = user_data.get("email") or f"{username}@users.noreply.github.com"

    print(f"Autenticato come: {username} ({name} <{email}>)", flush=True)

    # Configura git locale
    subprocess.run(["git", "config", "user.name", name], cwd=PROJECT_DIR)
    subprocess.run(["git", "config", "user.email", email], cwd=PROJECT_DIR)

    # Configura credenziali git per gh
    subprocess.run(["gh", "auth", "setup-git"], cwd=PROJECT_DIR)

    repo_name = "Jellyfin-Control-Center"
    print(f"Verifico se il repository {repo_name} esiste già su GitHub...", flush=True)
    check_repo = subprocess.run(["gh", "repo", "view", f"{username}/{repo_name}"], capture_output=True, text=True)

    if check_repo.returncode == 0:
        print(f"Repository {repo_name} già esistente su GitHub. Configuro remote e push...", flush=True)
        remote_url = f"https://github.com/{username}/{repo_name}.git"
        subprocess.run(["git", "remote", "remove", "origin"], cwd=PROJECT_DIR, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=PROJECT_DIR)
        push_res = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=PROJECT_DIR, capture_output=True, text=True)
        print(push_res.stdout, push_res.stderr, flush=True)
    else:
        print(f"Creazione del repository pubblico {repo_name} su GitHub...", flush=True)
        create_res = subprocess.run([
            "gh", "repo", "create", repo_name,
            "--public",
            "--description", "Jellyfin Control Center - Suite di gestione e monitoraggio per Jellyfin Server su Linux (PyQt6)",
            "--source=.",
            "--remote=origin",
            "--push"
        ], cwd=PROJECT_DIR, capture_output=True, text=True)
        print(create_res.stdout, create_res.stderr, flush=True)

    repo_url = f"https://github.com/{username}/{repo_name}"
    print(f"Repository pubblicato con successo su: {repo_url}", flush=True)

    # Creazione della Release v2.3.0
    if os.path.exists(APPIMAGE_PATH):
        print("Pubblicazione Release v2.3.0 con AppImage allegata...", flush=True)
        release_notes = """## 🎬 Jellyfin Control Center v2.3.0

> **💡 Idea & Visione:** Concepito da **PsyTech76**  
> Sviluppato con PyQt6, Python 3 e supporto IA.

### 🇮🇹 Italiano - Note di Rilascio:
- **Integrazione di Sistema XDG:** Pulsante con un clic per abilitare/disabilitare l'app nel menu di sistema e barra applicazioni/dock.
- **Architettura Universale Multi-Utente:** Codice indipendente dall'ambiente locale con risoluzione dinamica percorsi.
- **Istanza Singola in Runtime:** Previene avvii multipli accidentali con focus automatico della finestra attiva.
- **Supporto Completo Plugin:** Intro Skipper e Trickplay integrati nativamente con monitoraggio real-time.
- **Monitoraggio Hardware Leggero:** CPU, RAM e GPU su richiesta a impatto zero.
- **Sessioni Attive:** Tracciamento utenti e flussi in tempo reale.
- **Installazione & Backup:** Script multi-distro e backup/ripristino .zip completi.
- **Multilingua:** Supporto per 5 lingue (IT, EN, FR, DE, ES) e Guida HTML integrata.

### 🇬🇧 English - Release Notes:
- **XDG System Integration:** One-click toggle to integrate app into system desktop menu and taskbar/dock.
- **Universal Multi-User Architecture:** Completely dynamic environment and home folder resolution.
- **Runtime Single-Instance:** Prevents duplicate instances and focuses the active window smoothly.
- **Full Plugin Support:** Built-in managers for Intro Skipper and Trickplay with live telemetry.
- **Zero-Overhead Hardware Monitor:** CPU, RAM, and GPU tracked strictly on-demand.
- **Active Sessions:** Live tracker for users, devices, and playback streams.
- **Setup & Backup:** Distro-aware install/uninstall and compressed .zip backup/restore.
- **Multilingual:** 5 languages (IT, EN, FR, DE, ES) with integrated standalone HTML user guide.
"""
        subprocess.run(["gh", "release", "delete", "v2.3.0", "-y"], cwd=PROJECT_DIR, capture_output=True)
        rel_res = subprocess.run([
            "gh", "release", "create", "v2.3.0",
            APPIMAGE_PATH,
            "--title", "Jellyfin Control Center v2.3.0",
            "--notes", release_notes
        ], cwd=PROJECT_DIR, capture_output=True, text=True)
        print(rel_res.stdout, rel_res.stderr, flush=True)

        # Carica anche gli archivi zip se presenti
        desktop_dir = os.path.expanduser("~/Scrivania" if os.path.exists(os.path.expanduser("~/Scrivania")) else "~/Desktop")
        zips = [
            os.path.join(desktop_dir, "Jellyfin_Control_Center_AppImage.zip"),
            os.path.join(desktop_dir, "Jellyfin_Control_Center_Progetto_Sorgenti.zip")
        ]
        valid_zips = [z for z in zips if os.path.exists(z)]
        if valid_zips:
            subprocess.run(["gh", "release", "upload", "v2.3.0"] + valid_zips + ["--clobber"], cwd=PROJECT_DIR, capture_output=True)

    desktop_dir = os.path.expanduser("~/Scrivania" if os.path.exists(os.path.expanduser("~/Scrivania")) else "~/Desktop")
    summary_file = os.path.join(desktop_dir, "GITHUB_PUBLISH_SUCCESS.txt")
    with open(summary_file, "w") as f:
        f.write(f"""================================================================================
             PROGETTO PUBBLICATO CON SUCCESSO SU GITHUB!
================================================================================
Repository: https://github.com/{username}/{repo_name}
Releases:   https://github.com/{username}/{repo_name}/releases/tag/v2.3.0
Data:       {time.strftime("%d/%m/%Y %H:%M:%S")}
================================================================================
""")
    print(f"\nRiepilogo salvato su {summary_file}", flush=True)
    write_status({"status": "completed", "repo_url": repo_url, "username": username})
    return True

if __name__ == "__main__":
    if authenticate_via_browser():
        publish_repo()
