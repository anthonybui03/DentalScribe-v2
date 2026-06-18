"""Audit log viewer — v2 CustomTkinter."""
import customtkinter as ctk
from app.gui.theme import C, make_font, ghost_btn, make_entry
from app.core.audit_log import read_entries


class AuditWindow(ctk.CTkToplevel):

    def __init__(self, parent, cfg: dict):
        super().__init__(parent)
        self.cfg = cfg
        self.title("Audit Log — DentalScribe v2")
        self.geometry("840x560")
        self.resizable(True, True)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._all_entries: list[dict] = []
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        ctk.CTkLabel(top, text="Audit Log", font=make_font(16, bold=True),
                     text_color=C["text"]).pack(side="left")
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())
        search = make_entry(top, textvariable=self._search_var,
                            placeholder="Filter by user, action, or date…", width=300)
        search.pack(side="right", padx=(8, 0))
        ghost_btn(top, "Refresh", command=self._load,
                  height=30, width=80).pack(side="right")

        # Table
        table_frame = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=12)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(4, 12))
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(table_frame, fg_color=C["bg"], corner_radius=0, height=36)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        for col, (label, width) in enumerate({
            "Timestamp": 180, "User": 120, "Action": 200, "Note Preview": 0
        }.items()):
            kw = {"width": width} if width else {}
            ctk.CTkLabel(hdr, text=label, font=make_font(10, bold=True),
                         text_color=C["text3"], anchor="w", **kw).grid(
                row=0, column=col, padx=(14 if col == 0 else 6, 6),
                pady=8, sticky="w")
        hdr.grid_columnconfigure(3, weight=1)

        self._scroll = ctk.CTkScrollableFrame(table_frame, fg_color="transparent",
                                               scrollbar_button_color=C["border"])
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self._scroll.grid_columnconfigure(3, weight=1)

        # Footer
        self._count_label = ctk.CTkLabel(table_frame, text="",
                                          font=make_font(10), text_color=C["text3"])
        self._count_label.grid(row=2, column=0, pady=(4, 8))

    def _load(self) -> None:
        fernet = self.cfg.get("_fernet")
        if fernet:
            self._all_entries = read_entries(fernet)
        else:
            self._all_entries = [{"timestamp": "–", "user": "–",
                                   "action": "PIN required to view audit log",
                                   "detail": ""}]
        self._apply_filter()

    def _apply_filter(self) -> None:
        q = self._search_var.get().lower()
        shown = [e for e in self._all_entries
                 if not q or any(q in str(v).lower() for v in e.values() if isinstance(v, str))]
        self._render(shown)
        self._count_label.configure(
            text=f"Showing {len(shown)} of {len(self._all_entries)} entries")

    def _render(self, entries: list[dict]) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()
        for row_idx, entry in enumerate(reversed(entries)):
            bg = C["surface"] if row_idx % 2 == 0 else C["surface2"]
            for col, key in enumerate(["ts", "user", "action", "note_preview"]):
                val = str(entry.get(key, ""))
                ctk.CTkLabel(self._scroll, text=val,
                             font=make_font(10 if col == 3 else 11),
                             text_color=C["text2"] if col else C["text"],
                             anchor="w",
                             fg_color=bg,
                             corner_radius=0).grid(
                    row=row_idx, column=col,
                    padx=(14 if col == 0 else 6, 6), pady=3, sticky="ew")
        self._scroll.grid_columnconfigure(3, weight=1)
