"""
Configuration manager for YGBot.
Loads settings from .env and config.json with fallback defaults.
"""

import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
DEFAULT_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


def load_env_file(env_path: str = DEFAULT_ENV_PATH) -> None:
    """Loads environment variables from a .env file without requiring external dependencies."""
    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    # Do not overwrite variables already passed via shell environment
                    if key not in os.environ:
                        os.environ[key] = val
    except Exception as e:
        print(f"[WARN] Failed to load .env file from {env_path}: {e}")


@dataclass
class Config:
    # Game & Chrome settings
    game_url: str = "https://ygofm.com/"
    chrome_host: str = "127.0.0.1"
    chrome_port: int = 9222
    target_url_pattern: str = "ygofm.com"
    alt_url_pattern: str = "intercityygo.com"
    auto_launch: bool = False
    chrome_binary: str = "google-chrome"
    user_data_dir: str = os.path.expanduser("~/.config/ygbot-chrome")
    
    # Farming settings
    opponent: str = "High Mage Martis"
    max_duels: int = 0  # 0 = infinite
    strategy: str = "THTD"  # Twin-Headed Thunder Dragon priority
    guardian_star: str = "Pluto"
    action_delay: float = 0.5
    turn_wait: float = 1.5
    combat_wait: float = 2.0
    loading_timeout: float = 30.0
    
    # Normalized screen coordinates (relative 0.0 to 1.0)
    hand_cards: List[List[float]] = field(default_factory=lambda: [
        [0.372, 0.870],
        [0.417, 0.870],
        [0.461, 0.870],
        [0.505, 0.870],
        [0.550, 0.870]
    ])
    guardian_star_coords: Dict[str, List[float]] = field(default_factory=lambda: {
        "Pluto": [0.443, 0.856],
        "Mercury": [0.536, 0.856],
        "left": [0.443, 0.856],
        "right": [0.536, 0.856]
    })
    player_zones: List[List[float]] = field(default_factory=lambda: [
        [0.333, 0.523],
        [0.396, 0.523],
        [0.458, 0.523],
        [0.521, 0.523],
        [0.583, 0.523]
    ])
    opponent_zones: List[List[float]] = field(default_factory=lambda: [
        [0.333, 0.370],
        [0.396, 0.370],
        [0.458, 0.370],
        [0.521, 0.370],
        [0.583, 0.370]
    ])
    opponent_direct: List[float] = field(default_factory=lambda: [0.500, 0.250])
    combat_button: List[float] = field(default_factory=lambda: [0.500, 0.856])
    start_duel_button: List[float] = field(default_factory=lambda: [0.911, 0.468])
    duel_again_button: List[float] = field(default_factory=lambda: [0.448, 0.588])
    return_free_duel_button: List[float] = field(default_factory=lambda: [0.552, 0.588])

    @classmethod
    def load(cls, config_path: str = DEFAULT_CONFIG_PATH, env_path: str = DEFAULT_ENV_PATH) -> "Config":
        # Load environment variables from .env
        load_env_file(env_path)

        cfg = cls()

        # Load from config.json if present
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                chrome = data.get("chrome", {})
                cfg.game_url = chrome.get("game_url", cfg.game_url)
                cfg.chrome_host = chrome.get("host", cfg.chrome_host)
                cfg.chrome_port = chrome.get("debug_port", cfg.chrome_port)
                cfg.target_url_pattern = chrome.get("target_url_pattern", cfg.target_url_pattern)
                cfg.alt_url_pattern = chrome.get("alt_url_pattern", cfg.alt_url_pattern)
                cfg.auto_launch = chrome.get("auto_launch", cfg.auto_launch)
                cfg.chrome_binary = chrome.get("chrome_binary", cfg.chrome_binary)
                cfg.user_data_dir = chrome.get("user_data_dir", cfg.user_data_dir)
                
                farming = data.get("farming", {})
                cfg.opponent = farming.get("opponent", cfg.opponent)
                cfg.max_duels = farming.get("max_duels", cfg.max_duels)
                cfg.strategy = farming.get("strategy", cfg.strategy)
                cfg.guardian_star = farming.get("guardian_star", cfg.guardian_star)
                cfg.action_delay = farming.get("action_delay", cfg.action_delay)
                cfg.turn_wait = farming.get("turn_wait", cfg.turn_wait)
                cfg.combat_wait = farming.get("combat_wait", cfg.combat_wait)
                cfg.loading_timeout = farming.get("loading_timeout", cfg.loading_timeout)
                
                coords = data.get("coordinates", {})
                if "hand_cards" in coords:
                    cfg.hand_cards = coords["hand_cards"]
                if "guardian_star" in coords:
                    cfg.guardian_star_coords = coords["guardian_star"]
                if "player_zones" in coords:
                    cfg.player_zones = coords["player_zones"]
                if "opponent_zones" in coords:
                    cfg.opponent_zones = coords["opponent_zones"]
                if "opponent_direct" in coords:
                    cfg.opponent_direct = coords["opponent_direct"]
                if "combat_button" in coords:
                    cfg.combat_button = coords["combat_button"]
                if "start_duel_button" in coords:
                    cfg.start_duel_button = coords["start_duel_button"]
                if "duel_again_button" in coords:
                    cfg.duel_again_button = coords["duel_again_button"]
                if "return_free_duel_button" in coords:
                    cfg.return_free_duel_button = coords["return_free_duel_button"]
            except Exception as e:
                print(f"[WARN] Failed to load config from {config_path}: {e}. Using defaults.")

        # Override with environment variables (.env or shell)
        if "GAME_URL" in os.environ and os.environ["GAME_URL"]:
            cfg.game_url = os.environ["GAME_URL"]
        if "TARGET_URL_PATTERN" in os.environ and os.environ["TARGET_URL_PATTERN"]:
            cfg.target_url_pattern = os.environ["TARGET_URL_PATTERN"]
        if "ALT_URL_PATTERN" in os.environ and os.environ["ALT_URL_PATTERN"]:
            cfg.alt_url_pattern = os.environ["ALT_URL_PATTERN"]
        if "CHROME_HOST" in os.environ and os.environ["CHROME_HOST"]:
            cfg.chrome_host = os.environ["CHROME_HOST"]
        if "CHROME_PORT" in os.environ and os.environ["CHROME_PORT"]:
            try:
                cfg.chrome_port = int(os.environ["CHROME_PORT"])
            except ValueError:
                pass
        if "CHROME_BINARY" in os.environ and os.environ["CHROME_BINARY"]:
            cfg.chrome_binary = os.environ["CHROME_BINARY"]
        if "CHROME_USER_DATA_DIR" in os.environ and os.environ["CHROME_USER_DATA_DIR"]:
            cfg.user_data_dir = os.environ["CHROME_USER_DATA_DIR"]
        if "AUTO_LAUNCH" in os.environ and os.environ["AUTO_LAUNCH"]:
            cfg.auto_launch = os.environ["AUTO_LAUNCH"].strip().lower() in ("true", "1", "yes")
        if "OPPONENT" in os.environ and os.environ["OPPONENT"]:
            cfg.opponent = os.environ["OPPONENT"]
        if "MAX_DUELS" in os.environ and os.environ["MAX_DUELS"]:
            try:
                cfg.max_duels = int(os.environ["MAX_DUELS"])
            except ValueError:
                pass
        if "STRATEGY" in os.environ and os.environ["STRATEGY"]:
            cfg.strategy = os.environ["STRATEGY"]
        if "GUARDIAN_STAR" in os.environ and os.environ["GUARDIAN_STAR"]:
            cfg.guardian_star = os.environ["GUARDIAN_STAR"]
        if "ACTION_DELAY" in os.environ and os.environ["ACTION_DELAY"]:
            try:
                cfg.action_delay = float(os.environ["ACTION_DELAY"])
            except ValueError:
                pass
        if "TURN_WAIT" in os.environ and os.environ["TURN_WAIT"]:
            try:
                cfg.turn_wait = float(os.environ["TURN_WAIT"])
            except ValueError:
                pass
        if "COMBAT_WAIT" in os.environ and os.environ["COMBAT_WAIT"]:
            try:
                cfg.combat_wait = float(os.environ["COMBAT_WAIT"])
            except ValueError:
                pass
        if "LOADING_TIMEOUT" in os.environ and os.environ["LOADING_TIMEOUT"]:
            try:
                cfg.loading_timeout = float(os.environ["LOADING_TIMEOUT"])
            except ValueError:
                pass

        return cfg
