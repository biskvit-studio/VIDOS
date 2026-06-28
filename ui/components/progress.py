import os
import subprocess
import sys
import flet as ft
from ui.theme import ThemeColors
from downloader import _


def _resolve_status_style(status: str, colors: ThemeColors) -> tuple:
    """
    Returns (bg_color, text_color, label) for a given status string.
    Single source of truth — used by both StatusBadge.__init__ and update_badge().
    """
    status_norm = status.lower()
    if status_norm in ('downloading', 'processing'):
        bg = ft.Colors.with_opacity(0.1, colors.accent_blue)
        text_color = colors.accent_blue
        label = _("Downloading") if status_norm == 'downloading' else _("Processing")
    elif status_norm in ('finished', 'completed'):
        bg = ft.Colors.with_opacity(0.1, colors.accent_green)
        text_color = colors.accent_green
        label = _("Completed")
    elif status_norm in ('error', 'failed'):
        bg = ft.Colors.with_opacity(0.1, colors.accent_red)
        text_color = colors.accent_red
        label = _("Failed")
    elif status_norm == 'cancelled':
        bg = ft.Colors.with_opacity(0.1, colors.accent_orange)
        text_color = colors.accent_orange
        label = _("Cancelled")
    elif status_norm == 'queued':
        bg = colors.card_secondary
        text_color = colors.text_muted
        label = _("Queued")
    else:
        bg = colors.card_secondary
        text_color = colors.text_muted
        label = _(status.capitalize())
    return bg, text_color, label


class StatusBadge(ft.Container):
    """A pill badge representing the state of a download task."""
    def __init__(self, status: str, colors: ThemeColors):
        self._colors = colors
        self.current_status = status.lower()

        bg, text_color, label = _resolve_status_style(status, colors)

        self._badge_text = ft.Text(
            label,
            size=11,
            weight=ft.FontWeight.BOLD,
            color=text_color,
            font_family="Montserrat-Medium",
        )

        # super().__init__() called FIRST before any self.* assignments
        super().__init__(
            content=self._badge_text,
            bgcolor=bg,
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
            alignment=ft.alignment.Alignment(0, 0),
        )

    def update_badge(self, status: str):
        """Mutate badge appearance in-place without creating new objects."""
        self.current_status = status.lower()
        bg, text_color, label = _resolve_status_style(status, self._colors)
        self.bgcolor = bg
        self._badge_text.value = label
        self._badge_text.color = text_color


def _open_file(filepath: str):
    """Cross-platform: open the file in the user's default media player."""
    try:
        if sys.platform == 'win32':
            os.startfile(filepath)
        elif sys.platform == 'darwin':
            subprocess.run(['open', filepath], check=False)
        else:
            subprocess.run(['xdg-open', filepath], check=False)
    except Exception:
        pass


class DownloadProgressBar(ft.Container):
    """A comprehensive download status progress card."""
    def __init__(self, title: str, colors: ThemeColors, on_cancel=None):
        # Build all child controls as local variables first
        title_label = ft.Text(
            title,
            size=14,
            weight=ft.FontWeight.W_600,
            color=colors.text_primary,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            font_family="Montserrat-Medium",
            expand=True
        )

        percent_label = ft.Text(
            "0%",
            size=13,
            weight=ft.FontWeight.BOLD,
            color=colors.text_primary,
            font_family="Unbounded-Bold"
        )

        progress_bar = ft.ProgressBar(
            value=0.0,
            color=colors.primary if colors.is_dark else colors.primary_hover,
            bgcolor=colors.border,
            height=4,
            border_radius=2,
        )

        stats_label = ft.Text(
            _("Waiting in queue..."),
            size=12,
            color=colors.text_muted,
            font_family="Montserrat-Regular"
        )

        # 'badge' is reserved by Flet — use 'status_badge' instead
        status_badge = StatusBadge("queued", colors)

        cancel_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=16,
            icon_color=colors.text_muted,
            tooltip=_("Cancel Download"),
            on_click=lambda _: on_cancel() if on_cancel else None,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=4,
            )
        )

        # "Open File" button — hidden until download completes successfully.
        # Uses ft.Container (like ShadcnButton) instead of ft.TextButton which
        # does not support the 'text' keyword argument in Flet 0.85.
        open_file_btn_text = ft.Text(
            _("Open File"),
            size=12,
            color=colors.accent_blue,
            font_family="Montserrat-Medium",
        )
        open_file_btn = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.FOLDER_OPEN_OUTLINED, size=14, color=colors.accent_blue),
                    open_file_btn_text,
                ],
                spacing=4,
                tight=True,
            ),
            visible=False,
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_radius=6,
            border=ft.Border.all(1, colors.accent_blue),
            ink=True,
            on_click=None,  # Wired up in set_status() when filepath is known
        )

        content_layout = ft.Column(
            [
                ft.Row(
                    [
                        title_label,
                        status_badge,
                        open_file_btn,
                        cancel_btn
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                ft.Container(height=2),
                ft.Row(
                    [
                        ft.Container(content=progress_bar, expand=True),
                        ft.Container(width=8),
                        percent_label
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                stats_label
            ],
            spacing=6
        )

        # super().__init__() called FIRST — Flet requires this before ANY self.* assignments
        super().__init__(
            content=content_layout,
            bgcolor=colors.card,
            border=ft.Border.all(1, colors.border),
            border_radius=10,
            padding=14,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
        )

        # Store references AFTER super().__init__() so _values exists
        self._colors = colors
        self._on_cancel = on_cancel
        self._title_label = title_label
        self._percent_label = percent_label
        self._progress_bar = progress_bar
        self._stats_label = stats_label
        self._status_badge = status_badge  # NOT self.badge — that's reserved by Flet
        self._cancel_btn = cancel_btn
        self._open_file_btn = open_file_btn
        self._open_file_btn_text = open_file_btn_text

    def trigger_cancel(self):
        if self._on_cancel:
            self._on_cancel()

    def update_progress(self, percent: float, speed: float, eta: float, downloaded: float, total: float):
        """Updates the visual state of the progress bar with raw metrics."""
        self._progress_bar.value = percent / 100.0
        self._percent_label.value = f"{int(percent)}%"

        # Format speed
        if speed > 1024 * 1024:
            speed_str = f"{speed / (1024 * 1024):.1f} MB/s"
        elif speed > 1024:
            speed_str = f"{speed / 1024:.1f} KB/s"
        else:
            speed_str = f"{speed:.0f} B/s"

        # Format ETA
        if eta > 0:
            mins, secs = divmod(int(eta), 60)
            hours, mins = divmod(mins, 60)
            eta_str = _("ETA: {}").format(f"{hours:02d}:{mins:02d}:{secs:02d}") if hours > 0 else _("ETA: {}").format(f"{mins:02d}:{secs:02d}")
        else:
            eta_str = _("ETA: --:--")

        # Format sizes
        downloaded_mb = downloaded / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        if total > 0:
            size_str = _("{} / {}").format(f"{downloaded_mb:.1f} MB", f"{total_mb:.1f} MB")
        else:
            size_str = _("{} downloaded").format(f"{downloaded_mb:.1f} MB")

        self._stats_label.value = f"{speed_str}  •  {eta_str}  •  {size_str}"

        # Update badge to "Downloading" if not already
        try:
            if self._status_badge.current_status != "downloading":
                self._status_badge.update_badge("Downloading")
        except Exception:
            pass

        try:
            self.update()
        except Exception:
            pass

    def set_status(self, status: str, filepath: str = ""):
        """
        Updates status badge and control states for terminal download states.
        filepath: when provided on completion, wires up the Open File button.
        """
        try:
            self._status_badge.update_badge(status)
        except Exception:
            pass

        status_norm = status.lower()
        if status_norm in ('finished', 'completed'):
            self._progress_bar.value = 1.0
            self._percent_label.value = "100%"
            self._stats_label.value = _("Download completed successfully.")
            self._cancel_btn.visible = False
            # Show "Open File" button when a valid filepath is available
            if filepath and os.path.exists(filepath):
                self._open_file_btn.on_click = lambda evt: _open_file(filepath)
                self._open_file_btn.visible = True
        elif status_norm == 'cancelled':
            self._stats_label.value = _("Download cancelled by user.")
            self._cancel_btn.visible = False
            self._progress_bar.value = 0.0
        elif status_norm in ('error', 'failed'):
            self._stats_label.value = _("An error occurred during download.")
            self._cancel_btn.visible = False
            self._progress_bar.value = 0.0
        elif status_norm == 'processing':
            self._stats_label.value = _("Extracting audio/merging streams. Please wait...")
            self._progress_bar.value = None  # Indeterminate
            self._percent_label.value = "..."

        try:
            self.update()
        except Exception:
            pass
