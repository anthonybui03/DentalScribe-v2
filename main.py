"""DentalScribe v2 — entry point."""
import sys
import customtkinter as ctk

from app.core import config as cfg_module
from app.gui import theme  # noqa: F401 — applies ctk appearance mode
from app.gui.login_window import LoginWindow
from app.gui.main_window import MainWindow
from app.gui.onboarding import OnboardingWindow, should_show


def main() -> None:
    cfg = cfg_module.load()

    root = ctk.CTk()
    root.title("DentalScribe v2")
    root.geometry("1200x740")
    root.minsize(900, 600)
    root.configure(fg_color="#0F172A")

    main_win: MainWindow | None = None

    def launch_main() -> None:
        nonlocal main_win
        main_win = MainWindow(root, cfg)
        if should_show(cfg):
            root.after(400, lambda: OnboardingWindow(root, cfg))

    if cfg.get("pin_hash"):
        LoginWindow(root, cfg, on_authenticated=launch_main)
    else:
        launch_main()

    root.mainloop()


if __name__ == "__main__":
    main()
