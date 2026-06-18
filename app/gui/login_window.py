"""PIN lock screen — shown on startup and after inactivity."""
import customtkinter as ctk
from app.gui.theme import C, make_font, primary_btn, make_entry


class LoginWindow(ctk.CTkFrame):

    def __init__(self, root: ctk.CTk, cfg: dict, on_authenticated=None):
        super().__init__(root, fg_color=C["bg"])
        self.root = root
        self.cfg = cfg
        self.on_authenticated = on_authenticated
        self.pack(fill="both", expand=True)
        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=16, width=360)
        card.grid(row=0, column=0)
        card.grid_propagate(False)
        card.configure(width=360, height=420)

        ctk.CTkLabel(card, text="🦷", font=ctk.CTkFont("Segoe UI", 48)).pack(pady=(40, 4))
        ctk.CTkLabel(card, text="DentalScribe",
                     font=make_font(22, bold=True), text_color=C["text"]).pack()
        ctk.CTkLabel(card, text="v2.0  ·  Local AI",
                     font=make_font(11), text_color=C["text3"]).pack(pady=(2, 0))
        ctk.CTkLabel(card, text="Made by Anthony Bui",
                     font=make_font(10), text_color=C["text3"]).pack(pady=(2, 20))

        if self.cfg.get("pin_hash"):
            ctk.CTkLabel(card, text="Enter PIN to unlock",
                         font=make_font(12), text_color=C["text2"]).pack(pady=(0, 8))
            self._pin_var = ctk.StringVar()
            self._pin_entry = make_entry(card, textvariable=self._pin_var,
                                         placeholder="PIN", show="●", width=200)
            self._pin_entry.pack(pady=(0, 6))
            self._pin_entry.bind("<Return>", lambda _: self._unlock())
            self._error = ctk.CTkLabel(card, text="", font=make_font(11),
                                        text_color=C["danger"])
            self._error.pack()
            primary_btn(card, "Unlock", command=self._unlock, width=200).pack(pady=(8, 0))
            self.after(100, self._pin_entry.focus)
        else:
            ctk.CTkLabel(card, text="No PIN set — click to enter",
                         font=make_font(12), text_color=C["text2"]).pack(pady=(0, 12))
            self._pin_var = ctk.StringVar()
            self._pin_entry = make_entry(card, textvariable=self._pin_var,
                                         placeholder="Set a PIN (optional)", show="●", width=200)
            self._pin_entry.pack(pady=(0, 6))
            self._error = ctk.CTkLabel(card, text="", font=make_font(11),
                                        text_color=C["danger"])
            self._error.pack()
            primary_btn(card, "Set PIN & Enter", command=self._set_pin, width=200).pack(pady=(4, 0))
            ctk.CTkButton(card, text="Skip (no PIN)", command=self._skip,
                          fg_color="transparent", text_color=C["text3"],
                          hover_color=C["bg"], font=make_font(11),
                          width=200).pack(pady=(4, 0))

    def _unlock(self) -> None:
        from app.core.crypto import hash_pin, derive_key, get_fernet
        pin = self._pin_var.get()
        if hash_pin(pin) == self.cfg.get("pin_hash", ""):
            self.cfg["_fernet"] = get_fernet(derive_key(pin))
            self._enter()
        else:
            self._error.configure(text="Incorrect PIN — try again.")
            self._pin_var.set("")

    def _set_pin(self) -> None:
        from app.core.crypto import hash_pin, derive_key, get_fernet
        pin = self._pin_var.get().strip()
        if pin:
            self.cfg["pin_hash"] = hash_pin(pin)
            self.cfg["_fernet"] = get_fernet(derive_key(pin))
            from app.core import config as cfg_module
            cfg_module.save(self.cfg)
        self._enter()

    def _skip(self) -> None:
        self._enter()

    def _enter(self) -> None:
        self.pack_forget()
        if self.on_authenticated:
            self.on_authenticated()
