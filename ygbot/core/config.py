"""
Configuration manager for YGBot.
Loads settings from .env and config.json with fallback defaults.
"""

import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple

# Resolves to project root (/home/paulo/Projects/YGBot)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")
DEFAULT_ENV_PATH = os.path.join(PROJECT_ROOT, ".env")


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
        load_env_file(env_path)
        cfg = cls()

        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for k, v in data.items():
                    if hasattr(cfg, k):
                        setattr(cfg, k, v)
            except Exception as e:
                print(f"[WARN] Error loading {config_path}: {e}")

        # Environment variable overrides
        if os.environ.get("YGBOT_URL"):
            cfg.game_url = os.environ["YGBOT_URL"]
        if os.environ.get("CHROME_HOST"):
            cfg.chrome_host = os.environ["CHROME_HOST"]
        if os.environ.get("CHROME_PORT"):
            try:
                cfg.chrome_port = int(os.environ["CHROME_PORT"])
            except ValueError:
                pass
        if os.environ.get("OPPONENT"):
            cfg.opponent = os.environ["OPPONENT"]
        if os.environ.get("MAX_DUELS"):
            try:
                cfg.max_duels = int(os.environ["MAX_DUELS"])
            except ValueError:
                pass
        if os.environ.get("STRATEGY"):
            cfg.strategy = os.environ["STRATEGY"]
        if os.environ.get("GUARDIAN_STAR"):
            cfg.guardian_star = os.environ["GUARDIAN_STAR"]
        if os.environ.get("ACTION_DELAY"):
            try:
                cfg.action_delay = float(os.environ["ACTION_DELAY"])
            except ValueError:
                pass

        return cfg
