# ==================================================================================================
# MODULO DI LOCALIZZAZIONE (i18n) E GUIDA HTML MULTILINGUA - JELLYFIN CONTROL CENTER
# ==================================================================================================
# Supporta 5 lingue: Italiano (it), English (en), Français (fr), Deutsch (de), Español (es).
# ==================================================================================================

SUPPORTED_LANGUAGES = {
    "it": "🇮🇹 Italiano",
    "en": "🇬🇧 English",
    "fr": "🇫🇷 Français",
    "de": "🇩🇪 Deutsch",
    "es": "🇪🇸 Español"
}

STRINGS = {
    # Intestazione e Azioni Globali
    "app_title": {
        "it": "Jellyfin Control Center",
        "en": "Jellyfin Control Center",
        "fr": "Jellyfin Control Center",
        "de": "Jellyfin Control Center",
        "es": "Jellyfin Control Center"
    },
    "app_subtitle": {
        "it": "Pannello di controllo e gestione multimediale Jellyfin",
        "en": "Jellyfin media control and management dashboard",
        "fr": "Tableau de bord de contrôle et gestion multimédia Jellyfin",
        "de": "Jellyfin Medien-Kontroll- und Verwaltungs-Dashboard",
        "es": "Panel de control y gestión multimedia de Jellyfin"
    },
    "btn_info": {
        "it": "ℹ️ Info",
        "en": "ℹ️ Info",
        "fr": "ℹ️ Info",
        "de": "ℹ️ Info",
        "es": "ℹ️ Info"
    },
    "btn_guide": {
        "it": "📖 Guida",
        "en": "📖 Guide",
        "fr": "📖 Guide",
        "de": "📖 Handbuch",
        "es": "📖 Guía"
    },
    # Schede Principali
    "tab_control": {
        "it": "⚡ Controllo",
        "en": "⚡ Control",
        "fr": "⚡ Contrôle",
        "de": "⚡ Steuerung",
        "es": "⚡ Control"
    },
    "tab_sessions": {
        "it": "👥 Dispositivi & Sessioni",
        "en": "👥 Devices & Sessions",
        "fr": "👥 Appareils & Sessions",
        "de": "👥 Geräte & Sitzungen",
        "es": "👥 Dispositivos y Sesiones"
    },
    "tab_hardware": {
        "it": "📊 Monitor Hardware",
        "en": "📊 Hardware Monitor",
        "fr": "📊 Moniteur Matériel",
        "de": "📊 Hardware-Monitor",
        "es": "📊 Monitor de Hardware"
    },
    "tab_install": {
        "it": "📦 Gestione Installazione",
        "en": "📦 Installation Management",
        "fr": "📦 Gestion de l'Installation",
        "de": "📦 Installationsverwaltung",
        "es": "📦 Gestión de Instalación"
    },
    "tab_backup": {
        "it": "💾 Backup & Ripristino",
        "en": "💾 Backup & Restore",
        "fr": "💾 Sauvegarde & Restauration",
        "de": "💾 Sicherung & Wiederherstellung",
        "es": "💾 Copia de Seguridad y Restauración"
    },
    "tab_plugin": {
        "it": "🔌 Plugin",
        "en": "🔌 Plugins",
        "fr": "🔌 Extensions",
        "de": "🔌 Plugins",
        "es": "🔌 Complementos"
    },
    # Sub-schede Plugin
    "subtab_intro_skipper": {
        "it": "🎵 Intro Skipper",
        "en": "🎵 Intro Skipper",
        "fr": "🎵 Intro Skipper",
        "de": "🎵 Intro Skipper",
        "es": "🎵 Intro Skipper"
    },
    "subtab_trickplay": {
        "it": "🖼️ Trickplay",
        "en": "🖼️ Trickplay",
        "fr": "🖼️ Trickplay",
        "de": "🖼️ Trickplay",
        "es": "🖼️ Trickplay"
    },
    # Pulsanti Comuni
    "btn_start": {
        "it": "▶️ Avvia Jellyfin",
        "en": "▶️ Start Jellyfin",
        "fr": "▶️ Démarrer Jellyfin",
        "de": "▶️ Jellyfin starten",
        "es": "▶️ Iniciar Jellyfin"
    },
    "btn_stop": {
        "it": "⏹️ Arresta Jellyfin",
        "en": "⏹️ Stop Jellyfin",
        "fr": "⏹️ Arrêter Jellyfin",
        "de": "⏹️ Jellyfin stoppen",
        "es": "⏹️ Detener Jellyfin"
    },
    "btn_restart": {
        "it": "🔄 Riavvia Jellyfin",
        "en": "🔄 Restart Jellyfin",
        "fr": "🔄 Redémarrer Jellyfin",
        "de": "🔄 Jellyfin neustarten",
        "es": "🔄 Reiniciar Jellyfin"
    },
    "btn_browser": {
        "it": "🌐 Apri nel Browser",
        "en": "🌐 Open in Browser",
        "fr": "🌐 Ouvrir dans le Navigateur",
        "de": "🌐 Im Browser öffnen",
        "es": "🌐 Abrir en el Navegador"
    },
    "btn_copy": {
        "it": "Copia",
        "en": "Copy",
        "fr": "Copier",
        "de": "Kopieren",
        "es": "Copiar"
    },
    "status_running": {
        "it": "● IN ESECUZIONE",
        "en": "● RUNNING",
        "fr": "● EN COURS D'EXÉCUTION",
        "de": "● WIRD AUSGEFÜHRT",
        "es": "● EN EJECUCIÓN"
    },
    "status_stopped": {
        "it": "● ARRESTATO",
        "en": "● STOPPED",
        "fr": "● ARRÊTÉ",
        "de": "● GESTOPPT",
        "es": "● DETENIDO"
    },
    "status_wait": {
        "it": "● IN ATTESA...",
        "en": "● WAITING...",
        "fr": "● EN ATTENTE...",
        "de": "● WARTEN...",
        "es": "● ESPERANDO..."
    },
    "status_unknown": {
        "it": "● SCONOSCIUTO",
        "en": "● UNKNOWN",
        "fr": "● INCONNU",
        "de": "● UNBEKANNT",
        "es": "● DESCONOCIDO"
    },
    # Plugin Actions
    "btn_install_plugin": {
        "it": "📥 Installa / Aggiorna",
        "en": "📥 Install / Update",
        "fr": "📥 Installer / Mettre à jour",
        "de": "📥 Installieren / Aktualisieren",
        "es": "📥 Instalar / Actualizar"
    },
    "btn_uninstall_plugin": {
        "it": "🗑️ Rimuovi Plugin",
        "en": "🗑️ Remove Plugin",
        "fr": "🗑️ Supprimer le Plugin",
        "de": "🗑️ Plugin entfernen",
        "es": "🗑️ Eliminar Complemento"
    },
    "btn_web_config": {
        "it": "🌐 Configurazione Web",
        "en": "🌐 Web Configuration",
        "fr": "🌐 Configuration Web",
        "de": "🌐 Web-Konfiguration",
        "es": "🌐 Configuración Web"
    },
    "btn_start_analysis": {
        "it": "▶️ Avvia Analisi Media",
        "en": "▶️ Start Media Analysis",
        "fr": "▶️ Démarrer l'Analyse des Médias",
        "de": "▶️ Medienanalyse starten",
        "es": "▶️ Iniciar Análisis de Medios"
    },
    "btn_stop_analysis": {
        "it": "⏹️ Arresta Analisi",
        "en": "⏹️ Stop Analysis",
        "fr": "⏹️ Arrêter l'Analyse",
        "de": "⏹️ Analyse stoppen",
        "es": "⏹️ Detener Análisis"
    },
    "btn_reset_trickplay": {
        "it": "🔄 Reset e Ricostruisci Libreria",
        "en": "🔄 Reset & Rebuild Library",
        "fr": "🔄 Réinitialiser et Reconstruire",
        "de": "🔄 Zurücksetzen & Neu aufbauen",
        "es": "🔄 Restablecer y Reconstruir"
    },
    "btn_refresh": {
        "it": "🔄 Aggiorna",
        "en": "🔄 Refresh",
        "fr": "🔄 Actualiser",
        "de": "🔄 Aktualisieren",
        "es": "🔄 Actualizar"
    },
    "badge_installed": {
        "it": "● INSTALLATO",
        "en": "● INSTALLED",
        "fr": "● INSTALLÉ",
        "de": "● INSTALLIERT",
        "es": "● INSTALADO"
    },
    "badge_not_installed": {
        "it": "● NON INSTALLATO",
        "en": "● NOT INSTALLED",
        "fr": "● NON INSTALLÉ",
        "de": "● NICHT INSTALLIERT",
        "es": "● NO INSTALADO"
    },
    "badge_task_running": {
        "it": "▶️ IN ESECUZIONE...",
        "en": "▶️ RUNNING...",
        "fr": "▶️ EN COURS...",
        "de": "▶️ IN AUSFÜHRUNG...",
        "es": "▶️ EN EJECUCIÓN..."
    },
    "badge_task_idle": {
        "it": "⏹️ INATTIVO / PRONTO",
        "en": "⏹️ IDLE / READY",
        "fr": "⏹️ INACTIF / PRÊT",
        "de": "⏹️ INAKTIV / BEREIT",
        "es": "⏹️ INACTIVO / LISTO"
    },
    "total_media_label": {
        "it": "Totale Media Libreria",
        "en": "Total Library Media",
        "fr": "Total Médias Bibliothèque",
        "de": "Gesamte Bibliotheksmedien",
        "es": "Total Medios Biblioteca"
    },
    "analyzed_media_label": {
        "it": "File Già Processati",
        "en": "Processed Files",
        "fr": "Fichiers Traités",
        "de": "Verarbeitete Dateien",
        "es": "Archivos Procesados"
    },
    "remaining_media_label": {
        "it": "File Rimanenti",
        "en": "Remaining Files",
        "fr": "Fichiers Restants",
        "de": "Verbleibende Dateien",
        "es": "Archivos Restantes"
    },
    "segments_label": {
        "it": "Segmenti Rilevati (Intro)",
        "en": "Detected Segments (Intros)",
        "fr": "Segments Détectés (Intros)",
        "de": "Erkannte Segmente (Intros)",
        "es": "Segmentos Detectados (Intros)"
    },
    "trickplay_generated_label": {
        "it": "Media con Miniature Generate",
        "en": "Media with Generated Thumbnails",
        "fr": "Médias avec Miniatures Générées",
        "de": "Medien mit generierten Miniaturbildern",
        "es": "Medios con Miniaturas Generadas"
    },
    "trickplay_size_label": {
        "it": "Dimensione Dati Trickplay",
        "en": "Trickplay Data Size",
        "fr": "Taille des Données Trickplay",
        "de": "Trickplay-Datengröße",
        "es": "Tamaño de Datos de Trickplay"
    },
    "single_instance_warn": {
        "it": "Un'altra istanza di Jellyfin Control Center è già in esecuzione ed è stata portata in primo piano.",
        "en": "Another instance of Jellyfin Control Center is already running and has been brought to the foreground.",
        "fr": "Une autre instance de Jellyfin Control Center est déjà en cours d'exécution et a été mise au premier plan.",
        "de": "Eine andere Instanz von Jellyfin Control Center wird bereits ausgeführt und wurde in den Vordergrund gebracht.",
        "es": "Otra instancia de Jellyfin Control Center ya se está ejecutando y se ha traído al primer plano."
    },
    # Integrazione di Sistema (Desktop Menu & Taskbar)
    "btn_system_integration_enable": {
        "it": "📌 Aggiungi al Menu di Sistema",
        "en": "📌 Add to System Menu",
        "fr": "📌 Ajouter au Menu Système",
        "de": "📌 Zum Systemmenü hinzufügen",
        "es": "📌 Agregar al Menú del Sistema"
    },
    "btn_system_integration_disable": {
        "it": "🗑️ Rimuovi dal Menu di Sistema",
        "en": "🗑️ Remove from System Menu",
        "fr": "🗑️ Retirer du Menu Système",
        "de": "🗑️ Aus Systemmenü entfernen",
        "es": "🗑️ Eliminar del Menú del Sistema"
    },
    "system_integration_title": {
        "it": "Integrazione di Sistema",
        "en": "System Integration",
        "fr": "Intégration Système",
        "de": "Systemintegration",
        "es": "Integración del Sistema"
    },
    "system_integration_installed_msg": {
        "it": "L'applicazione è stata integrata nel menu di sistema con successo!\n\nOra puoi:\n• Trovarla cercando 'Jellyfin Control Center' nel menu applicazioni del sistema\n• Fissarla alla barra delle applicazioni o al dock.",
        "en": "Application successfully integrated into system menu!\n\nYou can now:\n• Find it by searching 'Jellyfin Control Center' in your application menu\n• Pin it to your taskbar or system dock.",
        "fr": "L'application a été intégrée avec succès au menu système!\n\nVous pouvez maintenant:\n• La trouver en cherchant 'Jellyfin Control Center' dans le menu des applications\n• L'épingler à votre barre des tâches ou dock.",
        "de": "Anwendung erfolgreich in das Systemmenü integriert!\n\nSie können jetzt:\n• Sie durch Suchen nach 'Jellyfin Control Center' im Anwendungsmenü finden\n• Sie an Ihre Taskleiste oder Ihr Dock anheften.",
        "es": "¡Aplicación integrada con éxito en el menú del sistema!\n\nAhora puedes:\n• Encontrarla buscando 'Jellyfin Control Center' en el menú de aplicaciones\n• Fijarla a la barra de tareas o dock del sistema."
    },
    "system_integration_removed_msg": {
        "it": "L'applicazione è stata rimossa dal menu di sistema.",
        "en": "Application removed from system menu.",
        "fr": "Application retirée du menu système.",
        "de": "Anwendung aus dem Systemmenü entfernt.",
        "es": "Aplicación eliminada del menú del sistema."
    },
    "system_integrated_badge": {
        "it": "✓ Integrata nel Sistema (Clicca per rimuovere dal menu)",
        "en": "✓ System Integrated (Click to remove from menu)",
        "fr": "✓ Intégré au Système (Cliquez pour retirer du menu)",
        "de": "✓ Systemintegriert (Klicken zum Entfernen aus dem Menü)",
        "es": "✓ Integrado en el Sistema (Clic para eliminar del menú)"
    },
    "system_not_integrated_badge": {
        "it": "Integra l'applicazione nel menu di sistema e nella barra delle applicazioni",
        "en": "Integrate application into system menu and taskbar",
        "fr": "Intégrer l'application au menu système et à la barre des tâches",
        "de": "Anwendung in Systemmenü und Taskleiste integrieren",
        "es": "Integrar la aplicación en el menú del sistema y barra de tareas"
    }
}

def t(key, lang="it"):
    """Restituisce la traduzione per la chiave specificata nella lingua richiesta."""
    if key in STRINGS:
        return STRINGS[key].get(lang, STRINGS[key].get("en", key))
    return key


# ==================================================================================================
# INFORMAZIONI SUL PROGRAMMA (CREDITI E NOTE DI DISTRIBUZIONE)
# ==================================================================================================
def get_about_info_html(lang="it"):
    titles = {
        "it": "Informazioni su Jellyfin Control Center",
        "en": "About Jellyfin Control Center",
        "fr": "À propos de Jellyfin Control Center",
        "de": "Über Jellyfin Control Center",
        "es": "Acerca de Jellyfin Control Center"
    }
    
    ideas = {
        "it": "Nato da un'idea e visione di <b>PsyTech76</b>",
        "en": "Conceived and designed from an idea by <b>PsyTech76</b>",
        "fr": "Né d'une idée et vision de <b>PsyTech76</b>",
        "de": "Entstanden aus einer Idee und Vision von <b>PsyTech76</b>",
        "es": "Nacido de una idea y visión de <b>PsyTech76</b>"
    }

    ai_devs = {
        "it": "Sviluppato con Intelligenza Artificiale avanzata (DeepMind Antigravity) e Framework grafico <b>PyQt6 / Qt 6</b>.",
        "en": "Developed using advanced Artificial Intelligence (DeepMind Antigravity) and the <b>PyQt6 / Qt 6</b> framework.",
        "fr": "Développé avec une Intelligence Artificielle avancée (DeepMind Antigravity) et le framework <b>PyQt6 / Qt 6</b>.",
        "de": "Entwickelt mit fortschrittlicher künstlicher Intelligenz (DeepMind Antigravity) und dem <b>PyQt6 / Qt 6</b> Framework.",
        "es": "Desarrollado con Inteligencia Artificial avanzada (DeepMind Antigravity) y el framework <b>PyQt6 / Qt 6</b>."
    }

    dist_notes = {
        "it": "<b>Note di Distribuzione & Licenza:</b><br>"
              "Software open-source distribuibile liberamente in formato portabile AppImage (x86_64). "
              "Progettato per integrarsi senza attriti con container Docker Jellyfin, GPU NVIDIA NVENC e toolkit multi-distro Linux.",
        "en": "<b>Distribution & License Notes:</b><br>"
              "Open-source software freely distributable as a portable AppImage (x86_64). "
              "Designed for seamless integration with Docker Jellyfin containers, NVIDIA NVENC GPU acceleration, and Linux multi-distro toolkits.",
        "fr": "<b>Notes de Distribution & Licence:</b><br>"
              "Logiciel open-source librement distribuable au format portable AppImage (x86_64). "
              "Conçu pour s'intégrer harmonieusement avec Docker Jellyfin, accélération NVIDIA NVENC et environnements Linux multi-distributions.",
        "de": "<b>Vertriebs- & Lizenzhinweise:</b><br>"
              "Open-Source-Software, frei verteilbar im portablen AppImage-Format (x86_64). "
              "Entwickelt für die nahtlose Integration mit Docker Jellyfin, NVIDIA NVENC-Beschleunigung und Linux-Multi-Distro-Tools.",
        "es": "<b>Notas de Distribución y Licencia:</b><br>"
              "Software de código abierto libremente distribuible en formato portátil AppImage (x86_64). "
              "Diseñado para una integración perfecta con contenedores Docker Jellyfin, aceleración NVIDIA NVENC y distribuciones Linux."
    }

    title = titles.get(lang, titles["en"])
    idea = ideas.get(lang, ideas["en"])
    ai_dev = ai_devs.get(lang, ai_devs["en"])
    dist_note = dist_notes.get(lang, dist_notes["en"])

    return f"""
    <div style="font-family: sans-serif; color: #cfd3dc; line-height: 1.6; padding: 10px;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #00d2ff; margin-bottom: 4px;">Jellyfin Control Center</h2>
            <span style="background-color: #1e3a5f; color: #38bdf8; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 11px;">
                Versione 2.3.0 (x86_64)
            </span>
        </div>
        <p style="font-size: 14px; text-align: center; color: #34d399; margin-bottom: 18px;">
            💡 {idea}
        </p>
        <div style="background-color: #141620; border: 1px solid #282d3f; border-radius: 10px; padding: 14px; margin-bottom: 16px;">
            <p style="margin: 0 0 10px 0;">🤖 {ai_dev}</p>
            <p style="margin: 0; font-size: 12px; color: #9ba1b0;">{dist_note}</p>
        </div>
        <div style="text-align: center; font-size: 11px; color: #6b7280;">
            Made for Linux • Zero-Impact Architecture • Autonomous Standalone AppImage
        </div>
    </div>
    """


# ==================================================================================================
# GUIDA DELL'APPLICAZIONE IN FORMATO HTML LOCALIZZATA
# ==================================================================================================
def get_user_guide_html(lang="it"):
    """Restituisce il manuale operativo completo formattato in HTML styled per la lingua scelta."""

    guides = {
        "it": """
        <h1>Jellyfin Control Center - Manuale Operativo Completo</h1>
        <p class="subtitle">Guida di riferimento dettagliata a tutte le sezioni, comandi e indicatori dell'applicazione.</p>

        <div class="toc">
            <h3>Indice dei Contenuti:</h3>
            <ul>
                <li><a href="#sec1">1. Scheda Controllo & Dashboard</a></li>
                <li><a href="#sec2">2. Scheda Dispositivi & Sessioni</a></li>
                <li><a href="#sec3">3. Scheda Monitor Hardware (Zero Impatto)</a></li>
                <li><a href="#sec4">4. Scheda Gestione Installazione</a></li>
                <li><a href="#sec5">5. Scheda Backup & Ripristino (.zip)</a></li>
                <li><a href="#sec6">6. Scheda Gestione Plugin (Intro Skipper & Trickplay)</a></li>
                <li><a href="#sec7">7. Informazioni, Singola Istanza & Lingue</a></li>
            </ul>
        </div>

        <h2 id="sec1">1. ⚡ Scheda Controllo & Dashboard</h2>
        <p>È la centrale operativa principale per monitorare lo stato del server e lanciare azioni rapide.</p>
        <ul>
            <li><b>Badge di Stato</b>: Indica in tempo reale se Jellyfin è <code>IN ESECUZIONE</code> (verde), <code>ARRESTATO</code> (rosso) o <code>IN ATTESA</code> (giallo).</li>
            <li><b>Pulsante Avvia Jellyfin</b>: Avvia il container Docker ed inizializza i servizi multimediali.</li>
            <li><b>Pulsante Arresta Jellyfin</b>: Ferma in sicurezza il container Docker.</li>
            <li><b>Pulsante Riavvia Jellyfin</b>: Esegue un riavvio a caldo rapido del container Docker.</li>
            <li><b>Pulsante Apri nel Browser</b>: Lancia l'interfaccia web di Jellyfin (<code>http://localhost:8096</code>) nel browser predefinito di sistema.</li>
            <li><b>Pulsante Integrazione di Sistema</b>: Registra o rimuove con un solo clic l'applicazione nel menu di sistema XDG (<code>~/.local/share/applications/</code>), rendendola reperibile nella ricerca app del desktop e permettendone il fissaggio alla barra delle applicazioni o al dock.</li>
            <li><b>Indirizzi di Connessione</b>: Mostra l'indirizzo <i>Localhost</i> e l'<i>IP LAN</i> del PC (con pulsanti <b>Copia</b>) per connettere tablet, smart TV e client mobili sulla stessa rete.</li>
            <li><b>Scorciatoie Cartelle Multimediali</b>: Pulsanti rapidi per aprire con un clic le cartelle multimediali nel gestore file di sistema.</li>
            <li><b>Log del Server</b>: Visualizzatore live degli ultimi eventi registrati dal demone Docker di Jellyfin.</li>
        </ul>

        <h2 id="sec2">2. 👥 Scheda Dispositivi & Sessioni</h2>
        <p>Permette di monitorare chi sta guardando contenuti e come li sta riproducendo.</p>
        <ul>
            <li><b>Tabella Sessioni Live</b>: Elenca Utente, Dispositivo/Client (es. Jellyfin Web, Tablet Android), Contenuto in riproduzione, Metodo e Tempo di connessione.</li>
            <li><b>Badge Trascodifica</b>: Indica se la riproduzione avviene in <code>Direct Play</code> (senza consumo CPU) oppure in <code>Transcodifica Hardware</code> (tramite GPU dedicata).</li>
            <li><b>Casella Vista Terminale / Dati Grezzi</b>: Commuta istantaneamente tra la tabella grafica elegante e la visualizzazione JSON grezza ricevuta dalle API REST.</li>
        </ul>

        <h2 id="sec3">3. 📊 Scheda Monitor Hardware (Architettura a Impatto Zero)</h2>
        <p>Progettata per garantire che il monitoraggio delle risorse non consumi mai cicli di calcolo durante la visione di film o il normale utilizzo.</p>
        <ul>
            <li><b>Principio di Impatto Zero</b>: Le chiamate a <code>nvidia-smi</code> e <code>psutil</code> avvengono <b>SOLO</b> quando questa scheda è fisicamente visualizzata ed è spuntata la casella <i>Attiva Monitoraggio Attivo</i>. Appena si cambia scheda, il consumo CPU/GPU torna a zero.</li>
            <li><b>Monitor CPU & RAM</b>: Percentuale di utilizzo complessiva e memoria fisica allocata.</li>
            <li><b>Accelerazione GPU (NVIDIA / AMD / Intel)</b>: Telemetria in tempo reale su VRAM utilizzata, temperatura (°C), consumo energetico (Watt) e frequenze di clock del processore grafico.</li>
            <li><b>Container Docker</b>: Consumo specifico del processo Jellyfin rispetto all'intero sistema.</li>
        </ul>

        <h2 id="sec4">4. 📦 Scheda Gestione Installazione</h2>
        <p>Automatizza l'installazione e la rimozione del server Jellyfin rispettando la specifica distribuzione Linux in uso.</p>
        <ul>
            <li><b>Rilevamento Multi-Distro</b>: Riconosce automaticamente Arch Linux / CachyOS (<code>pacman</code>), Debian / Ubuntu (<code>apt</code>), Fedora (<code>dnf</code>) e openSUSE (<code>zypper</code>).</li>
            <li><b>Autenticazione Sicura</b>: Dialogo protetto per la richiesta della password di amministratore con pre-validazione (<code>sudo -k -S true</code>).</li>
            <li><b>Installazione Guidata</b>: Configura Docker, abilita il servizio, assegna i permessi utente e installa il toolkit NVIDIA per il passthrough della GPU.</li>
            <li><b>Rimozione Software</b>: Procedura pulita con opzione per conservare o purgare la cartella dei dati multimediali.</li>
        </ul>

        <h2 id="sec5">5. 💾 Scheda Backup & Ripristino (.zip)</h2>
        <p>Consente di proteggere le configurazioni, i database utenti e le librerie in un archivio compresso universale .zip.</p>
        <ul>
            <li><b>Casella Includi Cartella Metadata (~9 GB)</b>: Lasciandola disattivata, il backup include solo configurazioni e database salvando in meno di 2 secondi un file da soli ~60 MB. Attivandola, esegue il backup integrale di ogni singola miniatura e immagine.</li>
            <li><b>Monitoraggio Streaming</b>: Mostra avanzamento percentuale, velocità di elaborazione in MB/s e tempo stimato residuo (ETA).</li>
            <li><b>Regola a Zero Residui</b>: Se l'utente annulla il backup o il ripristino durante l'esecuzione, tutti i file parziali o temporanei vengono cancellati istantaneamente da disco senza lasciare scorie.</li>
        </ul>

        <h2 id="sec6">6. 🔌 Scheda Gestione Plugin (Intro Skipper & Trickplay)</h2>
        <p>Riorganizzata in comode sottoschede dedicate ai plugin avanzati:</p>

        <h3>🎵 Sottoscheda Intro Skipper</h3>
        <ul>
            <li><b>Installa / Aggiorna</b>: Supporta sia il download automatico online da GitHub (v12.0.4.0) che il caricamento manuale da un file <code>.zip</code> locale.</li>
            <li><b>Rimuovi Plugin</b>: Dialogo guidato che permette di scegliere se rimuovere il solo plugin preservando il database delle impronte (<code>introskipper-v2.db</code>) o eliminare tutto.</li>
            <li><b>Avvia / Arresta Analisi Media</b>: Interagisce con il task pianificato <code>IntroSkipperDetectSegmentsTask</code> tramite API REST di Jellyfin.</li>
            <li><b>Contatori in Tempo Reale</b>: Visualizza Media totali, File già processati, File rimanenti e Segmenti intro/credits rilevati.</li>
            <li><b>Registro Eventi Live</b>: Mostra in tempo reale gli episodi e le stagioni in corso di analisi con data e ora precisa ed auto-scroll.</li>
        </ul>

        <h3>🖼️ Sottoscheda Trickplay</h3>
        <ul>
            <li><b>Verifica Preventiva</b>: Controlla se il modulo Trickplay è già presente nel server prima di tentare l'installazione.</li>
            <li><b>Monitoraggio Modulo</b>: Rileva lo stato in tempo reale (In esecuzione / Inattivo) del generatore di miniature di scorrimento (scrubbing preview).</li>
            <li><b>Avvia / Arresta Analisi File</b>: Permette di avviare o bloccare l'attività <code>RefreshTrickplayImages</code>.</li>
            <li><b>Reset e Ricostruzione Libreria</b>: Pulisce la cartella dati <code>trickplay/</code>, azzera i record nel database e riavvia la generazione pulita da zero.</li>
            <li><b>Configurazione Web</b>: Apre con un clic il pannello Trickplay nel browser.</li>
        </ul>

        <h2 id="sec7">7. ℹ️ Informazioni, Istanza Singola & Localizzazione</h2>
        <ul>
            <li><b>Istanza Singola a Runtime</b>: Impedisce l'apertura accidentale di finestre duplicate; se avviata una seconda volta, la finestra esistente viene portata automaticamente in primo piano.</li>
            <li><b>Supporto Multi-Lingua (5 Lingue)</b>: Rilevamento automatico della lingua di sistema (Italiano, Inglese, Francese, Tedesco, Spagnolo) e selettore istantaneo nella barra superiore.</li>
            <li><b>Crediti di Sviluppo</b>: Ideato da <b>PsyTech76</b>, sviluppato con intelligenza artificiale avanzata e framework PyQt6.</li>
        </ul>
        """,

        "en": """
        <h1>Jellyfin Control Center - Complete User Guide</h1>
        <p class="subtitle">Comprehensive reference manual for all application sections, controls, and indicators.</p>

        <div class="toc">
            <h3>Table of Contents:</h3>
            <ul>
                <li><a href="#sec1">1. Control & Dashboard Tab</a></li>
                <li><a href="#sec2">2. Devices & Sessions Tab</a></li>
                <li><a href="#sec3">3. Hardware Monitor Tab (Zero-Impact)</a></li>
                <li><a href="#sec4">4. Installation Management Tab</a></li>
                <li><a href="#sec5">5. Backup & Restore (.zip) Tab</a></li>
                <li><a href="#sec6">6. Plugin Management Tab (Intro Skipper & Trickplay)</a></li>
                <li><a href="#sec7">7. Information, Single Instance & Languages</a></li>
            </ul>
        </div>

        <h2 id="sec1">1. ⚡ Control & Dashboard Tab</h2>
        <p>The primary control center for server status monitoring and quick actions.</p>
        <ul>
            <li><b>Status Badge</b>: Real-time indication of whether Jellyfin is <code>RUNNING</code> (green), <code>STOPPED</code> (red), or <code>WAITING</code> (yellow).</li>
            <li><b>Start Jellyfin Button</b>: Starts the Docker container and initializes media services.</li>
            <li><b>Stop Jellyfin Button</b>: Safely terminates the Docker container.</li>
            <li><b>Restart Jellyfin Button</b>: Performs a quick hot restart of the container.</li>
            <li><b>Open in Browser Button</b>: Launches the Jellyfin web UI (<code>http://localhost:8096</code>) in your default browser.</li>
            <li><b>System Integration Button</b>: With a single click, registers or removes the app from the XDG system menu (<code>~/.local/share/applications/</code>), making it discoverable in desktop application search and allowing pinning to taskbar or dock.</li>
            <li><b>Connection Addresses</b>: Displays <i>Localhost</i> and <i>LAN IP</i> addresses with convenient <b>Copy</b> buttons for tablets, TVs, and mobile clients.</li>
            <li><b>Media Folder Shortcuts</b>: One-click shortcuts to open media directories in your file manager.</li>
            <li><b>Server Logs</b>: Live viewer of recent output emitted by the Jellyfin container.</li>
        </ul>

        <h2 id="sec2">2. 👥 Devices & Sessions Tab</h2>
        <p>Monitor active streaming clients, users, and media playback methods.</p>
        <ul>
            <li><b>Live Sessions Table</b>: Lists User, Device/Client name, current media title, playback method, and connection duration.</li>
            <li><b>Transcoding Badge</b>: Distinguishes between <code>Direct Play</code> (no CPU overhead) and <code>Hardware Transcoding</code> (via dedicated GPU).</li>
            <li><b>Terminal / Raw Data Toggle</b>: Instantly switches between the visual table and raw JSON returned by the REST API.</li>
        </ul>

        <h2 id="sec3">3. 📊 Hardware Monitor Tab (Zero-Impact Architecture)</h2>
        <p>Engineered to ensure resource monitoring never degrades movie playback or system performance.</p>
        <ul>
            <li><b>Zero-Impact Principle</b>: Hardware queries to <code>nvidia-smi</code> and <code>psutil</code> run <b>ONLY</b> while this tab is active and the monitoring toggle is checked. Leaving the tab immediately drops polling overhead to zero.</li>
            <li><b>CPU & RAM Monitor</b>: Overall processor load and allocated system memory.</li>
            <li><b>GPU Acceleration (NVIDIA / AMD / Intel)</b>: Live telemetry for VRAM utilization, temperature (°C), power draw (Watts), and clock speeds.</li>
            <li><b>Docker Container Stats</b>: Specific CPU and memory usage of the Jellyfin process.</li>
        </ul>

        <h2 id="sec4">4. 📦 Installation Management Tab</h2>
        <p>Automates setup and cleanup for your specific Linux distribution.</p>
        <ul>
            <li><b>Multi-Distro Detection</b>: Automatically recognizes Arch / CachyOS (<code>pacman</code>), Debian / Ubuntu (<code>apt</code>), Fedora (<code>dnf</code>), and openSUSE (<code>zypper</code>).</li>
            <li><b>Secure Authentication</b>: Root/sudo password dialog with pre-validation (<code>sudo -k -S true</code>).</li>
            <li><b>Guided Installation</b>: Configures Docker, enables systemd services, sets user groups, and installs NVIDIA Container Toolkit.</li>
            <li><b>Clean Uninstallation</b>: Mirror removal procedure with data purge options.</li>
        </ul>

        <h2 id="sec5">5. 💾 Backup & Restore (.zip) Tab</h2>
        <p>Safeguard configurations, databases, and library settings in standard .zip archives.</p>
        <ul>
            <li><b>Include Metadata Folder (~9 GB)</b>: Unchecked by default for instant 2-second configuration backups (~60 MB). Checked for full thumbnail/trickplay backups.</li>
            <li><b>Streaming Monitor</b>: Live percentage progress, MB/s transfer speed, and Estimated Time of Arrival (ETA).</li>
            <li><b>Zero-Residue Cancellation</b>: Aborting operations immediately cleans up partial or incomplete files from disk.</li>
        </ul>

        <h2 id="sec6">6. 🔌 Plugin Management Tab (Intro Skipper & Trickplay)</h2>
        <p>Dedicated sub-tabs for advanced media enhancement plugins:</p>

        <h3>🎵 Intro Skipper Sub-tab</h3>
        <ul>
            <li><b>Install / Update</b>: Supports automatic GitHub release download (v12.0.4.0) or custom local <code>.zip</code> archive loading.</li>
            <li><b>Remove Plugin</b>: Guided dialog allowing preservation of the audio fingerprint database (<code>introskipper-v2.db</code>) or complete purge.</li>
            <li><b>Start / Stop Analysis</b>: Controls the <code>IntroSkipperDetectSegmentsTask</code> via Jellyfin REST API.</li>
            <li><b>Real-time Metrics</b>: Library totals, processed items, remaining files, and detected intro/credit segments.</li>
            <li><b>Live Event Log</b>: Monitored TV series and seasons in progress with timestamps and auto-scroll.</li>
        </ul>

        <h3>🖼️ Trickplay Sub-tab</h3>
        <ul>
            <li><b>Pre-installation Check</b>: Verifies if Trickplay is already installed before initiating setup.</li>
            <li><b>Module Monitoring</b>: Real-time detection of thumbnail generation tasks.</li>
            <li><b>Start / Stop File Analysis</b>: Start or interrupt the <code>RefreshTrickplayImages</code> task.</li>
            <li><b>Reset & Rebuild Library</b>: Cleans the <code>trickplay/</code> data folder, resets database entries, and restarts fresh generation.</li>
            <li><b>Web Configuration</b>: Direct browser link to the Trickplay settings page.</li>
        </ul>

        <h2 id="sec7">7. ℹ️ Information, Single Instance & Languages</h2>
        <ul>
            <li><b>Runtime Single Instance</b>: Prevents duplicate windows; launching a second instance focuses the active window.</li>
            <li><b>5 Languages Supported</b>: Automatic system language detection (Italian, English, French, German, Spanish) with instant runtime switcher.</li>
            <li><b>Credits</b>: Conceived by <b>PsyTech76</b>, developed with advanced AI and PyQt6.</li>
        </ul>
        """,

        "fr": """
        <h1>Jellyfin Control Center - Guide de l'Utilisateur</h1>
        <p class="subtitle">Manuel de référence pour toutes les sections, commandes et fonctionnalités de l'application.</p>

        <div class="toc">
            <h3>Table des Matières:</h3>
            <ul>
                <li><a href="#sec1">1. Onglet Contrôle & Tableau de Bord</a></li>
                <li><a href="#sec2">2. Onglet Appareils & Sessions</a></li>
                <li><a href="#sec3">3. Onglet Moniteur Matériel (Zéro Impact)</a></li>
                <li><a href="#sec4">4. Onglet Gestion de l'Installation</a></li>
                <li><a href="#sec5">5. Onglet Sauvegarde & Restauration (.zip)</a></li>
                <li><a href="#sec6">6. Onglet Gestion des Extensions (Intro Skipper & Trickplay)</a></li>
                <li><a href="#sec7">7. Informations, Instance Unique & Langues</a></li>
            </ul>
        </div>

        <h2 id="sec1">1. ⚡ Onglet Contrôle & Tableau de Bord</h2>
        <p>Centre de commande pour surveiller l'état du serveur et exécuter les actions courantes.</p>
        <ul>
            <li><b>État du Serveur</b>: Indique en temps réel si Jellyfin est <code>EN COURS</code> (vert), <code>ARRÊTÉ</code> (rouge) ou <code>EN ATTENTE</code> (jaune).</li>
            <li><b>Démarrer / Arrêter / Redémarrer</b>: Contrôle immédiat du conteneur Docker Jellyfin.</li>
            <li><b>Ouvrir dans le Navigateur</b>: Lance l'interface web (<code>http://localhost:8096</code>).</li>
            <li><b>Adresses Réseau</b>: Affiche l'adresse locale et l'IP LAN avec boutons de copie rapide.</li>
            <li><b>Raccourcis Dossiers</b>: Accès direct à vos répertoires multimédias.</li>
            <li><b>Intégration Système</b>: Ajoute ou retire l'application du menu système XDG et du dock en un clic.</li>
        </ul>

        <h2 id="sec2">2. 👥 Onglet Appareils & Sessions</h2>
        <ul>
            <li><b>Sessions en Direct</b>: Utilisateur, appareil, média en cours et durée.</li>
            <li><b>Badge Transcodage</b>: Différencie la lecture directe (<code>Direct Play</code>) du transcodage matériel GPU.</li>
            <li><b>Vue Terminal</b>: Affichage basculable entre tableau graphique et JSON brut.</li>
        </ul>

        <h2 id="sec3">3. 📊 Onglet Moniteur Matériel (Zéro Impact)</h2>
        <ul>
            <li><b>Architecture Zéro Impact</b>: Les métriques GPU/CPU ne s'exécutent que lorsque cet onglet est affiché.</li>
            <li><b>Accélération GPU (NVIDIA / AMD / Intel)</b>: VRAM utilisée, température, watts et horloges en direct.</li>
        </ul>

        <h2 id="sec4">4. 📦 Onglet Gestion de l'Installation</h2>
        <ul>
            <li><b>Multi-Distributions</b>: Détection automatique d'Arch, Debian, Ubuntu, Fedora et openSUSE.</li>
            <li><b>Installation Automatisée</b>: Prise en charge de Docker et NVIDIA Container Toolkit.</li>
        </ul>

        <h2 id="sec5">5. 💾 Onglet Sauvegarde & Restauration (.zip)</h2>
        <ul>
            <li><b>Sauvegarde Rapide</b>: Option d'exclusion du dossier volumineux des métadonnées pour des sauvegardes en 2 secondes.</li>
            <li><b>Annulation Propre</b>: Suppression immédiate des fichiers temporaires en cas d'interruption.</li>
        </ul>

        <h2 id="sec6">6. 🔌 Onglet Gestion des Extensions (Intro Skipper & Trickplay)</h2>
        <h3>🎵 Intro Skipper</h3>
        <p>Détection et saut automatique des intros, crédits et résumés. Installation en ligne/locale, démarrage/arrêt d'analyse, compteurs et journaux en direct.</p>
        <h3>🖼️ Trickplay</h3>
        <p>Vérification préalable, suivi des tâches de génération de vignettes, réinitialisation de bibliothèque et configuration web.</p>

        <h2 id="sec7">7. ℹ️ Informations & Langues</h2>
        <p>Conçu d'après une idée de <b>PsyTech76</b>. Prise en charge de 5 langues (Italien, Anglais, Français, Allemand, Espagnol) avec détection automatique de la langue système.</p>
        """,

        "de": """
        <h1>Jellyfin Control Center - Vollständiges Handbuch</h1>
        <p class="subtitle">Detaillierte Anleitung zu allen Abschnitten, Befehlen und Indikatoren der Anwendung.</p>

        <div class="toc">
            <h3>Inhaltsverzeichnis:</h3>
            <ul>
                <li><a href="#sec1">1. Reiter Steuerung & Dashboard</a></li>
                <li><a href="#sec2">2. Reiter Geräte & Sitzungen</a></li>
                <li><a href="#sec3">3. Reiter Hardware-Monitor (Null Belastung)</a></li>
                <li><a href="#sec4">4. Reiter Installationsverwaltung</a></li>
                <li><a href="#sec5">5. Reiter Sicherung & Wiederherstellung (.zip)</a></li>
                <li><a href="#sec6">6. Reiter Plugin-Verwaltung (Intro Skipper & Trickplay)</a></li>
                <li><a href="#sec7">7. Informationen, Einzelinstanz & Sprachen</a></li>
            </ul>
        </div>

        <h2 id="sec1">1. ⚡ Reiter Steuerung & Dashboard</h2>
        <p>Hauptzentrale zur Überwachung und Steuerung des Jellyfin-Servers.</p>
        <ul>
            <li><b>Server-Status</b>: Echtzeit-Anzeige: <code>WIRD AUSGEFÜHRT</code> (Grün), <code>GESTOPPT</code> (Rot) oder <code>WARTEN</code> (Gelb).</li>
            <li><b>Start / Stopp / Neustart</b>: Direkte Steuerung des Docker-Containers.</li>
            <li><b>Im Browser öffnen</b>: Startet die Web-Oberfläche (<code>http://localhost:8096</code>).</li>
            <li><b>Systemintegration</b>: Registriert oder entfernt die Anwendung mit einem Klick im XDG-Systemmenü und Dock.</li>
            <li><b>Netzwerkadressen</b>: Schnelle Kopierbuttons für Localhost und LAN-IP.</li>
        </ul>

        <h2 id="sec2">2. 👥 Reiter Geräte & Sitzungen</h2>
        <ul>
            <li><b>Aktive Sitzungen</b>: Benutzer, Gerät, Medium und Dauer in Echtzeit.</li>
            <li><b>Transkodierungs-Status</b>: Erkennt Direct Play und Hardware-Transkodierung via dedizierter GPU.</li>
        </ul>

        <h2 id="sec3">3. 📊 Reiter Hardware-Monitor (Null Belastung)</h2>
        <ul>
            <li><b>Null-Last-Prinzip</b>: CPU- und GPU-Abfragen laufen nur, wenn der Reiter aktiv betrachtet wird.</li>
            <li><b>GPU-Beschleunigung (NVIDIA / AMD / Intel)</b>: VRAM, Temperatur, Stromverbrauch (Watt) und Taktfrequenzen.</li>
        </ul>

        <h2 id="sec4">4. 📦 Reiter Installationsverwaltung</h2>
        <ul>
            <li><b>Multi-Distribution</b>: Unterstützung für Arch, Debian, Ubuntu, Fedora und openSUSE.</li>
            <li><b>Automatisierte Einrichtung</b>: Konfiguriert Docker und das NVIDIA Container Toolkit.</li>
        </ul>

        <h2 id="sec5">5. 💾 Reiter Sicherung & Wiederherstellung (.zip)</h2>
        <ul>
            <li><b>Schnellsicherung</b>: Metadaten-Ausschluss für 2-Sekunden-Backups (~60 MB).</li>
            <li><b>Rückstandslose Bereinigung</b>: Sicheres Löschen bei Abbruch.</li>
        </ul>

        <h2 id="sec6">6. 🔌 Reiter Plugin-Verwaltung (Intro Skipper & Trickplay)</h2>
        <h3>🎵 Intro Skipper</h3>
        <p>Automatische Intro- und Abspann-Erkennung mit Online-Installation, Start/Stopp-Steuerung und Live-Logs.</p>
        <h3>🖼️ Trickplay</h3>
        <p>Vorschau-Miniaturansichten mit Vorabprüfung, Fortschrittsanzeige, Bibliotheks-Reset und Browser-Konfiguration.</p>

        <h2 id="sec7">7. ℹ️ Informationen & Sprachen</h2>
        <p>Entstanden aus einer Idee von <b>PsyTech76</b>. Unterstützung für 5 Sprachen (Italienisch, Englisch, Französisch, Deutsch, Spanisch).</p>
        """,

        "es": """
        <h1>Jellyfin Control Center - Manual del Usuario</h1>
        <p class="subtitle">Guía de referencia completa para todas las secciones, controles e indicadores.</p>

        <div class="toc">
            <h3>Índice de Contenidos:</h3>
            <ul>
                <li><a href="#sec1">1. Pestaña Control y Panel</a></li>
                <li><a href="#sec2">2. Pestaña Dispositivos y Sesiones</a></li>
                <li><a href="#sec3">3. Pestaña Monitor de Hardware (Cero Impacto)</a></li>
                <li><a href="#sec4">4. Pestaña Gestión de Instalación</a></li>
                <li><a href="#sec5">5. Pestaña Copia de Seguridad y Restauración (.zip)</a></li>
                <li><a href="#sec6">6. Pestaña Gestión de Complementos (Intro Skipper y Trickplay)</a></li>
                <li><a href="#sec7">7. Información, Instancia Única e Idiomas</a></li>
            </ul>
        </div>

        <h2 id="sec1">1. ⚡ Pestaña Control y Panel</h2>
        <p>Centro de mando principal para supervisar y operar el servidor Jellyfin.</p>
        <ul>
            <li><b>Estado del Servidor</b>: Indicador en tiempo real: <code>EN EJECUCIÓN</code> (verde), <code>DETENIDO</code> (rojo) o <code>ESPERANDO</code> (amarillo).</li>
            <li><b>Iniciar / Detener / Reiniciar</b>: Control directo del contenedor Docker.</li>
            <li><b>Abrir en el Navegador</b>: Abre la interfaz web (<code>http://localhost:8096</code>).</li>
            <li><b>Integración del Sistema</b>: Agrega o elimina con un clic la aplicación del menú del sistema XDG y dock.</li>
            <li><b>Direcciones de Red</b>: Botones de copia rápida para Localhost e IP de red local.</li>
        </ul>

        <h2 id="sec2">2. 👥 Pestaña Dispositivos y Sesiones</h2>
        <ul>
            <li><b>Sesiones Activas</b>: Usuario, dispositivo, reproducción y duración.</li>
            <li><b>Insignia de Transcodificación</b>: Distingue Direct Play de transcodificación hardware mediante GPU.</li>
        </ul>

        <h2 id="sec3">3. 📊 Pestaña Monitor de Hardware (Cero Impacto)</h2>
        <ul>
            <li><b>Principio de Cero Impacto</b>: Las consultas de hardware solo se ejecutan cuando esta pestaña está abierta.</li>
            <li><b>Aceleración GPU (NVIDIA / AMD / Intel)</b>: VRAM, temperatura, potencia (vatios) y reloj en tiempo real.</li>
        </ul>

        <h2 id="sec4">4. 📦 Pestaña Gestión de Instalación</h2>
        <ul>
            <li><b>Multi-Distribución</b>: Detección de Arch, Debian, Ubuntu, Fedora y openSUSE.</li>
            <li><b>Instalación Guiada</b>: Configura Docker y NVIDIA Container Toolkit.</li>
        </ul>

        <h2 id="sec5">5. 💾 Pestaña Copia de Seguridad y Restauración (.zip)</h2>
        <ul>
            <li><b>Copia Rápida</b>: Opción de exclusión de metadatos para copias en 2 segundos.</li>
            <li><b>Cancelación Limpia</b>: Borrado inmediato de archivos temporales al cancelar.</li>
        </ul>

        <h2 id="sec6">6. 🔌 Pestaña Gestión de Complementos (Intro Skipper y Trickplay)</h2>
        <h3>🎵 Intro Skipper</h3>
        <p>Detección automática de intros y créditos, instalación online/local, inicio/parada y registros en directo.</p>
        <h3>🖼️ Trickplay</h3>
        <p>Generación de miniaturas de desplazamiento, verificación previa, reinicio de biblioteca y panel web.</p>

        <h2 id="sec7">7. ℹ️ Información e Idiomas</h2>
        <p>Concebido por <b>PsyTech76</b>. Soporte para 5 idiomas (italiano, inglés, francés, alemán y español) con autodetección.</p>
        """
    }

    body = guides.get(lang, guides["en"])

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            background-color: #12141c;
            color: #cfd3dc;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            margin: 20px;
            padding: 0;
        }}
        h1 {{
            color: #00d2ff;
            border-bottom: 2px solid #232738;
            padding-bottom: 10px;
            font-size: 22px;
            margin-top: 0;
        }}
        h2 {{
            color: #b855d4;
            border-bottom: 1px solid #232738;
            padding-bottom: 6px;
            margin-top: 28px;
            font-size: 17px;
        }}
        h3 {{
            color: #38bdf8;
            font-size: 14px;
            margin-top: 18px;
        }}
        .subtitle {{
            color: #9ba1b0;
            font-size: 13px;
            margin-top: -6px;
            margin-bottom: 20px;
        }}
        .toc {{
            background-color: #181b26;
            border: 1px solid #282d3f;
            border-radius: 8px;
            padding: 14px 20px;
            margin-bottom: 25px;
        }}
        .toc h3 {{
            margin-top: 0;
            color: #00d2ff;
            font-size: 13px;
        }}
        .toc ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .toc li {{
            margin-bottom: 5px;
        }}
        a {{
            color: #00d2ff;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        code {{
            background-color: #1c202d;
            border: 1px solid #2e354b;
            color: #34d399;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
            font-family: monospace;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        b {{
            color: #ffffff;
        }}
    </style>
    </head>
    <body>
    {body}
    </body>
    </html>
    """
    return html
