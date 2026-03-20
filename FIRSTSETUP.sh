#!/usr/bin/env bash
# AI Search Engine - one-shot setup script (Linux/macOS / Bash)
# Run from project root: ./FIRSTSETUP.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo
echo "[*] AI Search Engine - Setup"
echo "Project root: ${PROJECT_ROOT}"

get_system_python() {
    local candidate
    for candidate in python3 python; do
        if command -v "${candidate}" >/dev/null 2>&1; then
            if "${candidate}" -c "import sys; print(sys.version)" >/dev/null 2>&1; then
                echo "${candidate}"
                return 0
            fi
        fi
    done
    return 1
}

echo "[1/6] Checking Python installation..."
if ! SYSTEM_PYTHON="$(get_system_python)"; then
    echo "[!] Python not found. Install Python 3.8+ and try again."
    exit 1
fi

PY_VERSION_STR="$(${SYSTEM_PYTHON} --version 2>&1)"
echo "    Found: ${PY_VERSION_STR}"

if ! ${SYSTEM_PYTHON} - <<'PY'
import sys
sys.exit(0 if sys.version_info >= (3, 8) else 1)
PY
then
    echo "[!] Python 3.8+ is required. Found: ${PY_VERSION_STR}"
    exit 1
fi

DOT_VENV_DIR="${PROJECT_ROOT}/.venv"
LEGACY_VENV_DIR="${PROJECT_ROOT}/venv"

if [[ -d "${DOT_VENV_DIR}" ]]; then
    VENV_DIR="${DOT_VENV_DIR}"
    VENV_LABEL=".venv"
elif [[ -d "${LEGACY_VENV_DIR}" ]]; then
    VENV_DIR="${LEGACY_VENV_DIR}"
    VENV_LABEL="venv"
else
    VENV_DIR="${DOT_VENV_DIR}"
    VENV_LABEL=".venv"
fi

echo
echo "[2/6] Setting up virtual environment..."
if [[ -d "${VENV_DIR}" ]]; then
    echo "Virtual environment already exists at ${VENV_LABEL} - skipping creation."
else
    "${SYSTEM_PYTHON}" -m venv "${VENV_DIR}"
    echo "Created virtual environment at ${VENV_LABEL}"
fi

PYTHON_EXE="${VENV_DIR}/bin/python"
PIP_EXE="${VENV_DIR}/bin/pip"

if [[ ! -x "${PYTHON_EXE}" || ! -x "${PIP_EXE}" ]]; then
    echo "[!] Virtual environment seems incomplete at '${VENV_DIR}'. Delete it and run the script again."
    exit 1
fi

echo
echo "[3/6] Installing dependencies..."
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"
if [[ ! -f "${REQUIREMENTS_FILE}" ]]; then
    echo "[!] requirements.txt not found at project root."
    exit 1
fi

"${PIP_EXE}" install --upgrade pip
"${PIP_EXE}" install -r "${REQUIREMENTS_FILE}"
echo "Dependencies installed."

ENV_FILE="${PROJECT_ROOT}/.env"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"

echo
echo "[4/6] Configuring environment file..."
if [[ -f "${ENV_FILE}" ]]; then
    echo ".env already exists - keeping it unchanged."
else
    if [[ -f "${ENV_EXAMPLE}" ]]; then
        cp "${ENV_EXAMPLE}" "${ENV_FILE}"
        echo "Created .env from .env.example"
        echo "!! Open .env and fill in API credentials before running searches."
    else
        echo "[!] .env.example not found. Create a .env file manually (see README)."
    fi
fi

MODEL_NAME="paraphrase-multilingual-mpnet-base-v2"
MODEL_DEST="${PROJECT_ROOT}/models/${MODEL_NAME}"

echo
echo "[5/6] Setting up embedding model..."
MODEL_READY=true
for f in config.json model.safetensors tokenizer.json; do
    if [[ ! -f "${MODEL_DEST}/${f}" ]]; then
        MODEL_READY=false
        break
    fi
done

if [[ "${MODEL_READY}" == "true" ]]; then
    echo "Embedding model already present at models/${MODEL_NAME}"
else
    echo "Downloading embedding model from Hugging Face (one-time, large download)..."
    "${PYTHON_EXE}" - <<PY
from sentence_transformers import SentenceTransformer
from pathlib import Path

dest = Path(r"${MODEL_DEST}")
dest.parent.mkdir(parents=True, exist_ok=True)
print(f"Saving model to: {dest}")
model = SentenceTransformer("${MODEL_NAME}")
model.save(str(dest))
print("Model saved.")
PY
    echo "Model downloaded and saved."
fi

echo
echo "[6/6] Selenium / Docker setup (optional)..."
DOCKER_AVAILABLE=false
if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
        DOCKER_AVAILABLE=true
    fi
fi

if [[ "${DOCKER_AVAILABLE}" == "true" ]]; then
    read -r -p "Docker is available. Start Selenium container now? [y/N] " answer
    if [[ "${answer}" =~ ^[Yy]$ ]]; then
        if PROJECT_ROOT="${PROJECT_ROOT}" "${PYTHON_EXE}" - <<'PY'
import os
import sys

project_root = os.environ["PROJECT_ROOT"]
sys.path.insert(0, project_root)
from src.docker_manager import ensure_selenium_container

ok = ensure_selenium_container()
sys.exit(0 if ok else 1)
PY
        then
            echo "[+] Selenium container is ready."
            echo "Tip: keep SELENIUM_REMOTE_URL empty in local .env to allow fallback behavior."
        else
            echo "[!] Selenium container could not be started. Check Docker and try again."
        fi
    else
        echo "Skipped. You can start Selenium later using src.docker_manager.ensure_selenium_container()."
    fi
else
    echo "Docker not detected or daemon unavailable - app can still use local ChromeDriver fallback."
fi

echo
echo "[+] Setup complete!"
echo "Activate virtual environment: source ${VENV_LABEL}/bin/activate"
echo "Start API server after activation: ./start_api.sh"
echo "Direct API start (without activation): ${VENV_LABEL}/bin/python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload"
echo "Or run CLI mode: ${VENV_LABEL}/bin/python src/main.py"
