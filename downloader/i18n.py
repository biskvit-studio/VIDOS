import os
import gettext
import logging
from typing import Dict
from downloader.config import get_setting

logger = logging.getLogger("vidos.i18n")

# Default language
DEFAULT_LANG = "en"

# List of supported languages and their human-readable labels
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "de": "Deutsch",
    "ru": "Русский",
    "fr": "Français",
    "es": "Español",
    "pt": "Português",
    "tr": "Türkçe",
    "id": "Bahasa Indonesia"
}

_translation = None

def init_translations():
    """Initializes the gettext translation catalog based on the user's config language setting."""
    global _translation
    
    # Load language from config, fallback to default English
    lang = get_setting("language", DEFAULT_LANG)
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANG
        
    # Resolve the absolute path to the 'locales' directory in the project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    locales_dir = os.path.normpath(os.path.join(current_dir, '../locales'))
    
    try:
        # Load translation catalog
        _translation = gettext.translation(
            'vidos',
            localedir=locales_dir,
            languages=[lang],
            fallback=True
        )
        logger.info(f"Loaded translation catalog for language: {lang}")
    except Exception as e:
        logger.error(f"Failed to load translations for {lang}, falling back to default strings. Error: {e}")
        _translation = gettext.NullTranslations()

def get_text(text: str) -> str:
    """Translates the input text using the currently loaded catalog."""
    global _translation
    if _translation is None:
        init_translations()
    return _translation.gettext(text)

# Standard alias for translation
_ = get_text
