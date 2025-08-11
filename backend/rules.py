import json
import os
from typing import Tuple

CONFIG_PATH = os.environ.get(
    "ACCOUNT_RULES_PATH", os.path.join(os.path.dirname(__file__), "account_rules.json")
)

def load_config() -> dict:
    """Load classification rules from JSON configuration."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def classify(desc: str) -> Tuple[str, str]:
    """Classify a description using rules from configuration."""
    cfg = load_config()
    account_map = cfg.get("account_map", {})
    d = desc.lower()
    for rule in cfg.get("classify_rules", []):
        keyword = rule.get("keyword", "").lower()
        if keyword and keyword in d:
            accounts = account_map.get(rule.get("account"))
            if accounts:
                return tuple(accounts)
    return ("000", "000")
