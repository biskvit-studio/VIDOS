# pyrefly: ignore [missing-import]
import flet as ft
from ui.theme import ThemeColors
from downloader import _



class ShadcnCard(ft.Container):
    """A generic styled card container with Shadcn borders and backgrounds."""
    def __init__(self, content: ft.Control, colors: ThemeColors, padding: float = 20, expand: bool = False, **kwargs):
        # super().__init__() FIRST — Flet 0.85 requires this
        super().__init__(
            content=content,
            bgcolor=colors.card,
            border=ft.Border.all(1, colors.border),
            border_radius=12,
            padding=padding,
            expand=expand,
            **kwargs
        )


class VideoMetadataCard(ShadcnCard):
    """Card displaying details of a resolved YouTube video."""
    def __init__(self, metadata: dict, colors: ThemeColors, format_dropdown: ft.Dropdown):
        # Duration formatter
        duration_sec = metadata.get('duration')
        if duration_sec:
            mins, secs = divmod(int(duration_sec), 60)
            hours, mins = divmod(mins, 60)
            duration_str = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins:02d}:{secs:02d}"
        else:
            duration_str = "Unknown"

        extractor = (metadata.get('extractor') or 'youtube').lower()
        is_vertical = extractor == 'tiktok'
        thumb_width = 90 if is_vertical else 180
        thumb_height = 135 if is_vertical else 100

        # Build platform brand badge
        badge_text = extractor.capitalize()
        if extractor == 'youtube':
            badge_bg = "#22FF0000"
            badge_fg = "#FF0000"
        elif extractor == 'vimeo':
            badge_bg = "#221AB7EA"
            badge_fg = "#1AB7EA"
        elif extractor == 'tiktok':
            badge_bg = "#2200F5FF"
            badge_fg = "#00F5FF"
            badge_text = "TikTok"
        else:
            badge_bg = "#22808080"
            badge_fg = colors.text_muted
            badge_text = "Web"

        platform_badge = ft.Container(
            content=ft.Text(badge_text, size=10, weight=ft.FontWeight.BOLD, color=badge_fg),
            bgcolor=badge_bg,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
            alignment=ft.alignment.center,
        )

        card_content = ft.Row(
            [
                # Thumbnail
                ft.Container(
                    content=ft.Image(
                        src=metadata.get('thumbnail') or "https://placehold.co/600x400/png",
                        fit=ft.BoxFit.COVER,
                        width=thumb_width,
                        height=thumb_height,
                        border_radius=8,
                    ),
                    border_radius=8,
                    border=ft.Border.all(1, colors.border),
                ),
                # Video Details
                ft.Column(
                    [
                        ft.Text(
                            metadata.get('title') or "Unknown Title",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=colors.text_primary,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            font_family="Unbounded-Bold",
                        ),
                        ft.Row(
                            [
                                platform_badge,
                                ft.Icon(ft.Icons.PERSON, size=14, color=colors.text_muted),
                                ft.Text(metadata.get('uploader', 'Unknown'), size=13, color=colors.text_muted),
                                ft.VerticalDivider(width=1, color=colors.border),
                                ft.Icon(ft.Icons.ACCESS_TIME, size=14, color=colors.text_muted),
                                ft.Text(duration_str, size=13, color=colors.text_muted),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=10,
                        ),
                        ft.Container(height=4),
                        ft.Row(
                            [
                                ft.Text(_("Quality:"), size=13, color=colors.text_muted),
                                ft.Container(content=format_dropdown, width=200),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=10,
                        ),
                    ],
                    expand=True,
                    spacing=6,
                )
            ],
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # super().__init__() FIRST
        super().__init__(content=card_content, colors=colors, padding=16)


class PlaylistItemRow(ft.Container):
    """A single row representation for checklist items in a playlist."""
    def __init__(self, entry: dict, colors: ThemeColors, on_change_callback):
        duration_sec = entry.get('duration')
        if duration_sec:
            mins, secs = divmod(int(duration_sec), 60)
            duration_str = f"{mins:02d}:{secs:02d}"
        else:
            duration_str = ""

        checkbox = ft.Checkbox(
            value=True,
            on_change=lambda e: on_change_callback(entry['playlist_index'], e.control.value),
            fill_color={
                ft.ControlState.SELECTED: colors.primary,
                ft.ControlState.DEFAULT: "transparent",
            },
            check_color=colors.on_primary,
            border_side=ft.BorderSide(1, colors.border),
        )

        # super().__init__() FIRST
        super().__init__(
            content=ft.Row(
                [
                    checkbox,
                    ft.Text(
                        f"{entry.get('playlist_index') or 1:02d}.",
                        size=14,
                        color=colors.text_muted,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Container(
                        content=ft.Image(
                            src=entry.get('thumbnail') or "https://placehold.co/120x90/png",
                            fit=ft.BoxFit.COVER,
                            width=64,
                            height=36,
                            border_radius=4,
                        ),
                        border_radius=4,
                        border=ft.Border.all(1, colors.border),
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                entry.get('title') or "Unknown Title",
                                size=14,
                                color=colors.text_primary,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                weight=ft.FontWeight.W_500,
                            ),
                            ft.Text(
                                duration_str,
                                size=12,
                                color=colors.text_muted,
                            )
                        ],
                        expand=True,
                        spacing=2,
                    )
                ],
                spacing=12,
            ),
            bgcolor=colors.card,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            border=ft.Border.all(1, colors.border),
        )

        # Store reference AFTER super().__init__()
        self.checkbox = checkbox
