# pyrefly: ignore [missing-import]
import flet as ft
from ui.theme import ThemeColors
from downloader import _



class SidebarButton(ft.Container):
    """Sidebar navigation link with active state highlighting."""
    def __init__(self, label: str, icon: str, is_active: bool, on_click, colors: ThemeColors):
        # Build child controls before super().__init__()
        icon_control = ft.Icon(
            icon=icon,
            size=18,
            color=colors.text_primary if is_active else colors.text_muted
        )
        label_control = ft.Text(
            label,
            size=14,
            weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500,
            color=colors.text_primary if is_active else colors.text_muted,
            font_family="Montserrat-Medium"
        )

        bg = colors.card_secondary if is_active else "transparent"

        # super().__init__() FIRST — Flet 0.85 requirement
        super().__init__(
            content=ft.Row(
                [icon_control, label_control],
                spacing=12,
            ),
            bgcolor=bg,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            on_click=on_click,
            on_hover=self._handle_hover,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT)
        )

        # Store references AFTER super().__init__()
        self._colors = colors
        self._is_active = is_active
        self._icon_control = icon_control
        self._label_control = label_control

    def _handle_hover(self, e):
        if self._is_active:
            return
        if e.data == "true":
            self.bgcolor = ft.Colors.with_opacity(0.05, self._colors.text_primary)
            self._label_control.color = self._colors.text_primary
            self._icon_control.color = self._colors.text_primary
        else:
            self.bgcolor = "transparent"
            self._label_control.color = self._colors.text_muted
            self._icon_control.color = self._colors.text_muted
        try:
            self.update()
        except Exception:
            pass

    def set_active(self, active: bool):
        self._is_active = active
        self.bgcolor = self._colors.card_secondary if active else "transparent"
        self._label_control.color = self._colors.text_primary if active else self._colors.text_muted
        self._label_control.weight = ft.FontWeight.W_600 if active else ft.FontWeight.W_500
        self._icon_control.color = self._colors.text_primary if active else self._colors.text_muted
        try:
            self.update()
        except Exception:
            pass


class AppLayout(ft.Row):
    """Main application shell containing sidebar and content frame."""
    def __init__(self, page: ft.Page, colors: ThemeColors, on_theme_toggle):
        # Build all sidebar elements before super().__init__()
        logo_src = "/vidos_logo_dark.png" if colors.is_dark else "/vidos_logo_light.png"
        logo = ft.Row(
            [
                ft.Image(src=logo_src, width=28, height=28, fit=ft.BoxFit.CONTAIN),
                ft.Text(
                    "VIDOS",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    font_family="Unbounded-Bold",
                    color=colors.text_primary
                )
            ],
            spacing=10
        )

        nav_buttons = {
            "download": SidebarButton(_("Download"), ft.Icons.DOWNLOAD_ROUNDED, True, lambda _: None, colors),
            "history": SidebarButton(_("History"), ft.Icons.HISTORY_ROUNDED, False, lambda _: None, colors),
            "settings": SidebarButton(_("Settings"), ft.Icons.SETTINGS_ROUNDED, False, lambda _: None, colors),
        }

        theme_btn = ft.IconButton(
            icon=ft.Icons.DARK_MODE_ROUNDED if colors.is_dark else ft.Icons.LIGHT_MODE_ROUNDED,
            icon_size=20,
            icon_color=colors.text_muted,
            on_click=lambda _: on_theme_toggle(),
            tooltip=_("Toggle Theme"),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=8,
            )
        )

        sidebar = ft.Container(
            content=ft.Column(
                [
                    ft.Column(
                        [
                            logo,
                            ft.Container(height=16),
                            nav_buttons["download"],
                            nav_buttons["history"],
                            nav_buttons["settings"],
                        ],
                        spacing=6,
                    ),
                    ft.Row(
                        [
                            ft.Text(_("Theme Mode"), size=13, color=colors.text_muted, font_family="Montserrat-Regular"),
                            theme_btn
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            width=230,
            bgcolor=colors.sidebar_bg,
            border=ft.Border.only(right=ft.BorderSide(1, colors.sidebar_border)),
            padding=ft.Padding.all(20),
        )

        content_frame = ft.Container(
            expand=True,
            bgcolor=colors.background,
            padding=ft.Padding.all(32),
        )

        # super().__init__() FIRST
        super().__init__(
            controls=[sidebar, content_frame],
            spacing=0,
            expand=True,
        )

        # Store references AFTER super().__init__()
        self._colors = colors
        self._on_theme_toggle = on_theme_toggle
        self.nav_buttons = nav_buttons
        self.content_frame = content_frame
        self.active_tab = "download"
        self.views = {}

        # Wire up nav button click handlers now that self exists
        nav_buttons["download"].on_click = lambda _: self.switch_tab("download")
        nav_buttons["history"].on_click = lambda _: self.switch_tab("history")
        nav_buttons["settings"].on_click = lambda _: self.switch_tab("settings")

    def switch_tab(self, tab_name: str):
        if tab_name == self.active_tab:
            return

        self.nav_buttons[self.active_tab].set_active(False)
        self.nav_buttons[tab_name].set_active(True)
        self.active_tab = tab_name

        if tab_name in self.views:
            self.content_frame.content = self.views[tab_name]
            if hasattr(self.views[tab_name], 'on_load'):
                self.views[tab_name].on_load()
        try:
            self.content_frame.update()
        except Exception:
            pass
