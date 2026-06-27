import os
import time
import asyncio
import yt_dlp
from typing import Dict, Any, Callable, Optional
from .ffmpeg import get_ffmpeg_path



class DownloadCancelledException(Exception):
    """Custom exception to interrupt download process when cancelled."""
    pass


class DownloadEngine:
    @staticmethod
    def extract_metadata(url: str) -> Dict[str, Any]:
        """
        Extract metadata for a video or playlist without downloading.
        Returns a dictionary with parsed info.
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'skip_download': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            raise ValueError("Could not extract any information from the URL.")

        is_playlist = info.get('_type') == 'playlist' or 'entries' in info

        if is_playlist:
            entries = []
            for entry in info.get('entries', []):
                if not entry:
                    continue
                # yt-dlp flat extraction often puts thumbnails in a list instead of 'thumbnail'
                thumbnail_url = entry.get('thumbnail')
                if not thumbnail_url and entry.get('thumbnails'):
                    # Grab the last thumbnail (usually highest quality)
                    thumbnail_url = entry.get('thumbnails')[-1].get('url')
                    
                entries.append({
                    'title': entry.get('title') or 'Unknown Title',
                    'url': entry.get('url') or entry.get('webpage_url'),
                    'duration': entry.get('duration'),
                    'thumbnail': thumbnail_url,
                    'id': entry.get('id'),
                    'playlist_index': entry.get('playlist_index') or len(entries) + 1
                })
            return {
                'type': 'playlist',
                'title': info.get('title') or 'Unnamed Playlist',
                'url': url,
                'entries': entries,
                'thumbnail': info.get('thumbnails', [{}])[0].get('url') if info.get('thumbnails') else None
            }
        else:
            ydl_opts_full = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts_full) as ydl:
                full_info = ydl.extract_info(url, download=False)

            return {
                'type': 'video',
                'title': full_info.get('title') or 'Unknown Title',
                'url': url,
                'duration': full_info.get('duration'),
                'thumbnail': full_info.get('thumbnail'),
                'uploader': full_info.get('uploader') or 'Unknown Creator',
                'id': full_info.get('id'),
                'description': full_info.get('description', '')[:200]
            }

    @classmethod
    async def download(
        cls,
        url: str,
        download_dir: str,
        quality: str,
        is_audio: bool = False,
        audio_format: str = "mp3",
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        cancel_event: Optional[asyncio.Event] = None,
        filename_template: Optional[str] = None
    ) -> str:
        """
        Runs the yt-dlp download in a separate thread to avoid blocking Flet's event loop.

        Performance tuning applied:
        - concurrent_fragment_downloads=4: downloads up to 4 DASH/HLS segments simultaneously
        - buffersize=1MB: larger socket read buffer reduces syscall overhead
        - http_chunk_size=10MB: fewer HTTP range requests for fragmented formats
        - noresizebuffer=True: keeps the large buffer constant (prevents yt-dlp shrinking it)
        - retries/fragment_retries: lower than default to avoid stall on flaky segments
        - Progress hook throttled to 4 Hz max: prevents the UI round-trip from
          blocking yt-dlp's write loop (the single biggest hidden slowdown)
        """
        loop = asyncio.get_running_loop()

        # ── Performance-tuned yt-dlp base options ────────────────────────────
        ydl_opts = {
            'outtmpl': filename_template or os.path.join(download_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,

            # ── Concurrency & buffering ───────────────────────────────────────
            # Download up to 4 DASH/HLS fragments in parallel
            'concurrent_fragment_downloads': 4,
            # 1 MB socket read buffer — reduces syscall overhead on fast links
            'buffersize': 1024 * 1024,
            # 10 MB HTTP chunk size — fewer range requests per fragment
            'http_chunk_size': 10 * 1024 * 1024,
            # Don't let yt-dlp shrink the buffer back down automatically
            'noresizebuffer': True,

            # ── Network reliability ───────────────────────────────────────────
            'retries': 5,
            'fragment_retries': 5,
            'socket_timeout': 30,
            # Reuse TCP connections across requests (keep-alive)
            'keepalive': True,
        }

        # Resolve FFmpeg location (either system path or bundled package path)
        ffmpeg_path = get_ffmpeg_path()
        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = ffmpeg_path


        # ── Format selection ──────────────────────────────────────────────────
        if is_audio:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format,
                    'preferredquality': '192',
                }]
            })
        else:
            if quality == "1080p":
                ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]'
            elif quality == "720p":
                ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]'
            elif quality == "480p":
                ydl_opts['format'] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]'
            else:
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'

        # ── Multi-stream aware, throttled progress hook ───────────────────────
        # Two root causes of inaccurate progress:
        #
        # 1. Multi-stream downloads: yt-dlp downloads video + audio as separate
        #    streams sequentially. Each stream reports 0→100% independently, so
        #    naively the bar resets after the video stream finishes. We fix this
        #    by accumulating completed stream bytes and computing one combined %.
        #
        # 2. total_bytes_estimate is wildly inaccurate early in the download
        #    (can be 5-10× too large), causing "50% real → 10% shown". We fix
        #    this by only using total_bytes (exact, from Content-Length header)
        #    and falling back to the estimate ONLY as a last resort.

        _last_ui_update: float = 0.0
        _UI_UPDATE_INTERVAL = 0.25  # seconds → max 4 UI refreshes/second

        # Accumulated bytes from streams that have fully completed
        _completed_bytes: list = [0]
        # Remembered total of the most recently finished stream
        _last_stream_total: list = [0]

        def ydl_hook(d: Dict[str, Any]):
            nonlocal _last_ui_update

            # Cancellation check is always instant — no throttle
            if cancel_event and cancel_event.is_set():
                raise DownloadCancelledException("Download cancelled by user.")

            if not progress_callback:
                return

            status = d.get('status')

            if status == 'finished':
                # Stream completed — add its bytes to the running total so the
                # NEXT stream's progress is offset correctly (avoids the reset).
                finished_total = d.get('total_bytes') or _last_stream_total[0]
                _completed_bytes[0] += finished_total
                _last_stream_total[0] = 0
                # Always forward finished events immediately (they are rare)
                progress_callback({
                    'status': 'finished',
                    'percent': 100.0,
                    'filename': os.path.basename(d.get('filename', ''))
                })
                return

            if status != 'downloading':
                return

            # Throttle UI updates — prevents blocking yt-dlp's write loop
            now = time.monotonic()
            if now - _last_ui_update < _UI_UPDATE_INTERVAL:
                return
            _last_ui_update = now

            downloaded = d.get('downloaded_bytes') or 0

            # Prefer total_bytes (exact Content-Length) over estimate.
            # total_bytes_estimate is extremely unreliable at the start of a
            # stream — it can be 5-10× too large, causing "50% real → 10% shown".
            total = d.get('total_bytes') or 0
            if total == 0:
                # Only fall back to estimate if we have NO other information
                total = d.get('total_bytes_estimate') or 0

            _last_stream_total[0] = total  # remember for the finished event

            # Combined progress across all streams in this download
            overall_downloaded = _completed_bytes[0] + downloaded
            overall_total = _completed_bytes[0] + total

            if overall_total > 0:
                percent = min((overall_downloaded / overall_total) * 100, 99.9)
            else:
                percent = 0.0

            progress_callback({
                'status': 'downloading',
                'percent': percent,
                'downloaded_bytes': overall_downloaded,
                'total_bytes': overall_total,
                'speed': d.get('speed') or 0,
                'eta': d.get('eta') or 0,
                'filename': os.path.basename(d.get('filename', ''))
            })

        ydl_opts['progress_hooks'] = [ydl_hook]

        # ── Run blocking yt-dlp in a thread pool ──────────────────────────────
        def run_ydl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if 'requested_downloads' in info and len(info['requested_downloads']) > 0:
                    return info['requested_downloads'][0].get('filepath') or ''
                return ydl.prepare_filename(info)

        try:
            filepath = await loop.run_in_executor(None, run_ydl)
            return filepath
        except DownloadCancelledException:
            raise
        except Exception as e:
            raise e
