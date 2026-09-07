import json
import os
import base64


APP_NAME = "zhipu-usage-tray"
CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

PLATFORMS_CFG = {
    "zhipu": {
        "name": "智谱 (open.bigmodel.cn)",
    },
    "zai": {
        "name": "Z.ai (api.z.ai)",
    },
}

DEFAULT_CONFIG = {
    "api_key": "",
    "platform": "zhipu",
    "refresh_interval": 300,
}


def _encode(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _decode(text: str) -> str:
    return base64.b64decode(text.encode("ascii")).decode("utf-8")


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if cfg.get("api_key"):
                try:
                    cfg["api_key"] = _decode(cfg["api_key"])
                except Exception:
                    pass
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> bool:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        save_data = dict(cfg)
        if save_data.get("api_key"):
            save_data["api_key"] = _encode(save_data["api_key"])
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        return True
    except (OSError, IOError) as e:
        return False
