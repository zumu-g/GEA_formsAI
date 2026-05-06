#!/usr/bin/env bash
# Starts the PDF form-filling Python backend on port 8000.
# Usage: bash slate/scripts/start-backend.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../../form_filling_app/form-filling-exp/backend"
VENV_DIR="$SCRIPT_DIR/../../form_filling_app/form-filling-exp/.venv"
ENV_FILE="$SCRIPT_DIR/../.env.local"

if [ ! -d "$BACKEND_DIR" ]; then
  echo "❌ Backend not found at: $BACKEND_DIR" >&2
  exit 1
fi

# Activate virtualenv
source "$VENV_DIR/bin/activate"

# Read ANTHROPIC_API_KEY from slate/.env.local if not already set
if [ -z "$ANTHROPIC_API_KEY" ] && [ -f "$ENV_FILE" ]; then
  export ANTHROPIC_API_KEY=$(grep '^ANTHROPIC_API_KEY=' "$ENV_FILE" | cut -d= -f2-)
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "⚠️  Warning: ANTHROPIC_API_KEY not set. AI detection features may fail." >&2
fi

cd "$BACKEND_DIR"
echo "🚀 Starting backend on http://localhost:8001 ..."
uvicorn main:app --port 8001 --reload
