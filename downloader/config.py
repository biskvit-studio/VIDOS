import os
import json
from typing import Any, Dict, Optional

CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.vid_downloader_config.json')

# In-memory cache — avoids reading the disk on every get_setting() call.
# Invalidated on every save_config() so it always stays in sync.
_config_cache: Optional[Dict[str, Any]] = None

_DEFAULT_CONFIG: Dict[str, Any] = {
    "theme_dark": True,
    "language": "en",
    "download_dir": os.path.join(os.path.expanduser('~'), 'Downloads'),
    "download_history": []
}

def load_config() -> Dict[str, Any]:
    """Loads settings from the in-memory cache, falling back to disk when cold."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if not os.path.exists(CONFIG_FILE):
        _config_cache = dict(_DEFAULT_CONFIG)
        return _config_cache

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure any new default keys are populated
            for k, v in _DEFAULT_CONFIG.items():
                if k not in data:
                    data[k] = v
            _config_cache = data
            return _config_cache
    except Exception:
        _config_cache = dict(_DEFAULT_CONFIG)
        return _config_cache

def save_config(config_data: Dict[str, Any]):
    """Saves settings to disk and updates the in-memory cache."""
    global _config_cache
    _config_cache = config_data  # Keep cache in sync immediately
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def get_setting(key: str, default: Any = None) -> Any:
    """Gets a specific configuration setting (served from cache)."""
    config = load_config()
    return config.get(key, default)

def set_setting(key: str, value: Any):
    """Sets a specific configuration setting and persists it."""
    config = load_config()
    config[key] = value
    save_config(config)
