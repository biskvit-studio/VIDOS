import os
import shutil
import logging
from typing import Optional, Tuple

logger = logging.getLogger("vidos.ffmpeg")

def get_ffmpeg_details() -> Tuple[Optional[str], str]:
    """
    Detects the location of the FFmpeg binary on the host system.
    Checks:
    1. System environment PATH (global installation)
    2. Bundled imageio-ffmpeg package (portable binary)

    Returns:
        Tuple[Optional[str], str]: (ffmpeg_path, source_description)
        Where source_description is one of: "System", "Bundled", or "Missing"
    """
    # 1. Check system path first
    system_path = shutil.which('ffmpeg')
    if system_path:
        logger.info(f"FFmpeg detected globally at: {system_path}")
        return system_path, "System"

    # 2. Check for imageio-ffmpeg bundled library
    try:
        # pyrefly: ignore [missing-import]
        import imageio_ffmpeg
        bundled_path = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled_path and os.path.exists(bundled_path):
            logger.info(f"FFmpeg detected inside virtual environment bundled path: {bundled_path}")
            return bundled_path, "Bundled"
    except ImportError:
        logger.warning("imageio-ffmpeg is not installed, unable to resolve bundled FFmpeg.")
    except Exception as e:
        logger.error(f"Error checking imageio-ffmpeg: {e}")

    logger.warning("FFmpeg binary could not be resolved on the system.")
    return None, "Missing"

def get_ffmpeg_path() -> Optional[str]:
    """Helper that returns just the FFmpeg path or None."""
    path, _ = get_ffmpeg_details()
    return path
