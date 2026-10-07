#!/usr/bin/env python3
"""
Script per la generazione automatica di screenshot ad alta risoluzione
delle schermate principali di Jellyfin Control Center.
Genera le immagini sia in Italiano (docs/screenshots/it/) che in Inglese (docs/screenshots/en/),
applicando sfocatura (Gaussian Blur) su tutti i dati sensibili (IP LAN, nomi utenti, log).
"""

import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt6.QtWidgets import QApplication, QTableWidgetItem, QTableWidget
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor
from PIL import Image, ImageFilter

from src.jellyfin_manager import JellyfinManager, GuideDialog
from src.translations import t


def blur_box(image_path, box, radius=10):
    """Applica un filtro Gaussian Blur ad una specifica area rettangolare (x1, y1, x2, y2)."""
    with Image.open(image_path) as im:
        im = im.convert("RGBA")
        crop = im.crop(box)
        blurred = crop.filter(ImageFilter.GaussianBlur(radius=radius))
        im.paste(blurred, box)
        im.save(image_path)


def populate_and_capture(lang="it", output_dir="docs/screenshots/it"):
    os.makedirs(output_dir, exist_ok=True)
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        
    win = JellyfinManager()
    win.resize(1160, 780)
    win.current_lang = lang
    idx = win.combo_lang.findData(lang)
    if idx >= 0:
        win.combo_lang.setCurrentIndex(idx)
    win.retranslate_ui()
    win.show()
    app.processEvents()

    # Stato server sempre attivo (verde)
    status_text = t("status_running", lang)
    win.header_status_badge.setText(status_text)
    win.header_status_badge.setStyleSheet(
        "background-color: #0f3d2e; color: #2ecc71; border: 1px solid #27ae60; "
        "border-radius: 12px; padding: 4px 12px; font-weight: bold; font-size: 13px;"
    )

    # =========================================================================
    # 1. SCHEDA CONTROLLO & DASHBOARD
    # =========================================================================
    win.tab_widget.setCurrentIndex(0)
    
    win.status_badge.setText(status_text)
    win.status_badge.setStyleSheet(
        "background-color: #0f3d2e; color: #2ecc71; border: 1px solid #27ae60; "
        "border-radius: 12px; padding: 4px 12px; font-weight: bold; font-size: 13px;"
    )
    
    uptime_str = "4 giorni, 18 ore, 35 minuti" if lang == "it" else "4 days, 18 hours, 35 minutes"
    win.lbl_val_uptime.setText(uptime_str)
    win.lbl_val_loc.setText("http://localhost:8096")
    win.lbl_val_lan.setText("http://192.168.1.185:8096")
    
    logs_sample = (
        "[2026-10-07 07:15:00] [INF] Jellyfin Media Server v10.9.11 initialized successfully\n"
        "[2026-10-07 07:15:01] [INF] Kestrel listening on all interfaces at http://0.0.0.0:8096\n"
        "[2026-10-07 07:15:02] [INF] Loaded libraries: Movies, TV Shows, Music, Documentaries\n"
        "[2026-10-07 07:15:03] [INF] Hardware acceleration profile: NVIDIA NVENC / NVDEC enabled\n"
        "[2026-10-07 07:15:04] [INF] WebSocket session manager ready for incoming client connections\n"
        "[2026-10-07 07:15:05] [INF] Background scheduled task engine started\n"
        "[2026-10-07 07:45:12] [INF] Client authenticated: TV-LivingRoom via Jellyfin Android TV\n"
        "[2026-10-07 08:02:19] [INF] Playback started: Direct Play stream allocated"
    )
    win.txt_logs.setPlainText(logs_sample)
    app.processEvents()

    dash_path = os.path.join(output_dir, "01_dashboard.png")
    win.grab().save(dash_path)
    
    # Sfocatura dell'indirizzo IP LAN su Dashboard
    pos_lan = win.lbl_val_lan.mapTo(win, QPoint(0, 0))
    ip_box = (pos_lan.x() + 45, pos_lan.y() - 2, pos_lan.x() + 195, pos_lan.y() + win.lbl_val_lan.height() + 2)
    blur_box(dash_path, ip_box, radius=8)
    print(f"[{lang.upper()}] Generato 01_dashboard.png con IP sfocato per privacy.")

    # =========================================================================
    # 2. SCHEDA DISPOSITIVI & SESSIONI LIVE
    # =========================================================================
    win.tab_widget.setCurrentIndex(1)
    win.lbl_sessions_count.setText("2 sessioni attive" if lang == "it" else "2 active sessions")
    win.sessions_table.setRowCount(2)
    win.sessions_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
    
    u1 = QTableWidgetItem("User_LivingRoom")
    u1.setForeground(QColor("#00d2ff"))
    d1 = QTableWidgetItem("Android TV (Sony 4K)")
    m1 = QTableWidgetItem("Tears of Steel (4K Remux)")
    p1 = QTableWidgetItem("Direct Play")
    p1.setForeground(QColor("#2ecc71"))
    t1 = QTableWidgetItem("00:48:15")
    
    for c, itm in enumerate([u1, d1, m1, p1, t1]):
        win.sessions_table.setItem(0, c, itm)
        
    u2 = QTableWidgetItem("User_MobileGuest")
    u2.setForeground(QColor("#00d2ff"))
    d2 = QTableWidgetItem("Jellyfin Web (Chrome 128)")
    m2 = QTableWidgetItem("Big Buck Bunny (1080p)")
    p2 = QTableWidgetItem("Transcode (NVENC H.264)" if lang == "en" else "Transcodifica (NVENC H.264)")
    p2.setForeground(QColor("#b855d4"))
    t2 = QTableWidgetItem("00:15:42")
    
    for c, itm in enumerate([u2, d2, m2, p2, t2]):
        win.sessions_table.setItem(1, c, itm)

    for r in range(win.sessions_table.rowCount()):
        for c in range(win.sessions_table.columnCount()):
            it = win.sessions_table.item(r, c)
            if it:
                it.setBackground(QColor("#161a24"))

    win.sessions_table.clearSelection()
    app.processEvents()
    sess_path = os.path.join(output_dir, "02_sessioni.png" if lang == "it" else "02_sessions.png")
    win.grab().save(sess_path)
    
    # Sfocatura colonna utenti (privacy)
    tbl_pos = win.sessions_table.viewport().mapTo(win, QPoint(0, 0))
    r1 = win.sessions_table.visualItemRect(u1)
    r2 = win.sessions_table.visualItemRect(u2)
    
    box_u1 = (tbl_pos.x() + r1.x() + 4, tbl_pos.y() + r1.y() + 4, tbl_pos.x() + r1.x() + 115, tbl_pos.y() + r1.y() + r1.height() - 4)
    box_u2 = (tbl_pos.x() + r2.x() + 4, tbl_pos.y() + r2.y() + 4, tbl_pos.x() + r2.x() + 115, tbl_pos.y() + r2.y() + r2.height() - 4)
    blur_box(sess_path, box_u1, radius=8)
    blur_box(sess_path, box_u2, radius=8)
    print(f"[{lang.upper()}] Generato {os.path.basename(sess_path)} con utenti sfocati per privacy.")

    # =========================================================================
    # 3. SCHEDA MONITOR HARDWARE
    # =========================================================================
    win.tab_widget.setCurrentIndex(2)
    win.chk_monitor_hw.setChecked(True)
    win.lbl_hw_status.setText("● MONITOR ATTIVO (0% IMPATTO IN BACKGROUND)" if lang == "it" else "● MONITOR ACTIVE (0% BACKGROUND OVERHEAD)")
    win.lbl_hw_status.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 11px;")
    
    win.lbl_cpu_model.setText("AMD Ryzen 7 / Intel Core Multi-Core (16 Threads)")
    win.bar_cpu.setValue(18)
    win.lbl_cpu_val.setText("18.4%")
    
    win.lbl_ram_details.setText("RAM: 4.8 GB / 16.0 GB (11.2 GB Liberi)" if lang == "it" else "RAM: 4.8 GB / 16.0 GB (11.2 GB Free)")
    win.bar_ram.setValue(30)
    win.lbl_ram_val.setText("30.0%")
    
    win.lbl_gpu_model.setText("NVIDIA GeForce GPU • Driver 560.35 • CUDA 12.6")
    win.bar_gpu.setValue(34)
    win.lbl_gpu_val.setText("34% Carico GPU" if lang == "it" else "34% GPU Load")
    win.lbl_gpu_vram.setText("VRAM: 2.4 GB / 8.0 GB (30%)")
    win.lbl_gpu_temp.setText("Temp: 48°C")
    win.lbl_gpu_power.setText("Potenza: 42 W" if lang == "it" else "Power: 42 W")
    
    win.lbl_docker_stats.setText(
        "Container Jellyfin: CPU: 2.6% | Memoria RAM: 580 MB | Task attivi: 4" if lang == "it" 
        else "Jellyfin Container: CPU: 2.6% | Memory RAM: 580 MB | Active Tasks: 4"
    )
    
    app.processEvents()
    hw_path = os.path.join(output_dir, "03_hardware.png")
    win.grab().save(hw_path)
    print(f"[{lang.upper()}] Generato 03_hardware.png.")

    # =========================================================================
    # 4. SCHEDA PLUGIN: INTRO SKIPPER
    # =========================================================================
    win.tab_widget.setCurrentIndex(5)
    win.plugin_subtabs.setCurrentIndex(0)
    
    win.lbl_plugin_badge.setText("● INSTALLATO (v12.0.4.0)" if lang == "it" else "● INSTALLED (v12.0.4.0)")
    win.lbl_plugin_badge.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 12px;")
    
    win.lbl_plugin_task_badge.setText("● ANALISI IN CORSO..." if lang == "it" else "● ANALYSIS IN PROGRESS...")
    win.lbl_plugin_task_badge.setStyleSheet("color: #00d2ff; font-weight: bold; font-size: 12px;")
    
    win.bar_plugin_progress.setValue(65)
    win.lbl_plugin_progress_pct.setText("65%")
    win.lbl_plugin_prog_desc.setText(
        "Scansione audio impronte digitali ed analisi sigle (420 / 646)" if lang == "it"
        else "Scanning audio fingerprints and detecting intro segments (420 / 646)"
    )
    
    win.lbl_plugin_total_media.setText("646")
    win.lbl_plugin_analyzed_media.setText("420")
    win.lbl_plugin_remaining_media.setText("226")
    win.lbl_plugin_segments_detected.setText("388")
    
    intro_log_sample = (
        "[2026-10-07 08:10:14] [INTRO] Inizializzazione motore di analisi spettrografica cromatica...\n"
        "[2026-10-07 08:11:02] [INTRO] File processato: S01E01 - Rilevato segmento Intro: 00:01:15 - 00:02:45\n"
        "[2026-10-07 08:11:45] [INTRO] File processato: S01E02 - Rilevato segmento Intro: 00:01:18 - 00:02:48\n"
        "[2026-10-07 08:12:30] [INTRO] File processato: S01E03 - Riconosciuta corrispondenza cluster impronte (Score: 0.98)\n"
        "[2026-10-07 08:13:12] [INTRO] File processato: S01E04 - Rilevati Titoli di Coda (Credits): 00:23:40 - 00:24:50\n"
        "[2026-10-07 08:14:05] [INTRO] Salvataggio fingerprint su introskipper-v2.db completato."
    )
    win.txt_plugin_log.setPlainText(intro_log_sample)
    
    app.processEvents()
    intro_path = os.path.join(output_dir, "04_intro_skipper.png")
    win.grab().save(intro_path)
    
    # Sfocatura di parti del log per privacy
    log_pos = win.txt_plugin_log.viewport().mapTo(win, QPoint(0, 0))
    blur_log_box = (log_pos.x() + 180, log_pos.y() + 15, log_pos.x() + 380, log_pos.y() + 110)
    blur_box(intro_path, blur_log_box, radius=7)
    print(f"[{lang.upper()}] Generato 04_intro_skipper.png con log sfocato per privacy.")

    # =========================================================================
    # 5. SCHEDA PLUGIN: TRICKPLAY
    # =========================================================================
    win.plugin_subtabs.setCurrentIndex(1)
    
    win.lbl_tp_badge.setText("● INSTALLATO E PRONTO" if lang == "it" else "● INSTALLED AND READY")
    win.lbl_tp_badge.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 12px;")
    
    win.lbl_tp_task_badge.setText("● GENERAZIONE MINIATURE IN CORSO..." if lang == "it" else "● THUMBNAIL GENERATION IN PROGRESS...")
    win.lbl_tp_task_badge.setStyleSheet("color: #00d2ff; font-weight: bold; font-size: 12px;")
    
    win.bar_tp_progress.setValue(58)
    win.lbl_tp_progress_pct.setText("58%")
    win.lbl_tp_prog_desc.setText(
        "Elaborazione frame e tile BIF (RefreshTrickplayImages: 375 / 646)" if lang == "it"
        else "Processing frames and BIF tiles (RefreshTrickplayImages: 375 / 646)"
    )
    
    win.lbl_tp_generated.setText("375")
    win.lbl_tp_total.setText("646")
    win.lbl_tp_remaining.setText("271")
    win.lbl_tp_size.setText("2.8 GB")
    
    tp_log_sample = (
        "[2026-10-07 08:05:10] [TRICKPLAY] Avvio task pianificato: RefreshTrickplayImages\n"
        "[2026-10-07 08:06:22] [TRICKPLAY] Generazione tile JPEG (320x180) per video ID #10482 completata (10 fps)\n"
        "[2026-10-07 08:07:44] [TRICKPLAY] Generazione tile JPEG (320x180) per video ID #10483 completata (10 fps)\n"
        "[2026-10-07 08:08:50] [TRICKPLAY] Aggiornamento record tabella TrickplayInfos su database jellyfin.db\n"
        "[2026-10-07 08:10:02] [TRICKPLAY] File BIF memorizzati nella directory di cache trickplay/\n"
        "[2026-10-07 08:11:15] [TRICKPLAY] Elaborazione in corso per prossimo elemento in coda..."
    )
    win.txt_tp_log.setPlainText(tp_log_sample)
    
    app.processEvents()
    tp_path = os.path.join(output_dir, "05_trickplay.png")
    win.grab().save(tp_path)
    print(f"[{lang.upper()}] Generato 05_trickplay.png.")

    # =========================================================================
    # 6. GUIDA UTENTE HTML INTEGRATA
    # =========================================================================
    guide = GuideDialog(win, lang=lang)
    guide.resize(960, 700)
    guide.show()
    app.processEvents()
    
    guide_path = os.path.join(output_dir, "06_guida_html.png" if lang == "it" else "06_html_guide.png")
    guide.grab().save(guide_path)
    guide.close()
    print(f"[{lang.upper()}] Generato {os.path.basename(guide_path)}.")

    win.close()
    print(f"[{lang.upper()}] Completato!\n")


if __name__ == "__main__":
    print("Avvio generazione screenshot bilingue con protezione privacy...")
    populate_and_capture(lang="it", output_dir="docs/screenshots/it")
    populate_and_capture(lang="en", output_dir="docs/screenshots/en")
    print("Tutti gli screenshot (IT ed EN) sono stati generati con successo!")
