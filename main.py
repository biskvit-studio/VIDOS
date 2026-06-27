# pyrefly: ignore [missing-import]
import flet as ft
import logging

# Configure logging to console only (stderr). Never log to files in source.
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

from ui.theme import ThemeColors, apply_base_page_theme
from ui.layout import AppLayout
from ui.views import DownloadView, HistoryView, SettingsView
from downloader import get_setting, set_setting, init_translations

async def main(page: ft.Page):
    # Initialize translations
    init_translations()

    # Retrieve theme preference (default to dark theme)
    is_dark = get_setting("theme_dark", True)
        
    # Configure base window dimensions, title, and styling fonts
    apply_base_page_theme(page)
    
    current_tab = "download"

    def toggle_theme():
        nonlocal is_dark
        is_dark = not is_dark
        set_setting("theme_dark", is_dark)
        rebuild_app()

    def rebuild_app():
        nonlocal current_tab
        # Re-initialize translations context in case language was updated
        init_translations()
        
        # Reinitialize palette colors
        colors = ThemeColors(is_dark=is_dark)
        page.bgcolor = colors.background
        
        # Configure layout
        layout = AppLayout(page, colors, on_theme_toggle=toggle_theme)
        
        # Instantiate views
        views = {
            "download": DownloadView(page, colors, layout),
            "history": HistoryView(page, colors),
            "settings": SettingsView(page, colors, on_language_change=rebuild_app)
        }
        layout.views = views
        
        # Preserve active tab navigation state
        layout.active_tab = current_tab
        for tab_name, btn in layout.nav_buttons.items():
            btn.set_active(tab_name == current_tab)
            
        layout.content_frame.content = views[current_tab]
        
        # Hook tab switch to preserve current tab state during rebuilds
        original_switch = layout.switch_tab
        def custom_switch(tab_name):
            nonlocal current_tab
            current_tab = tab_name
            original_switch(tab_name)
        layout.switch_tab = custom_switch

        page.clean()
        page.add(layout)
        page.update()

    rebuild_app()

if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
