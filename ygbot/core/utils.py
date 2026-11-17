"""
Logging, console formatting, and timing utilities for YGBot.
"""

import sys
import time


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    DIM = '\033[2m'


def log(msg: str, level: str = "INFO"):
    timestamp = time.strftime("%H:%M:%S")
    prefix = ""
    if level == "INFO":
        prefix = f"{Colors.BLUE}[INFO]{Colors.END}"
    elif level == "SUCCESS":
        prefix = f"{Colors.GREEN}[SUCCESS]{Colors.END}"
    elif level == "WARN":
        prefix = f"{Colors.YELLOW}[WARN]{Colors.END}"
    elif level == "ERROR":
        prefix = f"{Colors.RED}[ERROR]{Colors.END}"
    elif level == "DUEL":
        prefix = f"{Colors.CYAN}[DUEL]{Colors.END}"
    elif level == "FUSION":
        prefix = f"{Colors.YELLOW}[FUSION]{Colors.END}"
    elif level == "COMBAT":
        prefix = f"{Colors.RED}[COMBAT]{Colors.END}"
    else:
        prefix = f"[{level}]"
    
    print(f"{Colors.DIM}{timestamp}{Colors.END} {prefix} {msg}")


def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}================================================================
   __   ______  ___       _   
   \\ \\ / / ___|| __ )  ___ | |_ 
    \\ V / |  _ |  _ \\ / _ \\| __|
     | || |_| || |_) | (_) | |_ 
     |_| \\____||____/ \\___/ \\__|
  Forbidden Memories Online - Autonomous Auto-Dueler Bot
================================================================{Colors.END}
"""
    print(banner)


def format_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"
