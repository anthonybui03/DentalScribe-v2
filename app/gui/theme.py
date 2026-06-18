"""CustomTkinter theme configuration for DentalScribe v2."""
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Color palette
C = {
    "bg":          "#0F172A",
    "surface":     "#1E293B",
    "surface2":    "#162032",
    "border":      "#334155",
    "accent":      "#3B82F6",
    "accent_dark": "#2563EB",
    "text":        "#F1F5F9",
    "text2":       "#94A3B8",
    "text3":       "#475569",
    "success":     "#22C55E",
    "warn":        "#F59E0B",
    "warn_bg":     "#451A03",
    "danger":      "#EF4444",
    "record":      "#EF4444",
}

FONT       = ("Segoe UI", 12)
FONT_BOLD  = ("Segoe UI", 12, "bold")
FONT_SM    = ("Segoe UI", 11)
FONT_XS    = ("Segoe UI", 10)
FONT_MONO  = ("Consolas", 11)
FONT_LABEL = ("Segoe UI", 10)


def make_font(size=12, bold=False) -> ctk.CTkFont:
    return ctk.CTkFont("Segoe UI", size, weight="bold" if bold else "normal")


def section_label(parent, text: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(parent, text=text.upper(),
                        font=ctk.CTkFont("Segoe UI", 10, weight="bold"),
                        text_color=C["text3"])


def divider(parent) -> ctk.CTkFrame:
    return ctk.CTkFrame(parent, height=1, fg_color=C["border"], corner_radius=0)


def primary_btn(parent, text, command=None, **kw) -> ctk.CTkButton:
    defaults = dict(fg_color=C["accent"], hover_color=C["accent_dark"],
                    text_color="#ffffff", corner_radius=8,
                    font=ctk.CTkFont("Segoe UI", 12, weight="bold"))
    defaults.update(kw)
    return ctk.CTkButton(parent, text=text, command=command, **defaults)


def ghost_btn(parent, text, command=None, **kw) -> ctk.CTkButton:
    defaults = dict(fg_color="transparent", hover_color=C["border"],
                    text_color=C["text2"], border_width=1,
                    border_color=C["border"], corner_radius=8,
                    font=ctk.CTkFont("Segoe UI", 11))
    defaults.update(kw)
    return ctk.CTkButton(parent, text=text, command=command, **defaults)


def subtle_btn(parent, text, command=None, **kw) -> ctk.CTkButton:
    defaults = dict(fg_color="transparent", hover_color=C["surface"],
                    text_color=C["text2"], corner_radius=8,
                    font=ctk.CTkFont("Segoe UI", 11))
    defaults.update(kw)
    return ctk.CTkButton(parent, text=text, command=command, **defaults)


def make_entry(parent, textvariable=None, placeholder="", show="", **kw) -> ctk.CTkEntry:
    defaults = dict(fg_color=C["bg"], border_color=C["border"],
                    text_color=C["text"], placeholder_text_color=C["text3"],
                    corner_radius=8)
    defaults.update(kw)
    return ctk.CTkEntry(parent, textvariable=textvariable,
                        placeholder_text=placeholder, show=show, **defaults)


def make_textbox(parent, **kw) -> ctk.CTkTextbox:
    defaults = dict(
        fg_color=C["surface"],
        text_color=C["text"],
        font=ctk.CTkFont("Consolas", 11),
        corner_radius=10,
        border_width=1,
        border_color=C["border"],
        scrollbar_button_color=C["border"],
        scrollbar_button_hover_color=C["text3"],
        wrap="word",
    )
    defaults.update(kw)
    return ctk.CTkTextbox(parent, **defaults)


def make_combo(parent, values=None, command=None, **kw) -> ctk.CTkComboBox:
    return ctk.CTkComboBox(parent,
                           values=values or [],
                           command=command,
                           fg_color=C["bg"],
                           border_color=C["border"],
                           button_color=C["border"],
                           button_hover_color=C["accent"],
                           text_color=C["text"],
                           dropdown_fg_color=C["surface"],
                           dropdown_text_color=C["text"],
                           dropdown_hover_color=C["accent"],
                           corner_radius=8,
                           font=ctk.CTkFont("Segoe UI", 11),
                           state="readonly", **kw)
