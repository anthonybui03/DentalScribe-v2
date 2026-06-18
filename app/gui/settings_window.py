"""Settings window — v2 CustomTkinter."""
import customtkinter as ctk
from app.gui.theme import C, make_font, primary_btn, ghost_btn, make_entry, make_combo
from app.core import config as cfg_module
from app.core.note_generator import check_ollama_health, list_ollama_models
from app.core.transcriber import list_available_models


class SettingsWindow(ctk.CTkToplevel):

    def __init__(self, parent, cfg: dict):
        super().__init__(parent)
        self.cfg = cfg
        self.title("Settings — DentalScribe v2")
        self.geometry("640x580")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        tabs = ctk.CTkTabview(self, fg_color=C["surface"],
                               segmented_button_fg_color=C["bg"],
                               segmented_button_selected_color=C["accent"],
                               segmented_button_selected_hover_color=C["accent_dark"],
                               segmented_button_unselected_color=C["bg"],
                               segmented_button_unselected_hover_color=C["border"],
                               text_color=C["text2"],
                               corner_radius=12)
        tabs.grid(row=0, column=0, sticky="nsew", padx=16, pady=(16, 0))

        for name in ["Transcription", "AI / Ollama", "Security", "Open Dental", "Storage"]:
            tabs.add(name)

        self._build_transcription(tabs.tab("Transcription"))
        self._build_ollama(tabs.tab("AI / Ollama"))
        self._build_security(tabs.tab("Security"))
        self._build_open_dental(tabs.tab("Open Dental"))
        self._build_storage(tabs.tab("Storage"))

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=12)
        primary_btn(btn_bar, "Save & Close", command=self._save,
                    height=36).pack(side="right", padx=(6, 0))
        ghost_btn(btn_bar, "Cancel", command=self.destroy,
                  height=36).pack(side="right")

    def _row(self, parent, label, widget_fn, *a, **kw):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text=label, width=160, anchor="w",
                     font=make_font(11), text_color=C["text2"]).pack(side="left")
        widget = widget_fn(row, *a, **kw)
        widget.pack(side="left")
        return widget

    def _build_transcription(self, parent) -> None:
        ctk.CTkLabel(parent, text="Whisper Settings",
                     font=make_font(13, bold=True),
                     text_color=C["text"]).pack(anchor="w", pady=(12, 6), padx=16)
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=16)
        self._w_backend = self._row(f, "Backend", make_combo,
            values=["faster-whisper", "openai-whisper"])
        self._w_backend.set(self.cfg.get("whisper_backend", "faster-whisper"))
        self._w_model = self._row(f, "Model", make_combo,
            values=list_available_models())
        self._w_model.set(self.cfg.get("whisper_model", "base.en"))
        self._w_device = self._row(f, "Device", make_combo, values=["cpu", "cuda"])
        self._w_device.set(self.cfg.get("whisper_device", "cpu"))
        self._w_compute = self._row(f, "Compute type", make_combo,
            values=["float32", "int8", "float16"])
        self._w_compute.set(self.cfg.get("whisper_compute_type", "float32"))
        ctk.CTkLabel(f, text="Recommended: base.en, cpu, float32 for most office computers.",
                     font=make_font(10), text_color=C["text3"],
                     wraplength=480, justify="left").pack(anchor="w", pady=(8, 0))

    def _build_ollama(self, parent) -> None:
        ctk.CTkLabel(parent, text="Ollama Configuration",
                     font=make_font(13, bold=True),
                     text_color=C["text"]).pack(anchor="w", pady=(12, 6), padx=16)
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=16)
        self._ollama_host_var = ctk.StringVar(
            value=self.cfg.get("ollama_host", "http://localhost:11434"))
        self._row(f, "Ollama host", make_entry,
                  textvariable=self._ollama_host_var, width=260)
        model_row = ctk.CTkFrame(f, fg_color="transparent")
        model_row.pack(fill="x", pady=4)
        ctk.CTkLabel(model_row, text="Model", width=160, anchor="w",
                     font=make_font(11), text_color=C["text2"]).pack(side="left")
        self._ollama_model_var = ctk.StringVar(
            value=self.cfg.get("ollama_model", "llama3"))
        self._model_combo = make_combo(model_row, values=[self._ollama_model_var.get()])
        self._model_combo.set(self._ollama_model_var.get())
        self._model_combo.pack(side="left")
        ghost_btn(model_row, "Fetch", command=self._fetch_models,
                  width=70, height=30).pack(side="left", padx=8)
        self._health_label = ctk.CTkLabel(f, text="",
                                           font=make_font(11), text_color=C["text2"])
        self._health_label.pack(anchor="w", pady=4)
        ghost_btn(f, "Test Connection", command=self._test_ollama,
                  height=32).pack(anchor="w", pady=(0, 8))

    def _fetch_models(self) -> None:
        models = list_ollama_models(self._ollama_host_var.get())
        if models:
            self._model_combo.configure(values=models)
            self._health_label.configure(
                text=f"✓ {len(models)} model(s) found", text_color=C["success"])
        else:
            self._health_label.configure(
                text="✗ Could not fetch — is Ollama running?", text_color=C["danger"])

    def _test_ollama(self) -> None:
        ok = check_ollama_health(self._ollama_host_var.get())
        self._health_label.configure(
            text="✓ Ollama is reachable" if ok else "✗ Ollama not reachable",
            text_color=C["success"] if ok else C["danger"])

    def _build_security(self, parent) -> None:
        ctk.CTkLabel(parent, text="App Lock",
                     font=make_font(13, bold=True),
                     text_color=C["text"]).pack(anchor="w", pady=(12, 6), padx=16)
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=16)
        ghost_btn(f, "Change PIN…", command=self._change_pin,
                  height=32).pack(anchor="w", pady=(0, 8))
        self._timeout_var = ctk.StringVar(
            value=str(self.cfg.get("inactivity_timeout_minutes", 10)))
        self._row(f, "Auto-lock after (min)", make_entry,
                  textvariable=self._timeout_var, width=80)
        ctk.CTkLabel(parent, text="Data Encryption",
                     font=make_font(13, bold=True),
                     text_color=C["text"]).pack(anchor="w", pady=(12, 6), padx=16)
        f2 = ctk.CTkFrame(parent, fg_color="transparent")
        f2.pack(fill="x", padx=16)
        self._encrypt_var = ctk.BooleanVar(value=self.cfg.get("encrypt_at_rest", True))
        ctk.CTkCheckBox(f2, text="Encrypt saved notes and logs at rest",
                         variable=self._encrypt_var,
                         font=make_font(11), text_color=C["text2"],
                         fg_color=C["accent"], hover_color=C["accent_dark"]).pack(anchor="w", pady=3)
        self._audio_var = ctk.BooleanVar(value=self.cfg.get("save_raw_audio", False))
        ctk.CTkCheckBox(f2, text="Save raw audio (encrypted, opt-in)",
                         variable=self._audio_var,
                         font=make_font(11), text_color=C["text2"],
                         fg_color=C["accent"], hover_color=C["accent_dark"]).pack(anchor="w", pady=3)

    def _change_pin(self) -> None:
        from tkinter import simpledialog, messagebox
        pin = simpledialog.askstring("Change PIN", "Enter new PIN:", show="●", parent=self)
        if not pin:
            return
        confirm = simpledialog.askstring("Confirm", "Re-enter PIN:", show="●", parent=self)
        if pin != confirm:
            messagebox.showerror("Mismatch", "PINs do not match.")
            return
        from app.core.crypto import hash_pin, derive_key, get_fernet
        self.cfg["pin_hash"] = hash_pin(pin)
        self.cfg["_fernet"] = get_fernet(derive_key(pin))
        messagebox.showinfo("Done", "PIN updated.")

    def _build_open_dental(self, parent) -> None:
        ctk.CTkLabel(parent, text="Open Dental API (Optional)",
                     font=make_font(13, bold=True),
                     text_color=C["text"]).pack(anchor="w", pady=(12, 4), padx=16)
        ctk.CTkLabel(parent, text="Leave blank to use clipboard-only workflow (recommended).",
                     font=make_font(10), text_color=C["text3"]).pack(anchor="w", padx=16, pady=(0, 8))
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=16)
        self._od_url_var = ctk.StringVar(value=self.cfg.get("od_api_url", ""))
        self._od_dev_var = ctk.StringVar(value=self.cfg.get("od_developer_key", ""))
        self._od_cust_var = ctk.StringVar(value=self.cfg.get("od_customer_key", ""))
        self._row(f, "API URL", make_entry, textvariable=self._od_url_var, width=260)
        self._row(f, "Developer key", make_entry, textvariable=self._od_dev_var,
                  show="●", width=260)
        self._row(f, "Customer key", make_entry, textvariable=self._od_cust_var,
                  show="●", width=260)
        self._od_status = ctk.CTkLabel(f, text="", font=make_font(11), text_color=C["text2"])
        self._od_status.pack(anchor="w", pady=4)
        ghost_btn(f, "Test Connection", command=self._test_od, height=32).pack(anchor="w")

    def _test_od(self) -> None:
        from app.core.open_dental import OpenDentalConnector
        url, key = self._od_url_var.get(), self._od_dev_var.get()
        if not url or not key:
            self._od_status.configure(text="Enter URL and key first.", text_color=C["warn"])
            return
        ok = OpenDentalConnector(url, key, self._od_cust_var.get()).test_connection()
        self._od_status.configure(
            text="✓ Connected" if ok else "✗ Could not connect",
            text_color=C["success"] if ok else C["danger"])

    def _build_storage(self, parent) -> None:
        import os
        from pathlib import Path
        data_dir = Path(os.getenv("APPDATA", "~")).expanduser() / "DentalScribe-v2"
        ctk.CTkLabel(parent, text="Local Storage",
                     font=make_font(13, bold=True),
                     text_color=C["text"]).pack(anchor="w", pady=(12, 6), padx=16)
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=16)
        self._save_notes_var = ctk.BooleanVar(value=self.cfg.get("save_notes_locally", True))
        ctk.CTkCheckBox(f, text="Allow saving notes locally",
                         variable=self._save_notes_var,
                         font=make_font(11), text_color=C["text2"],
                         fg_color=C["accent"], hover_color=C["accent_dark"]).pack(anchor="w", pady=3)
        ctk.CTkLabel(f, text=f"Data folder:\n{data_dir}",
                     font=make_font(10), text_color=C["text3"],
                     justify="left").pack(anchor="w", pady=(10, 6))
        ghost_btn(f, "Open Data Folder",
                  command=lambda: os.startfile(str(data_dir)),
                  height=32).pack(anchor="w")
        ctk.CTkLabel(parent, text="Onboarding",
                     font=make_font(13, bold=True),
                     text_color=C["text"]).pack(anchor="w", pady=(14, 6), padx=16)
        ghost_btn(parent, "Restart Onboarding Tutorial",
                  command=self._restart_onboarding,
                  height=32).pack(anchor="w", padx=16)

    def _restart_onboarding(self) -> None:
        self.cfg["onboarding_complete"] = False
        cfg_module.save(self.cfg)
        from tkinter import messagebox
        messagebox.showinfo("Onboarding Reset",
                            "The tutorial will show next time you open the app.")
        self.destroy()

    def _save(self) -> None:
        self.cfg.update({
            "whisper_backend":            self._w_backend.get(),
            "whisper_model":              self._w_model.get(),
            "whisper_device":             self._w_device.get(),
            "whisper_compute_type":       self._w_compute.get(),
            "ollama_host":                self._ollama_host_var.get(),
            "ollama_model":               self._model_combo.get(),
            "inactivity_timeout_minutes": int(self._timeout_var.get() or 10),
            "encrypt_at_rest":            self._encrypt_var.get(),
            "save_raw_audio":             self._audio_var.get(),
            "od_api_url":                 self._od_url_var.get(),
            "od_developer_key":           self._od_dev_var.get(),
            "od_customer_key":            self._od_cust_var.get(),
            "save_notes_locally":         self._save_notes_var.get(),
        })
        cfg_module.save(self.cfg)
        self.destroy()
