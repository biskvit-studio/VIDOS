import os
import datetime
import asyncio
# pyrefly: ignore [missing-import]
import flet as ft
from ui.theme import ThemeColors
from ui.components import (
    ShadcnButton,
    ShadcnTextField,
    ShadcnCard,
    VideoMetadataCard,
    PlaylistItemRow,
    DownloadProgressBar,
    StatusBadge
)
from downloader import DownloadEngine, DownloadCancelledException, get_setting, set_setting, _

class DownloadView(ft.ListView):
    """Main view for parsing links and monitoring active downloads."""
    def __init__(self, page: ft.Page, colors: ThemeColors, app_layout=None):
        self.main_page = page
        self.colors = colors
        self.app_layout = app_layout
        
        # State tracking
        self.current_metadata = None
        self.selected_playlist_indices = set()
        self.active_cancels = {} # Task ID -> asyncio.Event
        
        # Inputs & Controllers
        self.url_input = ShadcnTextField(
            colors=colors,
            hint_text=_("Paste video or playlist link..."),
            expand=True,
            on_submit=self._on_parse_clicked
        )
        
        self.parse_btn = ShadcnButton(
            text=_("Analyze"),
            on_click=self._on_parse_clicked,
            colors=colors,
            is_primary=True,
        )
        
        self.loading_spinner = ft.ProgressRing(width=20, height=20, stroke_width=2.5, color=colors.primary)
        self.loading_text = ft.Text(_("Analyzing URL..."), size=13, color=colors.text_muted, font_family="Montserrat-Regular")
        self.loading_row = ft.Row([self.loading_spinner, self.loading_text], visible=False, alignment=ft.MainAxisAlignment.CENTER)
        
        # Result Containers
        self.metadata_container = ft.Container(expand=True)
        self.active_downloads_container = ft.Column(spacing=10)
        
        super().__init__(
            controls=[
                ft.Text(
                    _("Download"),
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=colors.text_primary,
                    font_family="Unbounded-Bold"
                ),
                ft.Text(
                    _("Download single videos or full playlists in high quality."),
                    size=14,
                    color=colors.text_muted,
                    font_family="Montserrat-Regular"
                ),
                ft.Container(height=20),
                # Input Row
                ft.Row(
                    [
                        self.url_input,
                        self.parse_btn
                    ],
                    spacing=10,
                ),
                ft.Container(height=10),
                self.loading_row,
                ft.Container(height=10),
                # Dynamic content area
                self.metadata_container,
                ft.Container(height=20),
                # Active downloads section
                ft.Text(
                    _("Active Downloads"),
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=colors.text_primary,
                    font_family="Montserrat-Medium"
                ),
                ft.Divider(height=1, color=colors.border),
                ft.Container(height=8),
                self.active_downloads_container
            ],
            spacing=0,
            expand=True,
            padding=ft.Padding(0, 0, 14, 0)
        )

    def on_load(self):
        # View refresh hook
        pass

    async def _on_parse_clicked(self, e):
        url = self.url_input.value.strip()
        if not url:
            self._show_snackbar(_("Please enter a valid URL."), self.colors.accent_red)
            return

        # Show loading spinner
        self.parse_btn.set_disabled(True)
        self.url_input.disabled = True
        self.url_input.update()
        self.loading_row.visible = True
        self.loading_row.update()
        self.metadata_container.content = None
        self.metadata_container.update()

        try:
            # Run metadata extraction in background
            loop = asyncio.get_running_loop()
            metadata = await loop.run_in_executor(None, DownloadEngine.extract_metadata, url)
            
            self.current_metadata = metadata
            self._render_metadata_card()
        except Exception as ex:
            self._show_snackbar(_("Failed to analyze URL: {}").format(str(ex)), self.colors.accent_red)
        finally:
            self.loading_row.visible = False
            self.loading_row.update()
            self.parse_btn.set_disabled(False)
            self.url_input.disabled = False
            self.url_input.update()

    def _render_metadata_card(self):
        meta = self.current_metadata
        if not meta:
            return

        # Shared Dropdown style
        format_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("1080p", _("1080p (Best MP4)")),
                ft.dropdown.Option("720p", _("720p (HD MP4)")),
                ft.dropdown.Option("480p", _("480p (SD MP4)")),
                ft.dropdown.Option("mp3", _("Audio Only (MP3)")),
                ft.dropdown.Option("m4a", _("Audio Only (M4A)")),
            ],
            value="1080p",
            width=200,
            height=40,
            text_size=13,
            color=self.colors.text_primary,
            border_color=self.colors.border,
            bgcolor=self.colors.card,
            focused_border_color=self.colors.text_primary,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=0),
        )

        if meta['type'] == 'video':
            # Single Video View
            download_btn = ShadcnButton(
                text=_("Start Download"),
                on_click=lambda _: self._start_video_download(meta, format_dropdown.value),
                colors=self.colors,
                is_primary=True,
                height=40
            )

            card = VideoMetadataCard(meta, self.colors, format_dropdown)
            
            layout = ft.Column(
                [
                    card,
                    ft.Container(height=10),
                    ft.Row([download_btn], alignment=ft.MainAxisAlignment.END)
                ],
                spacing=0
            )
            self.metadata_container.content = layout

        else:
            # Playlist View
            self.selected_playlist_indices = {entry['playlist_index'] for entry in meta['entries']}
            
            # Store references so we can update them without index traversal
            self._select_all_cb = ft.Checkbox(
                label=_("Select All Videos"),
                value=True,
                on_change=self._on_select_all_changed,
                fill_color={
                    ft.ControlState.SELECTED: self.colors.primary,
                    ft.ControlState.DEFAULT: "transparent",
                },
                check_color=self.colors.on_primary,
                border_side=ft.BorderSide(1, self.colors.border),
            )
            select_all_cb = self._select_all_cb

            # Playlist checklist rows
            # max_height was removed in Flet 0.85 — wrap in Container with height instead
            self.playlist_rows = ft.ListView(spacing=6, padding=ft.Padding(0, 0, 14, 0))
            self._playlist_rows_container = ft.Container(
                content=self.playlist_rows,
                height=250,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            )
            for entry in meta['entries']:
                row = PlaylistItemRow(entry, self.colors, self._on_playlist_item_changed)
                self.playlist_rows.controls.append(row)

            # Playlist details header
            details_header = ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                meta['title'],
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=self.colors.text_primary,
                                font_family="Unbounded-Bold"
                            ),
                            ft.Text(
                                _("{} Videos Available").format(len(meta['entries'])),
                                size=13,
                                color=self.colors.text_muted,
                                font_family="Montserrat-Regular"
                            )
                        ],
                        spacing=2,
                        expand=True
                    ),
                    ft.Row(
                        [
                            ft.Text(_("Quality:"), size=13, color=self.colors.text_muted),
                            format_dropdown,
                        ],
                        spacing=10
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )

            self._playlist_download_btn = ShadcnButton(
                text=_("Download Selected ({})").format(len(self.selected_playlist_indices)),
                on_click=lambda _: self._start_playlist_download(meta, format_dropdown.value),
                colors=self.colors,
                is_primary=True,
                height=40
            )
            download_btn = self._playlist_download_btn

            playlist_card = ShadcnCard(
                content=ft.Column(
                    [
                        details_header,
                        ft.Divider(height=16, color=self.colors.border),
                        select_all_cb,
                        ft.Container(height=6),
                        self._playlist_rows_container,
                        ft.Container(height=10),
                        ft.Row([download_btn], alignment=ft.MainAxisAlignment.END)
                    ],
                    spacing=0
                ),
                colors=self.colors
            )
            
            self.metadata_container.content = playlist_card
            
        self.metadata_container.update()

    def _on_select_all_changed(self, e):
        meta = self.current_metadata
        if not meta or 'entries' not in meta:
            return
            
        is_checked = e.control.value
        if is_checked:
            self.selected_playlist_indices = {entry['playlist_index'] for entry in meta['entries']}
        else:
            self.selected_playlist_indices.clear()
            
        # Update row checkboxes visual state
        for row in self.playlist_rows.controls:
            row.checkbox.value = is_checked
            try:
                row.checkbox.update()
            except Exception:
                pass

        # Update button text count
        self._update_playlist_btn_label()

    def _on_playlist_item_changed(self, index: int, checked: bool):
        if checked:
            self.selected_playlist_indices.add(index)
        else:
            self.selected_playlist_indices.discard(index)
            
        # Update select-all state using stored reference (not fragile index traversal)
        if hasattr(self, '_select_all_cb'):
            self._select_all_cb.value = len(self.selected_playlist_indices) == len(self.current_metadata['entries'])
            try:
                self._select_all_cb.update()
            except Exception:
                pass
        
        self._update_playlist_btn_label()

    def _update_playlist_btn_label(self):
        # Use stored reference (not fragile hardcoded index traversal)
        if hasattr(self, '_playlist_download_btn'):
            self._playlist_download_btn.text_control.value = _("Download Selected ({})").format(len(self.selected_playlist_indices))
            try:
                self._playlist_download_btn.update()
            except Exception:
                pass

    def _start_video_download(self, meta: dict, quality: str):
        # Create unique task ID
        task_id = f"video_{meta['id']}_{int(datetime.datetime.now().timestamp())}"
        cancel_event = asyncio.Event()
        self.active_cancels[task_id] = cancel_event

        download_dir = get_setting("download_dir") or os.path.join(os.path.expanduser('~'), 'Downloads')
        is_audio = quality in ('mp3', 'm4a')

        # Add ProgressBar component
        bar = DownloadProgressBar(
            title=meta['title'],
            colors=self.colors,
            on_cancel=lambda: self._cancel_download(task_id)
        )
        self.active_downloads_container.controls.append(bar)
        self.active_downloads_container.update()

        # Trigger download in Flet's background loop
        self.main_page.run_task(
            self._download_worker,
            task_id,
            meta['url'],
            download_dir,
            quality,
            is_audio,
            bar,
            meta['title']
        )
        
        self._show_snackbar(_("Download task added to queue."), self.colors.accent_blue)

    def _start_playlist_download(self, meta: dict, quality: str):
        if not self.selected_playlist_indices:
            self._show_snackbar(_("No videos selected."), self.colors.accent_red)
            return

        # Fetch selected entries
        selected_entries = [entry for entry in meta['entries'] if entry['playlist_index'] in self.selected_playlist_indices]
        download_dir = get_setting("download_dir") or os.path.join(os.path.expanduser('~'), 'Downloads')
        
        # Organize playlist files into subfolder
        playlist_name = meta['title']
        # Clean folder name
        safe_playlist_name = "".join([c for c in playlist_name if c.isalpha() or c.isdigit() or c in ' -_']).strip()
        playlist_dir = os.path.join(download_dir, safe_playlist_name)

        # Trigger the sequential playlist download in background task
        self.main_page.run_task(
            self._playlist_downloader_task,
            selected_entries,
            playlist_dir,
            quality
        )
        
        self._show_snackbar(_("Starting playlist download ({} items).").format(len(selected_entries)), self.colors.accent_blue)

    async def _playlist_downloader_task(self, entries: list, download_dir: str, quality: str):
        os.makedirs(download_dir, exist_ok=True)
        is_audio = quality in ('mp3', 'm4a')

        for idx, entry in enumerate(entries):
            task_id = f"playlist_{entry['id']}_{int(datetime.datetime.now().timestamp())}"
            cancel_event = asyncio.Event()
            self.active_cancels[task_id] = cancel_event

            # Format prefix index (e.g. 01 - title.mp4)
            prefix = f"{entry['playlist_index']:02d} - "
            filename_template = os.path.join(download_dir, f"{prefix}%(title)s.%(ext)s")

            bar = DownloadProgressBar(
                title=f"[{idx+1}/{len(entries)}] {entry['title']}",
                colors=self.colors,
                on_cancel=lambda t=task_id: self._cancel_download(t)
            )
            
            self.active_downloads_container.controls.append(bar)
            self.active_downloads_container.update()

            await self._download_worker(
                task_id,
                entry['url'],
                download_dir,
                quality,
                is_audio,
                bar,
                entry['title'],
                filename_template
            )

    async def _download_worker(
        self,
        task_id: str,
        url: str,
        download_dir: str,
        quality: str,
        is_audio: bool,
        bar: DownloadProgressBar,
        title: str,
        filename_template: str = None
    ):
        cancel_event = self.active_cancels[task_id]
        
        def handle_progress(d):
            # Safe progress updater callable by yt-dlp threads
            status = d.get('status')
            if status == 'downloading':
                bar.update_progress(
                    percent=d.get('percent', 0.0),
                    speed=d.get('speed', 0.0),
                    eta=d.get('eta', 0.0),
                    downloaded=d.get('downloaded_bytes', 0.0),
                    total=d.get('total_bytes', 0.0)
                )
            elif status == 'finished':
                # Processing: merging files or audio extraction
                bar.set_status("processing")

        try:
            # Execute engine download coroutine
            filepath = await DownloadEngine.download(
                url=url,
                download_dir=download_dir,
                quality=quality,
                is_audio=is_audio,
                audio_format=quality if is_audio else "mp3",
                progress_callback=handle_progress,
                cancel_event=cancel_event,
                filename_template=filename_template
            )
            
            # Successful Completion
            bar.set_status("completed")
            self._save_to_history(title, url, filepath, "completed")
            
        except DownloadCancelledException:
            bar.set_status("cancelled")
            self._save_to_history(title, url, "", "cancelled")
            
        except Exception as e:
            bar.set_status("failed")
            self._save_to_history(title, url, "", "failed")
            self._show_snackbar(_("Download error: {}").format(str(e)), self.colors.accent_red)
            
        finally:
            if task_id in self.active_cancels:
                del self.active_cancels[task_id]

    def _cancel_download(self, task_id: str):
        if task_id in self.active_cancels:
            self.active_cancels[task_id].set()
            self._show_snackbar(_("Cancelling download..."), self.colors.accent_orange)

    def _save_to_history(self, title: str, url: str, filepath: str, status: str):
        # Retrieve and update history array in config
        history = get_setting("download_history") or []
        history.append({
            'title': title,
            'url': url,
            'filepath': filepath,
            'status': status,
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        set_setting("download_history", history)
        
        # Trigger reload on layout views history screen if loaded
        if self.app_layout and "history" in self.app_layout.views:
            self.app_layout.views["history"].on_load()

    def _show_snackbar(self, message: str, color: str):
        # Flet 0.85: SnackBar is a DialogControl, shown via page.show_dialog()
        try:
            self.main_page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(message, color=self.colors.on_primary, font_family="Montserrat-Regular"),
                    bgcolor=color,
                    open=True,
                )
            )
        except Exception:
            pass
