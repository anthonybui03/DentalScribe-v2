"""Open Dental send-note dialog — v2 CustomTkinter."""
import threading
import customtkinter as ctk
from app.gui.theme import C, make_font, primary_btn, ghost_btn, make_entry


class OdDialog(ctk.CTkToplevel):
    """Confirm and send a note to Open Dental via the REST API."""

    def __init__(self, parent, cfg: dict, patient_id: str, note_text: str):
        super().__init__(parent)
        self.cfg = cfg
        self.patient_id = patient_id
        self.note_text = note_text
        self.title("Send to Open Dental")
        self.geometry("520x460")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Send Note to Open Dental",
                     font=make_font(15, bold=True), text_color=C["text"]).grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 6))

        ctk.CTkLabel(self,
                     text="Review the information below before sending.\n"
                          "The note will be added to the patient's chart in Open Dental.",
                     font=make_font(11), text_color=C["text2"],
                     justify="left", wraplength=480).grid(
            row=1, column=0, sticky="w", padx=20, pady=(0, 10))

        info = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=10)
        info.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))
        info.grid_columnconfigure(1, weight=1)

        for row_idx, (label, value) in enumerate([
            ("Patient ID", self.patient_id or "(not set)"),
            ("Destination", self.cfg.get("od_api_url", "(not configured)")),
        ]):
            ctk.CTkLabel(info, text=label, font=make_font(10, bold=True),
                         text_color=C["text3"], width=100, anchor="w").grid(
                row=row_idx, column=0, padx=(14, 6), pady=6, sticky="w")
            ctk.CTkLabel(info, text=value, font=make_font(11),
                         text_color=C["text"], anchor="w").grid(
                row=row_idx, column=1, padx=(0, 14), pady=6, sticky="ew")

        ctk.CTkLabel(self, text="Note Preview",
                     font=make_font(10, bold=True), text_color=C["text3"]).grid(
            row=3, column=0, sticky="nw", padx=20, pady=(0, 2))

        preview = ctk.CTkTextbox(self, fg_color=C["surface"],
                                  text_color=C["text2"],
                                  font=ctk.CTkFont("Consolas", 10),
                                  corner_radius=8, border_width=1,
                                  border_color=C["border"],
                                  wrap="word", state="normal", height=140)
        preview.grid(row=4, column=0, sticky="nsew", padx=20, pady=(0, 10))
        preview.insert("end", self.note_text[:2000] + ("…" if len(self.note_text) > 2000 else ""))
        preview.configure(state="disabled")

        self._status = ctk.CTkLabel(self, text="",
                                     font=make_font(11), text_color=C["text2"])
        self._status.grid(row=5, column=0, pady=(0, 4))

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 16))
        ghost_btn(btn_bar, "Cancel", command=self.destroy, height=36).pack(side="left")
        self._send_btn = primary_btn(btn_bar, "Send to Open Dental",
                                      command=self._send, height=36)
        self._send_btn.pack(side="right")

        if not self.cfg.get("od_api_url"):
            self._send_btn.configure(state="disabled")
            self._status.configure(
                text="Open Dental API not configured. Go to Settings → Open Dental.",
                text_color=C["warn"])

    def _send(self) -> None:
        self._send_btn.configure(state="disabled", text="Sending…")
        self._status.configure(text="Connecting to Open Dental…", text_color=C["text2"])
        threading.Thread(target=self._do_send, daemon=True).start()

    def _do_send(self) -> None:
        from app.core.open_dental import OpenDentalConnector
        try:
            conn = OpenDentalConnector(
                self.cfg.get("od_api_url", ""),
                self.cfg.get("od_developer_key", ""),
                self.cfg.get("od_customer_key", ""),
            )
            ok, msg = conn.send_chart_note(self.patient_id, self.note_text)
        except Exception as exc:
            ok, msg = False, str(exc)
        self.after(0, self._on_result, ok, msg)

    def _on_result(self, ok: bool, msg: str) -> None:
        if ok:
            self._status.configure(text="✓ Note sent successfully.", text_color=C["success"])
            self._send_btn.configure(state="disabled", text="Sent ✓")
            self.after(1500, self.destroy)
        else:
            self._status.configure(text=f"✗ {msg}", text_color=C["danger"])
            self._send_btn.configure(state="normal", text="Retry")
