# pyrefly: ignore [missing-import]
import flet as ft
from typing import Optional
from ui.theme import ThemeColors


class ShadcnButton(ft.Container):
    """A custom container-based button styled to look like a Shadcn UI button."""
    def __init__(
        self,
        text: str,
        on_click,
        colors: ThemeColors,
        is_primary: bool = True,
        icon: Optional[str] = None,
        width: Optional[float] = None,
        height: float = 40,
        disabled: bool = False,
        tooltip: Optional[str] = None
    ):
        # Compute styling before calling super().__init__()
        if disabled:
            bg = colors.card_secondary
            border = ft.Border.all(1, colors.border)
            text_color = colors.text_muted
        elif is_primary:
            bg = colors.primary
            border = None
            text_color = colors.on_primary
        else:
            bg = "transparent"
            border = ft.Border.all(1, colors.border)
            text_color = colors.text_primary

        text_control = ft.Text(
            text,
            size=14,
            weight=ft.FontWeight.W_600,
            color=text_color,
            font_family="Montserrat-Medium"
        )

        row_content = []
        if icon:
            row_content.append(ft.Icon(icon=icon, size=16, color=text_color))
        row_content.append(text_control)

        # super().__init__() FIRST — required by Flet 0.85 before any self.* assignments
        super().__init__(
            content=ft.Row(
                row_content,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=bg,
            border=border,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=16),
            alignment=ft.alignment.Alignment(0, 0),
            width=width,
            height=height,
            on_click=on_click if not disabled else None,
            ink=not disabled,
            tooltip=tooltip,
            on_hover=self._handle_hover,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT)
        )

        # Store references AFTER super().__init__() so _values exists
        self._colors = colors
        self._is_primary = is_primary
        self._disabled_state = disabled
        self._on_click_action = on_click
        self.text_control = text_control  # keep as public for external label updates

    def _handle_hover(self, e):
        if self._disabled_state:
            return
        if e.data == "true":
            self.bgcolor = self._colors.primary_hover if self._is_primary else self._colors.card_secondary
        else:
            self.bgcolor = self._colors.primary if self._is_primary else "transparent"
        try:
            self.update()
        except Exception:
            pass

    def set_disabled(self, disabled: bool):
        self._disabled_state = disabled
        if disabled:
            self.bgcolor = self._colors.card_secondary
            self.border = ft.Border.all(1, self._colors.border)
            self.text_control.color = self._colors.text_muted
            self.on_click = None
        else:
            if self._is_primary:
                self.bgcolor = self._colors.primary
                self.border = None
                self.text_control.color = self._colors.on_primary
            else:
                self.bgcolor = "transparent"
                self.border = ft.Border.all(1, self._colors.border)
                self.text_control.color = self._colors.text_primary
            self.on_click = self._on_click_action
        try:
            self.update()
        except Exception:
            pass


class ShadcnTextField(ft.TextField):
    """A pre-styled TextField mimicking the Shadcn Input design."""
    def __init__(self, colors: ThemeColors, hint_text: str = "", password: bool = False, expand: bool = False, on_submit=None, **kwargs):
        super().__init__(
            hint_text=hint_text,
            password=password,
            can_reveal_password=password,
            expand=expand,
            text_size=14,
            cursor_color=colors.text_primary,
            cursor_width=1.5,
            border_color=colors.border,
            focused_border_color=colors.text_primary,
            border_width=1,
            border_radius=8,
            bgcolor=colors.card,
            text_style=ft.TextStyle(font_family="Montserrat-Regular", color=colors.text_primary),
            hint_style=ft.TextStyle(font_family="Montserrat-Regular", color=colors.text_muted, size=14),
            content_padding=14,
            on_submit=on_submit,
            **kwargs
        )
