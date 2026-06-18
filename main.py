"""DentalScribe v2 — entry point."""
import subprocess
import sys
import time
import urllib.request
import customtkinter as ctk

from app.core import config as cfg_module


def _ensure_ollama() -> None:
    """Start ollama serve if it isn't already running."""
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return  # already up
    except Exception:
        pass
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        # Wait up to 10 s for Ollama to become ready
        for _ in range(20):
            time.sleep(0.5)
            try:
                urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1)
                return
            except Exception:
                pass
    except FileNotFoundError:
        pass  # ollama not installed — note_generator will surface the error
from app.gui import theme  # noqa: F401 — applies ctk appearance mode
from app.gui.login_window import LoginWindow
from app.gui.main_window import MainWindow
from app.gui.onboarding import OnboardingWindow, should_show


def main() -> None:
    _ensure_ollama()
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
