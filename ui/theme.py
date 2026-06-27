# pyrefly: ignore [missing-import]
import flet as ft

# Shadcn-inspired color design tokens
class ThemeColors:
    def __init__(self, is_dark: bool = True):
        self.is_dark = is_dark
        
        # Color mappings
        self.background = "#09090b" if is_dark else "#ffffff"
        self.card = "#18181b" if is_dark else "#fafafa"
        self.card_secondary = "#27272a" if is_dark else "#f4f4f5"
        self.border = "#27272a" if is_dark else "#e4e4e7"
        self.border_hover = "#3f3f46" if is_dark else "#cbd5e1"
        
        # Text
        self.text_primary = "#fafafa" if is_dark else "#09090b"
        self.text_muted = "#a1a1aa" if is_dark else "#71717a"
        
        # Accent / Status
        self.primary = "#fafafa" if is_dark else "#18181b"
        self.primary_hover = "#e4e4e7" if is_dark else "#27272a"
        self.on_primary = "#18181b" if is_dark else "#ffffff"
        
        self.accent_red = "#ef4444"
        self.accent_green = "#22c55e"
        self.accent_blue = "#3b82f6"
        self.accent_orange = "#f97316"
        
        # Sidebar specific
        self.sidebar_bg = "#09090b" if is_dark else "#fafafa"
        self.sidebar_border = "#27272a" if is_dark else "#e4e4e7"

# Global theme fonts loaded from local assets
FONTS = {
    "Montserrat-Regular": "/fonts/Montserrat-Regular.ttf",
    "Montserrat-Medium": "/fonts/Montserrat-Medium.ttf",
    "Montserrat-Bold": "/fonts/Montserrat-Bold.ttf",
    "Unbounded-Bold": "/fonts/Unbounded-Bold.ttf"
}

def apply_base_page_theme(page: ft.Page):
    """Configures the default Page fonts and window settings."""
    page.fonts = FONTS
    page.title = "VIDOS"
    page.window.icon = "/vidos_icon.ico"
    page.theme = ft.Theme(font_family="Montserrat-Regular")
    page.dark_theme = ft.Theme(font_family="Montserrat-Regular")
    page.window.title_bar_hidden = False
    page.window.min_width = 950
    page.window.min_height = 680
    page.window.width = 1000
    page.window.height = 720
