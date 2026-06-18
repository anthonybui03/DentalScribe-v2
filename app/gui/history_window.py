"""Note history viewer — v2 CustomTkinter."""
import customtkinter as ctk
from app.gui.theme import C, make_font, ghost_btn, primary_btn, make_entry, make_textbox
from app.core.note_history import load_entries, delete_entry


class HistoryWindow(ctk.CTkToplevel):

    def __init__(self, parent, cfg: dict = None, on_load=None):
        super().__init__(parent)
        self.cfg = cfg
        self.on_load = on_load  # callback(transcript, note, template)
        self.title("Note History — DentalScribe v2")
        self.geometry("900x600")
        self.resizable(True, True)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._entries: list[dict] = []
        self._selected_idx: int | None = None
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(1, weight=1)

        # ---- Left: list ----
        left = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(left, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(12, 6))
        ctk.CTkLabel(top, text="Note History",
                     font=make_font(13, bold=True), text_color=C["text"]).pack(side="left")

        self._filter_var = ctk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
        make_entry(left, textvariable=self._filter_var,
                   placeholder="Filter by patient ID…",
                   height=30).grid(row=1, column=0, sticky="ew",
                                   padx=10, pady=(0, 6))

        self._list = ctk.CTkScrollableFrame(left, fg_color="transparent",
                                             scrollbar_button_color=C["border"])
        self._list.grid(row=2, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self._list.grid_columnconfigure(0, weight=1)

        # ---- Right: detail ----
        right = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        right.grid_rowconfigure(2, weight=1)
        right.grid_rowconfigure(4, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._detail_header = ctk.CTkLabel(right, text="Select a note on the left",
                                            font=make_font(12), text_color=C["text2"])
        self._detail_header.grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))

        ctk.CTkLabel(right, text="Transcript",
                     font=make_font(10, bold=True), text_color=C["text3"]).grid(
            row=1, column=0, sticky="w", padx=14, pady=(0, 2))
        self._transcript_box = make_textbox(right, height=130)
        self._transcript_box.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 8))
        self._transcript_box.configure(state="disabled")

        ctk.CTkLabel(right, text="Generated Note",
                     font=make_font(10, bold=True), text_color=C["text3"]).grid(
            row=3, column=0, sticky="w", padx=14, pady=(0, 2))
        self._note_box = make_textbox(right)
        self._note_box.grid(row=4, column=0, sticky="nsew", padx=14, pady=(0, 8))
        self._note_box.configure(state="disabled")

        btn_bar = ctk.CTkFrame(right, fg_color="transparent")
        btn_bar.grid(row=5, column=0, sticky="ew", padx=14, pady=(0, 12))
        self._delete_btn = ghost_btn(btn_bar, "Delete Entry", command=self._delete,
                                      height=32, text_color=C["danger"],
                                      border_color=C["danger"])
        self._delete_btn.pack(side="left")
        self._delete_btn.configure(state="disabled")
        self._load_btn = primary_btn(btn_bar, "Load into Editor",
                                      command=self._load_into_editor, height=32)
        self._load_btn.pack(side="right")
        self._load_btn.configure(state="disabled")

    def _load(self) -> None:
        self._entries = load_entries()
        self._apply_filter()

    def _apply_filter(self) -> None:
        q = self._filter_var.get().lower()
        shown = [e for e in self._entries
                 if not q or q in str(e.get("patient_id", "")).lower()]
        self._render_list(shown)

    def _render_list(self, entries: list[dict]) -> None:
        for w in self._list.winfo_children():
            w.destroy()
        for idx, entry in enumerate(entries):
            ts = entry.get("timestamp", "")[:16].replace("T", " ")
            pid = entry.get("patient_id") or "(no patient)"
            tmpl = entry.get("template", "")
            label = f"{ts}\n{pid}  ·  {tmpl}"
            btn = ctk.CTkButton(self._list, text=label, anchor="w",
                                fg_color="transparent",
                                hover_color=C["border"],
                                text_color=C["text2"],
                                font=make_font(10), height=52, corner_radius=6,
                                command=lambda e=entry: self._select(e))
            btn.grid(sticky="ew", padx=4, pady=2)

    def _select(self, entry: dict) -> None:
        self._selected = entry
        ts = entry.get("timestamp", "")[:19].replace("T", " ")
        pid = entry.get("patient_id") or "(no patient)"
        self._detail_header.configure(
            text=f"{ts}  ·  {pid}  ·  {entry.get('template', '')}",
            text_color=C["text"])

        self._transcript_box.configure(state="normal")
        self._transcript_box.delete("1.0", "end")
        self._transcript_box.insert("end", entry.get("transcript", ""))
        self._transcript_box.configure(state="disabled")

        self._note_box.configure(state="normal")
        self._note_box.delete("1.0", "end")
        self._note_box.insert("end", entry.get("note", ""))
        self._note_box.configure(state="disabled")

        self._delete_btn.configure(state="normal")
        self._load_btn.configure(state="normal")

    def _delete(self) -> None:
        if not self._selected:
            return
        delete_entry(self._selected.get("timestamp", ""))
        self._selected = None
        self._detail_header.configure(text="Select a note on the left",
                                       text_color=C["text2"])
        self._transcript_box.configure(state="normal")
        self._transcript_box.delete("1.0", "end")
        self._transcript_box.configure(state="disabled")
        self._note_box.configure(state="normal")
        self._note_box.delete("1.0", "end")
        self._note_box.configure(state="disabled")
        self._delete_btn.configure(state="disabled")
        self._load_btn.configure(state="disabled")
        self._load()

    def _load_into_editor(self) -> None:
        if not self._selected or not self.on_load:
            return
        self.on_load(
            self._selected.get("patient_id", ""),
            self._selected.get("transcript", ""),
            self._selected.get("note", ""),
            self._selected.get("template", ""),
        )
        self.destroy()
