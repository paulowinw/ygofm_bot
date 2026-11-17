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


def format_cards_table(cards: list) -> str:
    """Formats a list of hand Card objects, dicts, or card names into a formatted terminal table."""
    if not cards:
        return "(No cards in hand)"

    headers = ["Slot", "Card Name", "Type", "ATK", "DEF", "Guardian Star"]
    rows = []
    for idx, c in enumerate(cards):
        if isinstance(c, str):
            slot = str(idx + 1)
            name = c
            ctype_str = "Monster"
            atk = "--"
            def_ = "--"
            star = "--"
        elif isinstance(c, dict):
            slot = str(c.get("slot", idx + 1))
            name = str(c.get("name", "Unknown"))
            ctype_str = str(c.get("type", "Monster"))
            atk = str(c.get("atk", "--"))
            def_ = str(c.get("def", "--"))
            star = str(c.get("star", "--"))
        else:
            slot = str(getattr(c, "index", -1) + 1) if getattr(c, "index", -1) >= 0 else str(idx + 1)
            name = getattr(c, "name", "Unknown")
            card_type = getattr(c, "card_type", None)
            ctype_str = card_type.value if hasattr(card_type, "value") else str(card_type or "Unknown")

            if getattr(c, "is_monster", False):
                atk = str(getattr(c, "atk", 1000))
                def_ = str(getattr(c, "def_", 1000))
                p_star = getattr(c, "guardian_star_primary", None)
                s_star = getattr(c, "guardian_star_secondary", None)
                if p_star and s_star:
                    star = f"{p_star} / {s_star}"
                elif p_star:
                    star = p_star
                else:
                    star = "Sun / Moon"
            elif getattr(c, "is_equip", False):
                atk = f"+{getattr(c, 'buff', 500)}"
                def_ = "--"
                targets = getattr(c, "target_types", [])
                star = ", ".join(targets) if targets else "Universal"
            else:
                atk = "--"
                def_ = "--"
                star = "--"

        rows.append([slot, name, ctype_str, atk, def_, star])

    # Sort table rows in ascending order by slot number (Slot 1 to 5)
    def _slot_sort_key(row):
        try:
            return int(row[0])
        except (ValueError, TypeError):
            return 999

    rows.sort(key=_slot_sort_key)

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))

    def make_line(cols, left="│", mid="│", right="│"):
        padded = [f" {c.ljust(col_widths[i])} " for i, c in enumerate(cols)]
        return f"{left}{mid.join(padded)}{right}"

    top_border = f"┌{'┬'.join('─' * (w + 2) for w in col_widths)}┐"
    mid_border = f"├{'┼'.join('─' * (w + 2) for w in col_widths)}┤"
    bot_border = f"└{'┴'.join('─' * (w + 2) for w in col_widths)}┘"

    table_lines = [
        f"{Colors.CYAN}{top_border}{Colors.END}",
        f"{Colors.CYAN}{make_line(headers)}{Colors.END}",
        f"{Colors.CYAN}{mid_border}{Colors.END}",
    ]
    for row in rows:
        table_lines.append(f"{Colors.BOLD}{make_line(row)}{Colors.END}")
    table_lines.append(f"{Colors.CYAN}{bot_border}{Colors.END}")

    return "\n".join(table_lines)


def print_cards_table(cards: list, title: str = "CARDS IN HAND"):
    """Prints a styled card table to stdout."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}=== [ {title} ] ==={Colors.END}")
    print(format_cards_table(cards))
    print()

