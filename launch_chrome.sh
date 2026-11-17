#!/bin/bash
# ==============================================================================
# Helper script to launch Google Chrome with remote debugging for YGBot
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load .env file if present
if [ -f "$SCRIPT_DIR/.env" ]; then
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # Trim leading/trailing whitespace
        key=$(echo "$key" | xargs)
        # Skip empty lines and comments
        [ -z "$key" ] && continue
        [[ "$key" =~ ^# ]] && continue
        # Strip outer quotes from value
        value=$(echo "$value" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^["'"'"']//' -e 's/["'"'"']$//')
        export "$key=$value"
    done < "$SCRIPT_DIR/.env"
fi

PORT="${CHROME_PORT:-9222}"
URL="${GAME_URL:-https://ygofm.com/}"
CHROME_BIN="${CHROME_BINARY:-google-chrome}"
USER_DATA_DIR="${CHROME_USER_DATA_DIR:-$HOME/.config/ygbot-chrome}"

echo "================================================================"
echo " Starting Google Chrome with Remote Debugging on port $PORT..."
echo " Profile: $USER_DATA_DIR"
echo " Target: $URL"
echo "================================================================"

mkdir -p "$USER_DATA_DIR"

# Check if google-chrome or configured binary exists
if command -v "$CHROME_BIN" &> /dev/null; then
    CHROME_CMD="$CHROME_BIN"
elif command -v google-chrome &> /dev/null; then
    CHROME_CMD="google-chrome"
elif command -v google-chrome-stable &> /dev/null; then
    CHROME_CMD="google-chrome-stable"
elif command -v chromium &> /dev/null; then
    CHROME_CMD="chromium"
elif command -v chromium-browser &> /dev/null; then
    CHROME_CMD="chromium-browser"
else
    echo "[ERROR] Google Chrome / Chromium not found in PATH."
    exit 1
fi

# Launch chrome with remote debugging port and dedicated user data dir
$CHROME_CMD --remote-debugging-port=$PORT --user-data-dir="$USER_DATA_DIR" --no-first-run --no-default-browser-check "$URL" &

echo "[SUCCESS] Chrome launched! You can now run: python3 run.py"
