"""Tkinter PDF reader used by Kwiddle.

PDFs are rendered page-by-page with PyMuPDF, keeping the document local.
"""
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk


def open_pdf_reader(parent, path, title=None):
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "PDF support needs PyMuPDF. Reinstall or upgrade Kwiddle with "
            "'pip install --upgrade kwiddle'."
        ) from exc

    path = Path(path)
    document = fitz.open(path)
    if document.needs_pass:
        document.close()
        password = tk.simpledialog.askstring(
            "Password-protected PDF", "Enter the PDF password:",
            parent=parent, show="*"
        )
        if not password or not document.authenticate(password):
            raise RuntimeError("The PDF password was missing or incorrect.")

    viewer = tk.Toplevel(parent)
    viewer.title(f"Kwiddle — {title or path.name}")
    viewer.geometry("1000x760")
    viewer.minsize(480, 360)
    state = {"page": 0, "zoom": 1.15, "fit": True, "photo": None}

    toolbar = tk.Frame(viewer, padx=8, pady=8)
    toolbar.pack(fill="x")
    canvas_frame = tk.Frame(viewer)
    canvas_frame.pack(fill="both", expand=True)
    canvas = tk.Canvas(canvas_frame, background="#555b66", highlightthickness=0)
    ybar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    xbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
    canvas.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
    ybar.pack(side="right", fill="y")
    xbar.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)
    page_info = tk.StringVar()

    def render():
        page = document.load_page(state["page"])
        available = max(250, canvas.winfo_width() - 36)
        zoom = min(state["zoom"], available / max(1, page.rect.width)) if state["fit"] else state["zoom"]
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        state["photo"] = ImageTk.PhotoImage(image)
        canvas.delete("all")
        canvas.create_image(18, 18, anchor="nw", image=state["photo"])
        canvas.configure(scrollregion=(0, 0, pix.width + 36, pix.height + 36))
        page_info.set(f"Page {state['page'] + 1} of {len(document)}")

    def previous():
        if state["page"] > 0:
            state["page"] -= 1
            render()

    def next_page():
        if state["page"] + 1 < len(document):
            state["page"] += 1
            render()

    def zoom(delta):
        state["fit"] = False
        state["zoom"] = min(4.0, max(0.35, state["zoom"] + delta))
        render()

    def fit_width():
        state["fit"] = True
        render()

    def go_to_page(_event=None):
        from tkinter import simpledialog
        value = simpledialog.askinteger(
            "Go to page", f"Enter a page number (1–{len(document)}):",
            parent=viewer, minvalue=1, maxvalue=len(document)
        )
        if value:
            state["page"] = value - 1
            render()

    def fullscreen(_event=None):
        enabled = not bool(viewer.attributes("-fullscreen"))
        viewer.attributes("-fullscreen", enabled)
        full_button.config(text="Exit full screen" if enabled else "Full screen")
        viewer.after_idle(render)

    tk.Button(toolbar, text="← Previous", command=previous).pack(side="left", padx=2)
    tk.Button(toolbar, text="Next →", command=next_page).pack(side="left", padx=2)
    tk.Button(toolbar, text="−", command=lambda: zoom(-0.15)).pack(side="left", padx=2)
    tk.Button(toolbar, text="+", command=lambda: zoom(0.15)).pack(side="left", padx=2)
    tk.Button(toolbar, text="Fit width", command=fit_width).pack(side="left", padx=2)
    tk.Button(toolbar, text="Go to page", command=go_to_page).pack(side="left", padx=2)
    tk.Label(toolbar, textvariable=page_info, padx=8).pack(side="left", expand=True)
    full_button = tk.Button(toolbar, text="Full screen", command=fullscreen)
    full_button.pack(side="right", padx=2)
    tk.Button(toolbar, text="Close", command=viewer.destroy).pack(side="right", padx=2)

    viewer.bind("<Left>", lambda _e: previous())
    viewer.bind("<Right>", lambda _e: next_page())
    viewer.bind("<F11>", fullscreen)
    viewer.bind("<Escape>", lambda _e: viewer.attributes("-fullscreen", False))
    viewer.bind("<Configure>", lambda _e: viewer.after_idle(render) if state["fit"] else None)
    viewer.protocol("WM_DELETE_WINDOW", lambda: (document.close(), viewer.destroy()))
    viewer.after(100, render)
    return viewer
