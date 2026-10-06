#!/usr/bin/env bash
# ==================================================================================================
# SCRIPT DI COMPILAZIONE / PACKAGING: Jellyfin Control Center -> AppImage x86_64
# ==================================================================================================
# Questo script automatizza l'assemblaggio e la creazione dell'eseguibile autonomo AppImage.
# Può essere eseguito su qualsiasi sistema Linux dove siano presenti:
#   1. Python 3 (con PyQt6 e psutil installati nel sistema o in un venv)
#   2. appimagetool (o connettività internet per scaricarlo automaticamente)
#
# Uso:
#   cd /percorso/del/progetto
#   ./scripts/build_appimage.sh [cartella_destinazione_output]
# ==================================================================================================

set -e # Interrompe immediatamente in caso di errore critico

# Determina la cartella radice del progetto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Cartella di output predefinita (se non passata come primo argomento)
OUTPUT_DIR="${1:-${PROJECT_ROOT}/dist}"
mkdir -p "${OUTPUT_DIR}"

APP_NAME="Jellyfin_Control_Center"
ARCH="x86_64"
OUTPUT_APPIMAGE="${OUTPUT_DIR}/${APP_NAME}-${ARCH}.AppImage"
BUILD_DIR="${PROJECT_ROOT}/build_tmp"
APPDIR="${BUILD_DIR}/AppDir"

echo "========================================================================"
echo "    CREAZIONE APPIMAGE: ${APP_NAME} (${ARCH})"
echo "========================================================================"
echo "Cartella Progetto : ${PROJECT_ROOT}"
echo "Cartella Build    : ${BUILD_DIR}"
echo "File Output       : ${OUTPUT_APPIMAGE}"
echo "========================================================================"

# 1. Verifica disponibilità di appimagetool
APPIMAGETOOL_BIN="$(command -v appimagetool || true)"
if [ -z "$APPIMAGETOOL_BIN" ]; then
    echo "[-] appimagetool non trovato nel PATH di sistema."
    echo "[*] Download automatico di appimagetool standalone..."
    mkdir -p "${PROJECT_ROOT}/bin"
    APPIMAGETOOL_BIN="${PROJECT_ROOT}/bin/appimagetool"
    if [ ! -f "$APPIMAGETOOL_BIN" ]; then
        curl -L -o "$APPIMAGETOOL_BIN" "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
        chmod +x "$APPIMAGETOOL_BIN"
    fi
fi
echo "[+] Strumento AppImage: ${APPIMAGETOOL_BIN}"

# 2. Pulizia e preparazione dell'AppDir
echo "[*] Preparazione struttura AppDir..."
rm -rf "${BUILD_DIR}"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${APPDIR}/usr/share/applications"

# Trova la directory site-packages di Python
PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
SITE_PACKAGES_DIR="${APPDIR}/usr/lib/python${PY_VER}/site-packages"
mkdir -p "${SITE_PACKAGES_DIR}"

# 3. Copia dei sorgenti e delle risorse
echo "[*] Copia del codice sorgente e icone..."
cp "${PROJECT_ROOT}/src/"*.py "${APPDIR}/usr/bin/"
chmod +x "${APPDIR}/usr/bin/jellyfin_manager.py"

if [ -f "${PROJECT_ROOT}/icons/jellyfin-control.png" ]; then
    cp "${PROJECT_ROOT}/icons/jellyfin-control.png" "${APPDIR}/jellyfin-control.png"
    cp "${PROJECT_ROOT}/icons/jellyfin-control.png" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/jellyfin-control.png"
fi

if [ -f "${PROJECT_ROOT}/icons/jellyfin-control.svg" ]; then
    cp "${PROJECT_ROOT}/icons/jellyfin-control.svg" "${APPDIR}/.DirIcon"
fi

# 4. Creazione del file desktop conforme a XDG
echo "[*] Generazione del file desktop..."
cat << 'EOF_DESKTOP' > "${APPDIR}/jellyfin-control.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Jellyfin Control Center
GenericName=Gestore Jellyfin
Comment=Gestione, Monitoraggio Risorse, Installazione e Backup di Jellyfin Media Server
Exec=jellyfin_manager.py
Icon=jellyfin-control
Terminal=false
Categories=AudioVideo;Video;Network;Settings;
StartupNotify=true
EOF_DESKTOP
cp "${APPDIR}/jellyfin-control.desktop" "${APPDIR}/usr/share/applications/jellyfin-control.desktop"

# 5. Raggruppamento librerie Python (PyQt6, psutil)
echo "[*] Impacchettamento librerie Python necessarie..."
HOST_SITE="$(python3 -c 'import site; print(site.getsitepackages()[0] if site.getsitepackages() else "")')"
if [ -d "${HOST_SITE}/PyQt6" ]; then
    cp -r "${HOST_SITE}/PyQt6" "${SITE_PACKAGES_DIR}/"
    cp -r "${HOST_SITE}"/psutil* "${SITE_PACKAGES_DIR}/" 2>/dev/null || true
else
    # Ricerca alternativa se in ambiente distro-specifico o venv
    PYQT_PATH="$(python3 -c 'import PyQt6, os; print(os.path.dirname(PyQt6.__file__))' 2>/dev/null || true)"
    PSUTIL_PATH="$(python3 -c 'import psutil, os; print(os.path.dirname(psutil.__file__))' 2>/dev/null || true)"
    if [ -n "$PYQT_PATH" ] && [ -d "$PYQT_PATH" ]; then
        cp -r "$PYQT_PATH" "${SITE_PACKAGES_DIR}/"
    fi
    if [ -n "$PSUTIL_PATH" ] && [ -d "$PSUTIL_PATH" ]; then
        cp -r "$PSUTIL_PATH" "${SITE_PACKAGES_DIR}/"
        cp -r "${PSUTIL_PATH}"*.dist-info "${SITE_PACKAGES_DIR}/" 2>/dev/null || true
    fi
fi

# 6. Generazione dello script launcher AppRun
echo "[*] Generazione del launcher AppRun..."
cat << 'EOF_APPRUN' > "${APPDIR}/AppRun"
#!/usr/bin/env bash
# Determina la posizione runtime dell'AppDir
SELF=$(readlink -f "$0")
HERE=${SELF%/*}

# Configura le variabili d'ambiente per il runtime isolato
export PATH="${HERE}/usr/bin:${PATH}"
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS}"

# Rileva automaticamente la cartella site-packages inclusa
for d in "${HERE}"/usr/lib/python*/site-packages; do
    if [ -d "$d" ]; then
        export PYTHONPATH="${d}:${PYTHONPATH}"
    fi
done

# Individua l'interprete Python sul sistema host
PYTHON_BIN=$(command -v python3 || command -v python)
if [ -z "$PYTHON_BIN" ]; then
    echo "Errore: Python 3 non trovato nel sistema operativo host." >&2
    exit 1
fi

# Avvia l'applicazione Jellyfin Control Center
exec "$PYTHON_BIN" "${HERE}/usr/bin/jellyfin_manager.py" "$@"
EOF_APPRUN
chmod +x "${APPDIR}/AppRun"

# 7. Compilazione finale con appimagetool
echo "[*] Compilazione pacchetto squashfs AppImage..."
ARCH=x86_64 "${APPIMAGETOOL_BIN}" -n "${APPDIR}" "${OUTPUT_APPIMAGE}"

# 8. Pulizia file temporanei di build
echo "[*] Pulizia cartelle temporanee..."
rm -rf "${BUILD_DIR}"

echo "========================================================================"
echo "    COMPILAZIONE COMPLETATA CON SUCCESSO!"
echo "========================================================================"
echo "AppImage generata : ${OUTPUT_APPIMAGE}"
ls -lh "${OUTPUT_APPIMAGE}"
echo "========================================================================"
