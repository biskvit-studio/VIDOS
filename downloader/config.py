import os
import json
from typing import Any, Dict, List

CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.vid_downloader_config.json')

def load_config() -> Dict[str, Any]:
    """Loads settings from a local JSON config file."""
    default_config = {
        "theme_dark": True,
        "language": "en",
        "download_dir": os.path.join(os.path.expanduser('~'), 'Downloads'),
        "download_history": []
    }
    
    if not os.path.exists(CONFIG_FILE):
        return default_config
        
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure fallback keys are populated
            for k, v in default_config.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return default_config

def save_config(config_data: Dict[str, Any]):
    """Saves settings to a local JSON config file."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def get_setting(key: str, default: Any = None) -> Any:
    """Gets a specific configuration setting."""
    config = load_config()
    return config.get(key, default)

def set_setting(key: str, value: Any):
    """Sets a specific configuration setting and persists it."""
    config = load_config()
    config[key] = value
    save_config(config)
