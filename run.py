#!/usr/bin/env python3
"""
Yu-Gi-Oh! Forbidden Memories Online Auto-Dueler Bot (YGBot)
Main command-line entry point.
"""

import sys
import os
import argparse
import subprocess
import time

from ygbot.config import Config
from ygbot.bot import YGBot
from ygbot.cdp_client import CDPClient
from ygbot.utils import print_banner, log, Colors

def launch_chrome_process(binary: str = "google-chrome", port: int = 9222, url: str = "https://ygofm.com/", user_data_dir: str = None):
    """Launches Google Chrome with remote debugging enabled."""
    if not user_data_dir:
        user_data_dir = os.path.expanduser("~/.config/ygbot-chrome")
    os.makedirs(user_data_dir, exist_ok=True)
    log(f"Launching {binary} with --remote-debugging-port={port} and --user-data-dir={user_data_dir}...", "INFO")
    cmd = [
        binary,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        url
    ]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(f"Chrome started (PID: {proc.pid}). Waiting for port to open...", "SUCCESS")
        time.sleep(2.0)
        return proc
    except FileNotFoundError:
        log(f"Could not find binary '{binary}'. Please start Chrome manually with: google-chrome --remote-debugging-port={port}", "ERROR")
        return None

def test_connection(config: Config):
    """Diagnoses connection to Chrome and lists open tabs."""
    log("Running connection diagnostics...", "INFO")
    client = CDPClient(host=config.chrome_host, port=config.chrome_port)
    
    if not client.is_chrome_running():
        log(f"No Chrome instance found listening on {config.chrome_host}:{config.chrome_port}", "ERROR")
        log("To start Chrome with debugging:", "WARN")
        log(f"  ./launch_chrome.sh  OR  google-chrome --remote-debugging-port={config.chrome_port} --user-data-dir=\"$HOME/.config/ygbot-chrome\"", "WARN")
        return False

    log(f"Successfully reached Chrome on port {config.chrome_port}!", "SUCCESS")
    tabs = client.get_tabs()
    log(f"Found {len(tabs)} open page tabs:", "INFO")
    for i, tab in enumerate(tabs):
        title = tab.get("title", "No Title")
        url = tab.get("url", "")
        log(f"  [{i+1}] {title} ({url})", "INFO")

    game_tab = client.find_game_tab([config.target_url_pattern, config.alt_url_pattern, "ygofm", "duel", "forbidden"])
    if game_tab:
        log(f"Game tab detected: '{game_tab.get('title')}'", "SUCCESS")
    else:
        log("No tab matched game patterns, but you can navigate to the game in any open tab.", "WARN")
    
    return True

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="Autonomous Auto-Dueler Bot for Forbidden Memories Online"
    )
    parser.add_argument("--url", "-u", type=str, default=None,
                        help="Target game URL to play (default: https://ygofm.com/)")
    parser.add_argument("--opponent", "-o", type=str, default=None,
                        help="Opponent name in Free Duel (e.g. 'High Mage Martis', 'Meadow Mage')")
    parser.add_argument("--duels", "-d", type=int, default=None,
                        help="Number of duels to farm (0 = infinite farming)")
    parser.add_argument("--port", "-p", type=int, default=None,
                        help="Chrome remote debugging port (default: 9222)")
    parser.add_argument("--star", "-s", type=str, default=None,
                        help="Preferred Guardian Star (default: Pluto)")
    parser.add_argument("--strategy", type=str, default=None,
                        help="Duel strategy: 'THTD' (Twin-Headed Thunder Dragon) or 'highest_atk'")
    parser.add_argument("--user-data-dir", type=str, default=None,
                        help="Chrome user data directory for isolated profile (default: ~/.config/ygbot-chrome)")
    parser.add_argument("--test", action="store_true",
                        help="Test connection to Chrome and list open tabs")
    parser.add_argument("--launch-chrome", action="store_true",
                        help="Automatically launch Chrome with remote debugging enabled")
    
    args = parser.parse_args()
    
    cfg = Config.load()
    
    # Apply CLI overrides
    if args.url:
        cfg.game_url = args.url
    if args.opponent:
        cfg.opponent = args.opponent
    if args.duels is not None:
        cfg.max_duels = args.duels
    if args.port:
        cfg.chrome_port = args.port
    if args.user_data_dir:
        cfg.user_data_dir = args.user_data_dir
    if args.star:
        cfg.guardian_star = args.star
    if args.strategy:
        cfg.strategy = args.strategy

    if args.launch_chrome:
        launch_chrome_process(cfg.chrome_binary, cfg.chrome_port, cfg.game_url, cfg.user_data_dir)

    if args.test:
        test_connection(cfg)
        return

    # Start the bot!
    bot = YGBot(cfg)
    bot.start_farming()

if __name__ == "__main__":
    main()
