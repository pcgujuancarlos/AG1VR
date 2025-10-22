#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 AG_SPY_V90b — http://localhost:8565"
if [ ! -d ".venv" ]; then
  echo "🔧 Creando entorno virtual (.venv)…"
  python3 -m venv .venv || { echo "❌ Error creando .venv"; exit 1; }
fi
source .venv/bin/activate || { echo "❌ No se pudo activar .venv"; exit 1; }
pip install -r requirements.txt --quiet || { echo "❌ Error en pip install"; exit 1; }
python3 -m streamlit run app_v90b.py --server.port=8565
