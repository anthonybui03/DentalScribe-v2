"""First-run onboarding tutorial — v2."""
import customtkinter as ctk
from app.gui.theme import C
from app.core import config as cfg_module

STEPS = [
    {"title": "Welcome to DentalScribe", "icon": "🦷",
     "body": "DentalScribe turns your spoken dictation into professional dental chart notes — completely on this computer.\n\nNo patient data ever leaves this machine.\n\nThis quick tour walks you through the basics in about 2 minutes."},
    {"title": "Set Up Your Microphone", "icon": "🎙",
     "body": "In the left sidebar, select the microphone you'll be speaking into — usually your headset or built-in mic.\n\nClick the ↻ button next to the microphone dropdown if your mic isn't showing up."},
    {"title": "Choose a Note Template", "icon": "📋",
     "body": "DentalScribe includes 7 built-in templates:\n\n  • Hygiene Recall\n  • Limited Exam\n  • Pediatric Restorative\n  • Fluoride / SDF\n  • Extraction\n  • Referral Letter\n  • Custom / Freeform\n\nPick the one that matches your note type. The note box will show the section headings so you know what to cover.\n\nCreate custom templates under ✎ Manage."},
    {"title": "Dictate Your Note", "icon": "⏺",
     "body": "Enter the Patient ID at the top of the sidebar.\n\nClick Start Dictation or press F2 and speak naturally.\n\nClick Stop Dictation or press F2 again when done.\n\nDentalScribe transcribes your audio locally and sends it to the AI to generate a formatted note."},
    {"title": "Review and Edit the Note", "icon": "✏️",
     "body": "The generated note appears on the right side of the screen.\n\nAlways review it before using it — the AI is very accurate but may occasionally miss details.\n\nClick directly in the note box to edit anything.\n\nIf you're not happy with the result, click ↻ Regenerate to try again."},
    {"title": "Send to Open Dental", "icon": "➤",
     "body": "When the note looks good:\n\n📋 Copy to Clipboard — copies the note so you can paste it directly into Open Dental.\n\n➤ Open Dental — if your office has the API configured, this sends the note directly.\n\nThe clipboard method works without any setup and is recommended for most offices."},
    {"title": "Security and Privacy", "icon": "🔒",
     "body": "DentalScribe is designed with privacy in mind:\n\n  • Everything runs on this computer — no cloud, no internet\n  • Notes and logs are encrypted on disk\n  • The app locks automatically after inactivity\n  • Every action is logged in the Audit Log\n\nConfigure PIN, timeout, and encryption under ⚙ Settings."},
    {"title": "You're All Set!", "icon": "✅",
     "body": "You're ready to start using DentalScribe.\n\nQuick reminders:\n\n  • F2 — Start / Stop dictation\n  • F12 — Lock the app\n  • Always review AI-generated notes before chart entry\n\nTo see this tutorial again, go to ⚙ Settings → Storage → Restart Onboarding Tutorial."},
]


class OnboardingWindow(ctk.CTkToplevel):

    def __init__(self, parent, cfg: dict, on_complete=None):
        super().__init__(parent)
        self.cfg = cfg
        self.on_complete = on_complete
        self._step = 0
        self.title("Welcome to DentalScribe")
        self.geometry("580x560")
        self.minsize(500, 500)
        self.resizable(True, True)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._finish)
        self._build_ui()
        self._show_step(0)

    def _build_ui(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Progress dots
        self._dots_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self._dots_frame.grid(row=0, column=0, sticky="ew", pady=(12, 0))

        # Nav bar — packed first so it always stays visible
        nav = ctk.CTkFrame(self, fg_color="transparent", height=56)
        nav.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 12))
        nav.grid_propagate(False)
        nav.grid_columnconfigure(1, weight=1)

        self._back_btn = ctk.CTkButton(nav, text="← Back", command=self._prev,
                                        fg_color="transparent", hover_color=C["border"],
                                        text_color=C["text2"], border_width=1,
                                        border_color=C["border"], corner_radius=8,
                                        font=ctk.CTkFont("Segoe UI", 12),
                                        width=90, height=36)
        self._back_btn.grid(row=0, column=0, sticky="w")

        self._skip_btn = ctk.CTkButton(nav, text="Skip Tour", command=self._finish,
                                        fg_color="transparent", hover_color=C["border"],
                                        text_color=C["text3"],
                                        font=ctk.CTkFont("Segoe UI", 11),
                                        width=80, height=36)
        self._skip_btn.grid(row=0, column=1, sticky="w", padx=8)

        self._next_btn = ctk.CTkButton(nav, text="Next →", command=self._next,
                                        fg_color=C["accent"], hover_color=C["accent_dark"],
                                        text_color="#fff", corner_radius=8,
                                        font=ctk.CTkFont("Segoe UI", 12, weight="bold"),
                                        width=120, height=36)
        self._next_btn.grid(row=0, column=2, sticky="e")

        # Content card
        card = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=12)
        card.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 8))
        card.grid_rowconfigure(3, weight=1)
        card.grid_columnconfigure(0, weight=1)

        self._icon_label = ctk.CTkLabel(card, text="",
                                         font=ctk.CTkFont("Segoe UI", 36))
        self._icon_label.grid(row=0, column=0, pady=(24, 4))

        self._title_label = ctk.CTkLabel(card, text="",
                                          font=ctk.CTkFont("Segoe UI", 16, weight="bold"),
                                          text_color=C["text"], wraplength=480)
        self._title_label.grid(row=1, column=0, pady=(0, 10))

        ctk.CTkFrame(card, fg_color=C["border"], height=1,
                     corner_radius=0).grid(row=2, column=0, sticky="ew",
                                           padx=24, pady=(0, 10))

        self._body = ctk.CTkTextbox(card,
                                     fg_color="transparent",
                                     text_color=C["text2"],
                                     font=ctk.CTkFont("Segoe UI", 12),
                                     wrap="word",
                                     border_width=0,
                                     scrollbar_button_color=C["border"],
                                     activate_scrollbars=True)
        self._body.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 20))

    def _show_step(self, index: int) -> None:
        step = STEPS[index]
        self._icon_label.configure(text=step["icon"])
        self._title_label.configure(text=step["title"])
        self._body.configure(state="normal")
        self._body.delete("1.0", "end")
        self._body.insert("end", step["body"])
        self._body.configure(state="disabled")

        # Dots
        for w in self._dots_frame.winfo_children():
            w.destroy()
        dot_row = ctk.CTkFrame(self._dots_frame, fg_color="transparent")
        dot_row.pack(expand=True)
        for i in range(len(STEPS)):
            color = C["accent"] if i == index else C["border"]
            size = 10 if i == index else 7
            ctk.CTkFrame(dot_row, fg_color=color,
                         width=size, height=size,
                         corner_radius=size).pack(side="left", padx=3)

        is_first = index == 0
        is_last  = index == len(STEPS) - 1
        self._back_btn.configure(state="disabled" if is_first else "normal")
        self._next_btn.configure(text="Get Started ✓" if is_last else "Next →")
        if is_last:
            self._skip_btn.grid_remove()
        else:
            self._skip_btn.grid()

    def _next(self) -> None:
        if self._step < len(STEPS) - 1:
            self._step += 1
            self._show_step(self._step)
        else:
            self._finish()

    def _prev(self) -> None:
        if self._step > 0:
            self._step -= 1
            self._show_step(self._step)

    def _finish(self) -> None:
        self.cfg["onboarding_complete"] = True
        try:
            cfg_module.save(self.cfg)
        except Exception:
            pass
        parent = self.master
        on_complete = self.on_complete
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
        try:
            parent.lift()
            parent.focus_force()
        except Exception:
            pass
        if on_complete:
            on_complete()


def should_show(cfg: dict) -> bool:
    return not cfg.get("onboarding_complete", False)
