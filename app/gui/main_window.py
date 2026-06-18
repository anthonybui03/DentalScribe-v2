"""Main dictation window — DentalScribe v2 (CustomTkinter)."""
import threading
import customtkinter as ctk
from datetime import datetime, timezone
from pathlib import Path

from app.core import audio, config, note_generator, note_history
from app.core.audit_log import append_entry
from app.gui import theme as T
from app.gui.theme import C
from app.models.note_templates import template_names, get_template

_LIVE_MS = 3000


class MainWindow(ctk.CTkFrame):

    def __init__(self, root: ctk.CTk, cfg: dict):
        super().__init__(root, fg_color=C["bg"])
        self.root = root
        self.cfg = cfg
        self.recorder = audio.AudioRecorder(device_index=cfg.get("mic_device_index"))
        self._wav_bytes: bytes = b""
        self._inactivity_job = None
        self._live_job = None
        self._live_running = False

        self.pack(fill="both", expand=True)
        self._build_ui()
        self._refresh_devices()
        self._bind_hotkeys(root)
        self._reset_inactivity_timer()
        self.after(150, self._on_template_change)
        self._status("Ready — select a template and click Start Dictation.", "normal")

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_main()

    def _build_sidebar(self) -> None:
        sb = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0, width=230)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(10, weight=1)

        # Logo
        logo = ctk.CTkFrame(sb, fg_color="transparent")
        logo.grid(row=0, column=0, sticky="ew", padx=16, pady=(20, 12))
        icon_frame = ctk.CTkFrame(logo, fg_color=C["accent"], corner_radius=10,
                                   width=40, height=40)
        icon_frame.pack(side="left", padx=(0, 10))
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text="🦷", font=ctk.CTkFont("Segoe UI", 20)).place(relx=0.5, rely=0.5, anchor="center")
        title_col = ctk.CTkFrame(logo, fg_color="transparent")
        title_col.pack(side="left")
        ctk.CTkLabel(title_col, text="DentalScribe",
                     font=ctk.CTkFont("Segoe UI", 15, weight="bold"),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(title_col, text="v2.0  ·  Local AI",
                     font=ctk.CTkFont("Segoe UI", 10), text_color=C["text3"]).pack(anchor="w")
        ctk.CTkLabel(title_col, text="Made by Anthony Bui",
                     font=ctk.CTkFont("Segoe UI", 10), text_color=C["text3"]).pack(anchor="w")

        T.divider(sb).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))

        # Patient ID
        pid = ctk.CTkFrame(sb, fg_color="transparent")
        pid.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 4))
        T.section_label(pid, "Patient ID / Chart #").pack(anchor="w", pady=(0, 4))
        self._patient_var = ctk.StringVar()
        T.make_entry(pid, textvariable=self._patient_var,
                     placeholder="Enter patient ID…").pack(fill="x")

        # Template
        tmpl = ctk.CTkFrame(sb, fg_color="transparent")
        tmpl.grid(row=3, column=0, sticky="ew", padx=16, pady=4)
        tmpl_hdr = ctk.CTkFrame(tmpl, fg_color="transparent")
        tmpl_hdr.pack(fill="x", pady=(0, 4))
        T.section_label(tmpl_hdr, "Note Template").pack(side="left")
        ctk.CTkButton(tmpl_hdr, text="✎ Manage", command=self._open_templates,
                      fg_color="transparent", hover_color=C["bg"],
                      text_color=C["accent"], font=ctk.CTkFont("Segoe UI", 10),
                      width=60, height=20).pack(side="right")
        self._template_var = ctk.StringVar(value=self.cfg.get("default_template", "Custom / Freeform"))
        self._template_combo = T.make_combo(tmpl, values=template_names(),
                                             command=lambda _: self.after(50, self._on_template_change))
        self._template_combo.set(self._template_var.get())
        self._template_combo.pack(fill="x")

        # Microphone
        mic = ctk.CTkFrame(sb, fg_color="transparent")
        mic.grid(row=4, column=0, sticky="ew", padx=16, pady=4)
        mic_hdr = ctk.CTkFrame(mic, fg_color="transparent")
        mic_hdr.pack(fill="x", pady=(0, 4))
        T.section_label(mic_hdr, "Microphone").pack(side="left")
        ctk.CTkButton(mic_hdr, text="↻", command=self._refresh_devices,
                      fg_color="transparent", hover_color=C["bg"],
                      text_color=C["text3"], font=ctk.CTkFont("Segoe UI", 13),
                      width=24, height=20).pack(side="right")
        self._mic_combo = T.make_combo(mic, values=[])
        self._mic_combo.pack(fill="x")

        T.divider(sb).grid(row=5, column=0, sticky="ew", padx=16, pady=8)

        # Record button
        rec = ctk.CTkFrame(sb, fg_color="transparent")
        rec.grid(row=6, column=0, sticky="ew", padx=16, pady=4)
        self._rec_btn = ctk.CTkButton(
            rec, text="⏺   Start Dictation",
            command=self._toggle_recording,
            fg_color=C["accent"], hover_color=C["accent_dark"],
            text_color="#fff", corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 13, weight="bold"),
            height=44,
        )
        self._rec_btn.pack(fill="x")
        ctk.CTkLabel(rec, text="or press  F2",
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=C["text3"]).pack(pady=(4, 0))
        self._rec_indicator = ctk.CTkLabel(rec, text="",
                                            font=ctk.CTkFont("Segoe UI", 10, weight="bold"),
                                            text_color=C["record"])
        self._rec_indicator.pack(pady=(2, 0))

        T.divider(sb).grid(row=7, column=0, sticky="ew", padx=16, pady=4)

        # Nav buttons
        nav = ctk.CTkFrame(sb, fg_color="transparent")
        nav.grid(row=8, column=0, sticky="ew", padx=12, pady=4)
        for icon, label, cmd in [
            ("📜", "Note History",  self._open_history),
            ("⚙",  "Settings",     self._open_settings),
            ("📋", "Audit Log",    self._open_audit),
            ("🔒", "Lock App",     self._lock_app),
        ]:
            ctk.CTkButton(nav, text=f"{icon}  {label}", command=cmd,
                          fg_color="transparent", hover_color=C["bg"],
                          text_color=C["text2"], anchor="w",
                          font=ctk.CTkFont("Segoe UI", 11),
                          height=34, corner_radius=8).pack(fill="x", pady=1)

    def _build_main(self) -> None:
        main = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(2, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Top bar
        topbar = ctk.CTkFrame(main, fg_color=C["surface"], corner_radius=0, height=48)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)
        topbar.grid_columnconfigure(1, weight=1)

        left_chips = ctk.CTkFrame(topbar, fg_color="transparent")
        left_chips.grid(row=0, column=0, padx=14, pady=8, sticky="w")
        self._patient_chip = ctk.CTkLabel(left_chips, text="No patient",
                                           fg_color=C["bg"], corner_radius=20,
                                           font=ctk.CTkFont("Segoe UI", 11),
                                           text_color=C["text2"],
                                           padx=12, pady=4)
        self._patient_chip.pack(side="left", padx=(0, 6))
        self._template_chip = ctk.CTkLabel(left_chips, text="Custom / Freeform",
                                            fg_color="#1D4ED8", corner_radius=20,
                                            font=ctk.CTkFont("Segoe UI", 11),
                                            text_color="#60A5FA",
                                            padx=12, pady=4)
        self._template_chip.pack(side="left")

        right_btns = ctk.CTkFrame(topbar, fg_color="transparent")
        right_btns.grid(row=0, column=2, padx=14, pady=8, sticky="e")
        self._regen_btn = ctk.CTkButton(
            right_btns, text="↻  Regenerate",
            command=self._regenerate,
            fg_color=C["surface2"], hover_color=C["border"],
            text_color=C["text2"], corner_radius=6,
            font=ctk.CTkFont("Segoe UI", 11), height=28,
            state="disabled",
        )
        self._regen_btn.pack(side="right")

        # Warning banner
        banner = ctk.CTkFrame(main, fg_color="#1C1008", corner_radius=0, height=34)
        banner.grid(row=1, column=0, sticky="ew")
        banner.grid_propagate(False)
        ctk.CTkLabel(banner,
                     text="⚠  AI-generated notes require provider review before chart entry",
                     font=ctk.CTkFont("Segoe UI", 11, "italic" ),
                     text_color="#B45309").place(x=14, rely=0.5, anchor="w")

        # Two panels
        panels = ctk.CTkFrame(main, fg_color=C["bg"], corner_radius=0)
        panels.grid(row=2, column=0, sticky="nsew", padx=12, pady=(10, 6))
        panels.grid_rowconfigure(1, weight=1)
        panels.grid_columnconfigure(0, weight=1)
        panels.grid_columnconfigure(2, weight=1)

        # Transcript header
        th = ctk.CTkFrame(panels, fg_color="transparent")
        th.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ctk.CTkLabel(th, text="Transcript",
                     font=ctk.CTkFont("Segoe UI", 13, weight="bold"),
                     text_color=C["text"]).pack(side="left")
        ctk.CTkLabel(th, text="Raw speech-to-text",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text3"]).pack(side="left", padx=8)

        self._transcript_box = T.make_textbox(panels)
        self._transcript_box.grid(row=1, column=0, sticky="nsew")

        # Divider
        ctk.CTkFrame(panels, fg_color=C["border"], width=1,
                     corner_radius=0).grid(row=0, column=1, rowspan=2,
                                           sticky="ns", padx=8)

        # Note header
        nh = ctk.CTkFrame(panels, fg_color="transparent")
        nh.grid(row=0, column=2, sticky="ew", pady=(0, 4))
        ctk.CTkLabel(nh, text="Generated Note",
                     font=ctk.CTkFont("Segoe UI", 13, weight="bold"),
                     text_color=C["text"]).pack(side="left")
        ctk.CTkLabel(nh, text="Editable — review before use",
                     font=ctk.CTkFont("Segoe UI", 10, slant="italic"),
                     text_color=C["text3"]).pack(side="left", padx=8)

        self._note_box = T.make_textbox(panels, fg_color=C["surface2"])
        self._note_box.grid(row=1, column=2, sticky="nsew")

        # Action bar
        action = ctk.CTkFrame(main, fg_color=C["surface"], corner_radius=0, height=52)
        action.grid(row=3, column=0, sticky="ew")
        action.grid_propagate(False)
        btn_row = ctk.CTkFrame(action, fg_color="transparent")
        btn_row.place(x=14, rely=0.5, anchor="w")
        T.primary_btn(btn_row, "📋  Copy to Clipboard",
                      command=self._copy_note, height=34).pack(side="left", padx=(0, 6))
        T.ghost_btn(btn_row, "💾  Save Note",
                    command=self._save_note, height=34).pack(side="left", padx=4)
        T.ghost_btn(btn_row, "➤  Open Dental",
                    command=self._send_to_open_dental, height=34).pack(side="left", padx=4)

        # Status bar
        self._status_label = ctk.CTkLabel(main, text="",
                                           font=ctk.CTkFont("Segoe UI", 10),
                                           text_color=C["text3"], anchor="w")
        self._status_label.grid(row=4, column=0, sticky="ew", padx=16, pady=(2, 6))

    # ── Devices ───────────────────────────────────────────────────────────────

    def _refresh_devices(self) -> None:
        devices = audio.list_input_devices()
        names = [f"[{d['index']}] {d['name']}" for d in devices]
        self._mic_devices = devices
        self._mic_combo.configure(values=names)
        if names:
            saved_idx = self.cfg.get("mic_device_index")
            if saved_idx is not None:
                match = next((n for n in names if n.startswith(f"[{saved_idx}]")), None)
                if match:
                    self._mic_combo.set(match)
                    return
            self._mic_combo.set(names[0])

    def _selected_device_index(self):
        sel = self._mic_combo.get()
        if not sel:
            return None
        try:
            return int(sel.split("]")[0].lstrip("["))
        except (ValueError, IndexError):
            return None

    # ── Template ──────────────────────────────────────────────────────────────

    def _on_template_change(self) -> None:
        if self.recorder.is_recording:
            return
        name = self._template_combo.get()
        self._template_var.set(name)
        self._template_chip.configure(text=name)
        template = get_template(name)
        self._note_box.configure(state="normal")
        self._note_box.delete("1.0", "end")
        self._note_box.insert("end", template.skeleton)
        self._regen_btn.configure(state="disabled")

    # ── Recording ─────────────────────────────────────────────────────────────

    def _toggle_recording(self) -> None:
        self._reset_inactivity_timer()
        if self.recorder.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        self.recorder.device_index = self._selected_device_index()
        try:
            self.recorder.start()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Microphone Error", str(e))
            return
        self._rec_btn.configure(text="⏹   Stop Dictation",
                                 fg_color=C["record"], hover_color="#C41E1E")
        self._status("Recording — speak clearly into the microphone.", "record")
        self._animate_indicator()
        self._transcript_box.configure(state="normal")
        self._transcript_box.delete("1.0", "end")
        self._transcript_box.insert("end", "Listening…")
        self._transcript_box.configure(state="disabled")
        self._live_running = True
        self._live_job = self.after(_LIVE_MS, self._live_tick)

    def _stop_recording(self) -> None:
        self._live_running = False
        if self._live_job:
            self.after_cancel(self._live_job)
            self._live_job = None
        self._wav_bytes = self.recorder.stop()
        self._rec_btn.configure(text="⏺   Start Dictation",
                                 fg_color=C["accent"], hover_color=C["accent_dark"])
        self._rec_indicator.configure(text="")
        if not self._wav_bytes:
            self._status("No audio captured — check microphone.", "warn")
            return
        self._status("Transcribing locally…", "normal")
        threading.Thread(target=self._run_transcription, daemon=True).start()

    def _animate_indicator(self) -> None:
        if not self.recorder.is_recording:
            self._rec_indicator.configure(text="")
            return
        cur = self._rec_indicator.cget("text")
        self._rec_indicator.configure(text="● REC" if not cur else "")
        self.after(600, self._animate_indicator)

    # ── Live transcription ────────────────────────────────────────────────────

    def _live_tick(self) -> None:
        if not self._live_running or not self.recorder.is_recording:
            return
        snap = self.recorder.get_snapshot()
        if snap:
            threading.Thread(target=self._live_worker, args=(snap,), daemon=True).start()
        self._live_job = self.after(_LIVE_MS, self._live_tick)

    def _live_worker(self, wav_bytes: bytes) -> None:
        try:
            from app.core import transcriber
            text = transcriber.transcribe(wav_bytes,
                backend=self.cfg.get("whisper_backend", "faster-whisper"),
                model_size=self.cfg.get("whisper_model", "base.en"),
                device=self.cfg.get("whisper_device", "cpu"),
                compute_type=self.cfg.get("whisper_compute_type", "float32"))
            if self._live_running and text:
                self.after(0, self._update_live, text)
        except Exception:
            pass

    def _update_live(self, text: str) -> None:
        if not self._live_running:
            return
        self._transcript_box.configure(state="normal")
        self._transcript_box.delete("1.0", "end")
        self._transcript_box.insert("end", text + " ▌")
        self._transcript_box.configure(state="disabled")

    # ── Transcription ─────────────────────────────────────────────────────────

    def _run_transcription(self) -> None:
        try:
            from app.core import transcriber
            text = transcriber.transcribe(self._wav_bytes,
                backend=self.cfg.get("whisper_backend", "faster-whisper"),
                model_size=self.cfg.get("whisper_model", "base.en"),
                device=self.cfg.get("whisper_device", "cpu"),
                compute_type=self.cfg.get("whisper_compute_type", "float32"))
            self.after(0, self._on_transcript, text)
        except Exception as e:
            self.after(0, self._status, f"Transcription error: {e}", "danger")

    def _on_transcript(self, text: str) -> None:
        self._transcript_box.configure(state="normal")
        self._transcript_box.delete("1.0", "end")
        self._transcript_box.insert("end", text)
        self._transcript_box.configure(state="disabled")
        self._status("Generating note with AI…", "normal")
        threading.Thread(target=self._run_note_gen, daemon=True).start()

    # ── Note generation ───────────────────────────────────────────────────────

    def _run_note_gen(self, transcript: str | None = None) -> None:
        if transcript is None:
            transcript = self._transcript_box.get("1.0", "end").strip()
        template = get_template(self._template_combo.get())
        try:
            note = note_generator.generate_note(
                transcript=transcript,
                template_instruction=template.llm_instruction,
                ollama_host=self.cfg.get("ollama_host", "http://localhost:11434"),
                model=self.cfg.get("ollama_model", "llama3"),
            )
            self.after(0, self._on_note_ready, note)
        except ConnectionError as e:
            self.after(0, self._status, "Ollama not reachable — open Settings.", "danger")
        except Exception as e:
            self.after(0, self._status, f"Note error: {e}", "danger")

    def _on_note_ready(self, note: str) -> None:
        self._note_box.configure(state="normal")
        self._note_box.delete("1.0", "end")
        self._note_box.insert("end", note)
        self._regen_btn.configure(state="normal")
        self._status("Note ready — review and edit before chart entry.", "success")
        self._log_action("NOTE_GENERATED")
        if self.cfg.get("save_raw_audio") and self._wav_bytes:
            self._save_audio_encrypted()
        try:
            note_history.save_entry(
                patient_id=self._patient_var.get().strip(),
                template=self._template_combo.get(),
                transcript=self._transcript_box.get("1.0", "end").strip(),
                note=note,
            )
        except Exception as e:
            print(f"[history] {e}")

    def _regenerate(self) -> None:
        self._status("Regenerating…", "normal")
        self._regen_btn.configure(state="disabled")
        threading.Thread(target=self._run_note_gen, daemon=True).start()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _copy_note(self) -> None:
        note = self._note_box.get("1.0", "end").strip()
        if not note:
            from tkinter import messagebox
            messagebox.showwarning("Empty Note", "No note to copy.")
            return
        self.clipboard_clear()
        self.clipboard_append(note)
        self._status("Copied to clipboard — paste into Open Dental.", "success")
        self._log_action("NOTE_COPIED_TO_CLIPBOARD", note)

    def _save_note(self) -> None:
        note = self._note_box.get("1.0", "end").strip()
        if not note:
            from tkinter import messagebox
            messagebox.showwarning("Empty Note", "No note to save.")
            return
        from tkinter import filedialog
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        patient = self._patient_var.get().strip().replace(" ", "_") or "unknown"
        dest = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")],
            initialfile=f"note_{patient}_{ts}.txt",
            initialdir=str(config.notes_dir()),
        )
        if not dest:
            return
        fernet = self.cfg.get("_fernet")
        dest_path = Path(dest)
        if fernet and self.cfg.get("encrypt_at_rest", True):
            from app.core.crypto import encrypt_text
            dest_path.write_bytes(encrypt_text(note, fernet))
            self._status(f"Saved (encrypted): {dest_path.name}", "success")
        else:
            dest_path.write_text(note, encoding="utf-8")
            self._status(f"Saved: {dest_path.name}", "success")
        self._log_action("NOTE_SAVED", note, extra={"file": str(dest_path)})

    def _save_audio_encrypted(self) -> None:
        fernet = self.cfg.get("_fernet")
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = config.audio_dir() / f"audio_{ts}.wav.enc"
        if fernet:
            dest.write_bytes(fernet.encrypt(self._wav_bytes))
        else:
            dest.with_suffix(".wav").write_bytes(self._wav_bytes)

    def _send_to_open_dental(self) -> None:
        from app.gui.od_dialog import OpenDentalDialog
        OpenDentalDialog(self.root, self.cfg,
                         note=self._note_box.get("1.0", "end").strip(),
                         patient_id=self._patient_var.get().strip(),
                         on_sent=lambda: self._log_action("NOTE_SENT_TO_OPEN_DENTAL",
                                                           self._note_box.get("1.0", "end")))

    # ── Navigation ────────────────────────────────────────────────────────────

    def _open_history(self) -> None:
        from app.gui.history_window import HistoryWindow
        HistoryWindow(self.root, on_load=self._load_from_history)

    def _load_from_history(self, patient_id, transcript, note, template) -> None:
        if patient_id:
            self._patient_var.set(patient_id)
            self._patient_chip.configure(text=f"Patient {patient_id}")
        self._transcript_box.configure(state="normal")
        self._transcript_box.delete("1.0", "end")
        self._transcript_box.insert("end", transcript)
        self._transcript_box.configure(state="disabled")
        self._note_box.configure(state="normal")
        self._note_box.delete("1.0", "end")
        self._note_box.insert("end", note)
        if template in template_names():
            self._template_combo.set(template)
            self._template_chip.configure(text=template)
        self._regen_btn.configure(state="normal")
        self._status("Loaded from history — review before chart entry.", "success")

    def _open_settings(self) -> None:
        from app.gui.settings_window import SettingsWindow
        SettingsWindow(self.root, self.cfg)

    def _open_audit(self) -> None:
        from app.gui.audit_window import AuditWindow
        AuditWindow(self.root, self.cfg)

    def _open_templates(self) -> None:
        from app.gui.templates_window import TemplatesWindow
        TemplatesWindow(self.root, on_close=self._refresh_templates)

    def _refresh_templates(self) -> None:
        from app.models.note_templates import template_names, load_templates
        load_templates()
        names = template_names()
        self._template_combo.configure(values=names)
        if self._template_combo.get() not in names:
            self._template_combo.set(names[0] if names else "")

    # ── Audit ─────────────────────────────────────────────────────────────────

    def _log_action(self, action, note="", extra=None) -> None:
        fernet = self.cfg.get("_fernet")
        if not fernet:
            return
        try:
            append_entry(action=action, fernet=fernet,
                         patient_id=self._patient_var.get().strip(),
                         note_text=note, extra=extra)
        except Exception as e:
            print(f"[audit] {e}")

    # ── Security ──────────────────────────────────────────────────────────────

    def _lock_app(self) -> None:
        self.pack_forget()
        from app.gui.login_window import LoginWindow
        LoginWindow(self.root, self.cfg,
                    on_authenticated=lambda: self.pack(fill="both", expand=True))

    def _reset_inactivity_timer(self) -> None:
        if self._inactivity_job:
            self.after_cancel(self._inactivity_job)
        ms = self.cfg.get("inactivity_timeout_minutes", 10) * 60 * 1000
        if ms > 0:
            self._inactivity_job = self.after(ms, self._lock_app)

    def _bind_hotkeys(self, root) -> None:
        root.bind("<F2>",  lambda _: self._toggle_recording())
        root.bind("<F12>", lambda _: self._lock_app())
        root.bind_all("<Key>",    lambda _: self._reset_inactivity_timer())
        root.bind_all("<Motion>", lambda _: self._reset_inactivity_timer())

    # ── Status ────────────────────────────────────────────────────────────────

    def _status(self, msg: str, level: str = "normal") -> None:
        colors = {"normal": C["text3"], "success": C["success"],
                  "warn": C["warn"], "danger": C["danger"], "record": C["record"]}
        self._status_label.configure(text=f"  {msg}",
                                      text_color=colors.get(level, C["text3"]))
