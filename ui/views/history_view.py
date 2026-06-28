import os
import subprocess
# pyrefly: ignore [missing-import]
import flet as ft
from ui.theme import ThemeColors
from ui.components import ShadcnCard, ShadcnButton, StatusBadge
from downloader import get_setting, set_setting, _

class HistoryView(ft.Column):
    """Displays previous downloads list with actions to clear history or view files."""
    def __init__(self, page: ft.Page, colors: ThemeColors):
        self.main_page = page
        self.colors = colors
        self.list_container = ft.ListView(spacing=10, expand=True, padding=ft.Padding(0, 0, 14, 0))
        
        # Header controls
        self.count_label = ft.Text(
            _("0 items downloaded"),
            size=14,
            color=colors.text_muted,
            font_family="Montserrat-Regular"
        )
        
        self.clear_btn = ShadcnButton(
            text=_("Clear History"),
            on_click=self._clear_history,
            colors=colors,
            is_primary=False,
            height=32
        )

        super().__init__(
            controls=[
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    _("Download History"),
                                    size=24,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.text_primary,
                                    font_family="Unbounded-Bold"
                                ),
                                self.count_label
                            ],
                            spacing=4
                        ),
                        self.clear_btn
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                ft.Container(height=20),
                ft.Container(
                    content=self.list_container,
                    expand=True
                )
            ],
            spacing=0,
            expand=True
        )

    def did_mount(self):
        self.load_history()

    def on_load(self):
        self.load_history()

    def load_history(self):
        """Loads and lists history entries from configuration."""
        self.list_container.controls.clear()
        
        # Load from config synchronously
        history = get_setting("download_history") or []
        
        if not history:
            self.count_label.value = _("No downloads recorded yet")
            self.clear_btn.visible = False
            self.list_container.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.HISTORY_ROUNDED, size=48, color=self.colors.text_muted),
                            ft.Text(
                                _("Your download history is empty"),
                                size=15,
                                weight=ft.FontWeight.W_500,
                                color=self.colors.text_muted,
                                font_family="Montserrat-Medium"
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12
                    ),
                    alignment=ft.alignment.Alignment(0, 0),
                    expand=True,
                    padding=40
                )
            )
        else:
            self.count_label.value = _("{} items downloaded").format(len(history))
            self.clear_btn.visible = True
            
            # Show items (newest first)
            for item in reversed(history):
                self.list_container.controls.append(self._create_history_row(item))
                
        try:
            self.count_label.update()
        except Exception:
            pass
        try:
            self.clear_btn.update()
        except Exception:
            pass
        try:
            self.list_container.update()
        except Exception:
            pass

    def _clear_history(self, e):
        set_setting("download_history", [])
        self.load_history()

    def _create_history_row(self, item: dict) -> ft.Container:
        title = item.get("title") or _("Unknown Title")
        url = item.get("url") or ""
        filepath = item.get("filepath") or ""
        timestamp = item.get("timestamp") or _("Just now")
        status = item.get("status") or "queued" # Use system status key
        
        file_exists = os.path.exists(filepath) if filepath else False
        
        actions = []
        if filepath and file_exists:
            actions.append(
                ShadcnButton(
                    text=_("Show in Folder"),
                    on_click=lambda _: self._reveal_file(filepath),
                    colors=self.colors,
                    is_primary=False,
                    height=32
                )
            )
        elif filepath:
            actions.append(
                ft.Text(
                    _("File moved or deleted"),
                    size=12,
                    color=self.colors.accent_red,
                    font_family="Montserrat-Regular",
                    italic=True
                )
            )

        row_content = ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(
                            title,
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=self.colors.text_primary,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            font_family="Montserrat-Medium"
                        ),
                        ft.Row(
                            [
                                ft.Text(timestamp, size=12, color=self.colors.text_muted, font_family="Montserrat-Regular"),
                                ft.Text("•", size=12, color=self.colors.text_muted),
                                ft.Text(
                                    url,
                                    size=12,
                                    color=self.colors.accent_blue,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    font_family="Montserrat-Regular",
                                    expand=True
                                )
                            ],
                            spacing=6,
                            expand=True
                        )
                    ],
                    expand=True,
                    spacing=4
                ),
                ft.Row(
                    [
                        StatusBadge(status, self.colors),
                        ft.Container(width=4),
                        *actions
                    ],
                    spacing=10
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        return ShadcnCard(content=row_content, colors=self.colors, padding=12)

    def _reveal_file(self, filepath: str):
        """Opens windows explorer and highlights the target file."""
        if os.path.exists(filepath):
            try:
                # Select the file in windows explorer
                subprocess.run(['explorer', '/select,', os.path.normpath(filepath)])
            except Exception as e:
                # Fallback to opening folder
                os.startfile(os.path.dirname(filepath))
