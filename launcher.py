import os
import socket
import sys
import threading
import time
import traceback
import tkinter as tk
import webbrowser
from tkinter import messagebox

import uvicorn

from app.main import app
from app.paths import DATA_DIR, STATIC_DIR

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"
ERROR_LOG = DATA_DIR / "vk_search_error.log"


def _dump_exception(exc_type, exc_value, exc_tb) -> None:
    """Пишем трейсбек в файл: у сборки без консоли stderr никуда не выводится."""
    try:
        with open(ERROR_LOG, "w", encoding="utf-8") as file:
            traceback.print_exception(exc_type, exc_value, exc_tb, file=file)
    except Exception:
        pass

    traceback.print_exception(exc_type, exc_value, exc_tb, file=sys.stderr)


def _ensure_std_streams() -> None:
    """В сборке без консоли (console=False) sys.stdout/stderr равны None,
    из-за чего падает логирование uvicorn."""
    for name in ("stdout", "stderr"):
        if getattr(sys, name) is None:
            stream = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115
            setattr(sys, name, stream)


_ensure_std_streams()

server = uvicorn.Server(
    uvicorn.Config(
        app,
        host=HOST,
        port=PORT,
        reload=False,
    ),
)


def _wait_for_server(timeout: float = 30.0) -> bool:
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            with socket.create_connection((HOST, PORT), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)

    return False


def _show_error(message: str) -> None:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("vk_search", message)
    root.destroy()


def _build_window() -> tk.Tk:
    root = tk.Tk()
    root.title("vk_search")
    root.resizable(False, False)

    icon_path = STATIC_DIR / "favicon.png"
    if icon_path.exists():
        try:
            icon = tk.PhotoImage(file=str(icon_path))
            root.iconphoto(True, icon)
            root.icon_image = icon  # держим ссылку, иначе Tk соберёт картинку
        except tk.TclError:
            pass

    frame = tk.Frame(root, padx=24, pady=16)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="Сервер запущен:", font=("Segoe UI", 10)).pack()
    tk.Label(
        frame,
        text=URL,
        font=("Segoe UI", 10, "bold"),
        fg="#2b6cb0",
    ).pack(pady=(0, 12))

    tk.Button(
        frame,
        text="Открыть сайт",
        width=22,
        command=lambda: webbrowser.open(URL),
    ).pack(pady=2)
    tk.Button(frame, text="Выход", width=22, command=root.destroy).pack(pady=2)

    tk.Label(
        frame,
        text="Закрытие окна останавливает сервер",
        fg="gray",
        font=("Segoe UI", 8),
    ).pack(pady=(10, 0))

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    return root


def main() -> None:
    sys.excepthook = _dump_exception
    threading.excepthook = lambda args: _dump_exception(
        args.exc_type, args.exc_value, args.exc_traceback
    )

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    if not _wait_for_server() or not server_thread.is_alive():
        _show_error(
            f"Не удалось запустить сервер на {URL}.\n"
            "Возможно, порт 8000 уже занят."
        )
        server.should_exit = True
        return

    webbrowser.open(URL)

    root = _build_window()
    root.mainloop()

    # Окно закрыто — останавливаем сервер.
    server.should_exit = True
    server_thread.join(timeout=5)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        _dump_exception(*sys.exc_info())

        try:
            messagebox.showerror(
                "vk_search",
                f"Не удалось запустить приложение.\nПодробности: {ERROR_LOG}",
            )
        except Exception:
            pass
