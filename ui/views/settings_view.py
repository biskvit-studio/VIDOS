import os
import logging
import shutil
import asyncio
# pyrefly: ignore [missing-import]
import flet as ft
from ui.theme import ThemeColors
from ui.components import ShadcnCard, ShadcnButton, ShadcnTextField, StatusBadge
from downloader import get_setting, set_setting, get_ffmpeg_details, _

logger = logging.getLogger("vidos.settings")


class SettingsView(ft.ListView):
    """Settings screen allowing directory changes, language toggling, and displaying system status."""
    def __init__(self, page: ft.Page, colors: ThemeColors, on_language_change=None):
        self.main_page = page
        self.colors = colors
        self._on_language_change_callback = on_language_change

        # Load directories synchronously from config helper
        self.download_dir = get_setting("download_dir")

        # Flet 0.85: FilePicker is a Service — no overlay, no on_result callback.
        # Register it as a page service; get_directory_path() is async and returns path directly.
        self.dir_picker = ft.FilePicker()

        # UI Elements
        self.dir_input = ShadcnTextField(
            colors=colors,
            value=self.download_dir,
            expand=True,
            read_only=True
        )

        self.ffmpeg_badge = StatusBadge("checking", colors)

        # Directory configuration section
        dir_section = ShadcnCard(
            content=ft.Column(
                [
                    ft.Text(
                        _("Download Directory"),
                        size=15,
                        weight=ft.FontWeight.W_600,
                        color=colors.text_primary,
                        font_family="Montserrat-Medium"
                    ),
                    ft.Text(
                        _("Select the default folder where downloaded media files will be saved."),
                        size=13,
                        color=colors.text_muted,
                        font_family="Montserrat-Regular"
                    ),
                    ft.Container(height=6),
                    ft.Row(
                        [
                            self.dir_input,
                            ShadcnButton(
                                text=_("Browse"),
                                on_click=lambda _: page.run_task(self._browse_directory),
                                colors=colors,
                                is_primary=False
                            )
                        ],
                        spacing=10
                    )
                ],
                spacing=8
            ),
            colors=colors
        )

        # App Language configuration section
        current_lang = get_setting("language", "en")
        self.lang_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(key="en", text="English"),
                ft.dropdown.Option(key="de", text="Deutsch"),
                ft.dropdown.Option(key="ru", text="Русский"),
                ft.dropdown.Option(key="fr", text="Français"),
                ft.dropdown.Option(key="es", text="Español"),
                ft.dropdown.Option(key="pt", text="Português"),
                ft.dropdown.Option(key="tr", text="Türkçe"),
                ft.dropdown.Option(key="id", text="Bahasa Indonesia"),
            ],
            value=current_lang,
            width=200,
            text_size=13,
            color=colors.text_primary,
            border_color=colors.border,
            bgcolor=colors.card,
            focused_border_color=colors.text_primary,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=0),
            on_select=self._on_language_changed,
        )

        lang_section = ShadcnCard(
            content=ft.Column(
                [
                    ft.Text(
                        _("App Language"),
                        size=15,
                        weight=ft.FontWeight.W_600,
                        color=colors.text_primary,
                        font_family="Montserrat-Medium"
                    ),
                    ft.Text(
                        _("Change application interface language."),
                        size=13,
                        color=colors.text_muted,
                        font_family="Montserrat-Regular"
                    ),
                    ft.Container(height=6),
                    ft.Row(
                        [
                            self.lang_dropdown
                        ],
                        spacing=10
                    )
                ],
                spacing=8
            ),
            colors=colors
        )

        # System requirements section (FFmpeg detection)
        sys_section = ShadcnCard(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                _("System Requirements"),
                                size=15,
                                weight=ft.FontWeight.W_600,
                                color=colors.text_primary,
                                font_family="Montserrat-Medium"
                            ),
                            self.ffmpeg_badge
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Text(
                        _("This tool must be installed to help process and download your media files."),
                        size=13,
                        color=colors.text_muted,
                        font_family="Montserrat-Regular"
                    )
                ],
                spacing=8
            ),
            colors=colors
        )

        super().__init__(
            controls=[
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    _("Settings"),
                                    size=24,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.text_primary,
                                    font_family="Unbounded-Bold"
                                ),
                                ft.Text(
                                    _("Configure application settings and dependencies."),
                                    size=14,
                                    color=colors.text_muted,
                                    font_family="Montserrat-Regular"
                                )
                            ],
                            spacing=4
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Container(height=16),
                dir_section,
                ft.Container(height=10),
                lang_section,
                ft.Container(height=10),
                sys_section
            ],
            spacing=0,
            expand=True,
            padding=ft.Padding(0, 0, 14, 0)
        )

    def did_mount(self):
        # Register the FilePicker service now that the page is live
        try:
            self.main_page.services.register(self.dir_picker)
        except Exception:
            pass
        # Initialize requirements check asynchronously
        self.main_page.run_task(self._check_system_dependencies)

    def on_load(self):
        # Refresh values
        self.download_dir = get_setting("download_dir")
        self.dir_input.value = self.download_dir
        try:
            self.dir_input.update()
        except Exception:
            pass
        
        # Refresh selected language
        self.lang_dropdown.value = get_setting("language", "en")
        try:
            self.lang_dropdown.update()
        except Exception:
            pass

        self.main_page.run_task(self._check_system_dependencies)

    async def _browse_directory(self):
        """Opens directory picker dialog and updates path if user selects one."""
        try:
            path = await self.dir_picker.get_directory_path(
                dialog_title=_("Select Download Folder"),
                initial_directory=self.download_dir
            )
            if path:
                self.download_dir = path
                self.dir_input.value = path
                try:
                    self.dir_input.update()
                except Exception:
                    pass
                set_setting("download_dir", path)
        except Exception:
            pass

    async def _check_system_dependencies(self):
        """Asynchronously check if FFmpeg executable is available (System or Bundled)."""
        loop = asyncio.get_running_loop()
        ffmpeg_path, source = await loop.run_in_executor(None, get_ffmpeg_details)

        if source == "System":
            self.ffmpeg_badge.content.value = _("FFmpeg Detected (System)")
            self.ffmpeg_badge.bgcolor = ft.Colors.with_opacity(0.1, self.colors.accent_green)
            self.ffmpeg_badge.content.color = self.colors.accent_green
        elif source == "Bundled":
            self.ffmpeg_badge.content.value = _("FFmpeg Detected (Bundled)")
            self.ffmpeg_badge.bgcolor = ft.Colors.with_opacity(0.1, self.colors.accent_green)
            self.ffmpeg_badge.content.color = self.colors.accent_green
        else:
            self.ffmpeg_badge.content.value = _("FFmpeg Missing")
            self.ffmpeg_badge.bgcolor = ft.Colors.with_opacity(0.1, self.colors.accent_red)
            self.ffmpeg_badge.content.color = self.colors.accent_red
        try:
            self.ffmpeg_badge.update()
        except Exception:
            pass

    def _on_language_changed(self, e):
        """Saves selected language and triggers app-wide rebuild to apply translations."""
        # In Flet 0.85+, the Dropdown uses on_select; value is on e.control.value
        new_lang = e.control.value
        logger.info(f"Language selection event fired. New value: {new_lang!r}")
        if not new_lang:
            logger.warning("Received empty language value, ignoring.")
            return
        try:
            set_setting("language", new_lang)
            logger.info(f"Saved setting 'language' = {new_lang!r}")
            if self._on_language_change_callback:
                logger.info("Dispatching rebuild_app via page.run_task...")
                # Use page.run_task to safely dispatch into the async event loop
                self.main_page.run_task(self._trigger_rebuild)
            else:
                logger.warning("on_language_change_callback is None — cannot rebuild.")
        except Exception as ex:
            logger.error(f"Error in _on_language_changed: {ex}", exc_info=True)

    async def _trigger_rebuild(self):
        """Async trampoline that dispatches the sync rebuild callback safely."""
        try:
            self._on_language_change_callback()
            logger.info("rebuild_app completed.")
        except Exception as ex:
            logger.error(f"Error in _trigger_rebuild: {ex}", exc_info=True)
