#!/usr/bin/env python3
"""Standalone popup notification — runs as its own process."""
import sys
import tkinter as tk

def show_popup(title: str, message: str):
    root = tk.Tk()
    root.title(title)
    root.attributes("-topmost", True)
    root.resizable(False, False)

    w, h = 420, 160
    screen_w = root.winfo_screenwidth()
    x = screen_w - w - 30
    y = 50
    root.geometry(f"{w}x{h}+{x}+{y}")

    root.configure(bg="#1e1e2e")

    tk.Label(
        root, text=title, font=("Helvetica", 15, "bold"),
        fg="#cdd6f4", bg="#1e1e2e", anchor="w", padx=20,
    ).pack(fill="x", pady=(18, 6))

    tk.Label(
        root, text=message, font=("Helvetica", 12),
        fg="#a6adc8", bg="#1e1e2e", anchor="w", padx=20,
        wraplength=380, justify="left",
    ).pack(fill="x", pady=(0, 12))

    btn_frame = tk.Frame(root, bg="#1e1e2e")
    btn_frame.pack(pady=(0, 12))

    tk.Button(
        btn_frame, text="OK", font=("Helvetica", 12, "bold"),
        fg="#1e1e2e", bg="#89b4fa", relief="flat",
        padx=30, pady=6, command=root.destroy, cursor="hand2",
    ).pack()

    root.after(10000, root.destroy)
    root.mainloop()

if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else "Agent Alert"
    m = sys.argv[2] if len(sys.argv) > 2 else "Notification"
    show_popup(t, m)