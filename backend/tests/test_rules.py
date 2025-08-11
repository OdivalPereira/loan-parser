import json
from importlib import reload
import backend.rules as rules

def test_classify_uses_config(tmp_path, monkeypatch):
    cfg = {
        "account_map": {"test": ["123", "321"]},
        "classify_rules": [{"keyword": "sample", "account": "test"}],
    }
    cfg_file = tmp_path / "cfg.json"
    cfg_file.write_text(json.dumps(cfg))

    monkeypatch.setenv("ACCOUNT_RULES_PATH", str(cfg_file))
    reload(rules)
    assert rules.classify("sample description") == ("123", "321")
    assert rules.classify("other") == ("000", "000")
