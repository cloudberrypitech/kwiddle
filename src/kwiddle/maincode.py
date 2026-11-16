import webbrowser
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageTk
from tkinter import (
    Tk,
    Toplevel,
    Frame,
    Label,
    Button,
    Canvas,
    Scrollbar,
    PanedWindow,
    Text,
    END,
    LEFT,
    RIGHT,
    Y,
    BOTH,
    VERTICAL,
    NORMAL,
    DISABLED,
    RAISED,
    messagebox,
)
from .reader_features import load_progress, save_progress, document_headings, fit_horizontal_margins
from kwloader import (
    SUPPORTED_EXTENSIONS,
    BookDocument,
    TextBlock,
    TextStyle,
    ImageAsset,
    load_book,
)


def run():
    global window
    global books
    global book_files
    global book_buttons
    global empty_library_label
    global library_count_label
    global library_signature

    window = None

    REPO_URL = "https://github.com/cloudberrypitech/kwiddle"
    BOOKS_FOLDER = Path(__file__).resolve().parent / "books"
    AUTO_UPDATE_INTERVAL = 2000

    books = {}
    book_files = {}
    book_buttons = {}

    empty_library_label = None
    library_count_label = None
    library_signature = None

    def contribute_repo():
        answer = messagebox.askyesno(
            parent=window,
            title="Contribute",
            message="Do you want to star the Kwiddle repo on GitHub?",
        )

        if not answer:
            return

        try:
            webbrowser.open(REPO_URL)
        except Exception as error:
            messagebox.showerror(
                parent=window,
                title="Contribute",
                message=f"Could not open the repository.\n\n{error}",
            )
            return

        messagebox.showinfo(
            parent=window,
            title="Contribute",
            message="Thank you for contributing to Kwiddle.",
        )

    def size_to_tk(size):
        """Convert a point size into a Tkinter font size."""
        if not size:
            return 14

        try:
            return max(6, int(round(float(size))))
        except Exception:
            return 14

    def make_font(style: TextStyle):
        font_name = style.font or "Arial"
        size = size_to_tk(style.size)

        if style.bold and style.italic:
            return (font_name, size, "bold", "italic")
        if style.bold:
            return (font_name, size, "bold", "roman")
        if style.italic:
            return (font_name, size, "normal", "italic")

        return (font_name, size, "normal", "roman")

    def configure_text_tag(text_widget, tag_name, style, align=None, attributes=None):
        options = {"font": make_font(style)}
        if style.underline:
            options["underline"] = True
        if getattr(style, "strike", False):
            options["overstrike"] = True
        if getattr(style, "color", None):
            options["foreground"] = style.color
        if getattr(style, "background_color", None) and style.background_color != "transparent":
            options["background"] = style.background_color
        if getattr(style, "superscript", False):
            options["offset"] = 4
        elif getattr(style, "subscript", False):
            options["offset"] = -3
        if align == "center":
            options["justify"] = "center"
        elif align == "right":
            options["justify"] = "right"
        else:
            options["justify"] = "left"
        attributes = attributes or {}
        for source, target in (("margin_left", "lmargin1"),
                               ("margin_right", "rmargin"),
                               ("text_indent", "lmargin2"),
                               ("margin_top", "spacing1"),
                               ("margin_bottom", "spacing3")):
            value = attributes.get(source)
            if value:
                try:
                    # kwloader stores original ODF length strings.
                    import re
                    match = re.match(r"\s*(-?\d+(?:\.\d+)?)\s*(pt|px|cm|mm|in)?", str(value))
                    if match:
                        number = float(match.group(1))
                        unit = match.group(2) or "pt"
                        points = number * {"pt": 1, "px": .75, "cm": 28.346, "mm": 2.835, "in": 72}[unit]
                        options[target] = max(0, int(points * 1.33))
                except Exception:
                    pass
        background = attributes.get("background_color")
        if background and background != "transparent":
            options["background"] = background
        border = attributes.get("border")
        if border and border != "none":
            options.update({"borderwidth": 1, "relief": "solid"})
        line_height = attributes.get("line_height")
        if line_height:
            try:
                import re
                match = re.match(r"\\s*(\\d+(?:\\.\\d+)?)\\s*(pt|px|cm|mm|in)?", str(line_height))
                if match:
                    number = float(match.group(1))
                    unit = match.group(2) or "pt"
                    points = number * {"pt": 1, "px": .75, "cm": 28.346, "mm": 2.835, "in": 72}[unit]
                    options["spacing2"] = max(0, int(points * 1.33))
            except Exception:
                pass
        text_widget.tag_configure(tag_name, **options)

    def _insert_image(text_widget, asset):
        if asset is None or not asset.data:
            text_widget.insert(END, "[Image unavailable]")
            return
        try:
            image_bytes = asset.data
            if asset.mime_type == "image/svg+xml" or asset.name.lower().endswith((".svg", ".svgz")):
                import cairosvg
                if asset.name.lower().endswith(".svgz"):
                    import gzip
                    image_bytes = gzip.decompress(image_bytes)
                image_bytes = cairosvg.svg2png(bytestring=image_bytes)
            image = Image.open(BytesIO(image_bytes)).convert("RGBA")
            # Honour ODF frame dimensions where present, but keep images within
            # the reader viewport so unusually large page graphics remain usable.
            import re
            def dimension_px(value):
                if not value:
                    return None
                match = re.match(r"\s*(\d+(?:\.\d+)?)\s*(pt|px|cm|mm|in)?", str(value).lower())
                if not match:
                    return None
                number = float(match.group(1)); unit = match.group(2) or "px"
                return int(number * {"pt": 96 / 72, "px": 1, "cm": 96 / 2.54,
                                     "mm": 96 / 25.4, "in": 96}[unit])
            requested_w = dimension_px(getattr(asset, "width", None))
            requested_h = dimension_px(getattr(asset, "height", None))
            if requested_w or requested_h:
                ratio = image.width / max(1, image.height)
                target_w = requested_w or int(requested_h * ratio)
                target_h = requested_h or int(target_w / ratio)
                scale = min(1.0, 680 / max(1, target_w), 520 / max(1, target_h))
                image = image.resize((max(1, int(target_w * scale)),
                                      max(1, int(target_h * scale))), Image.Resampling.LANCZOS)
            else:
                image.thumbnail((680, 520), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            if not hasattr(text_widget, "_kwiddle_image_refs"):
                text_widget._kwiddle_image_refs = []
            text_widget._kwiddle_image_refs.append(photo)
            text_widget.image_create(END, image=photo, align="baseline")
            if asset.alt_text or asset.title:
                text_widget.insert(END, "\n" + (asset.alt_text or asset.title) + "\n")
        except Exception as error:
            text_widget.insert(END, f"[Could not display image: {error}]")

    def _list_marker(index, list_style):
        levels = (list_style or {}).get("levels", [])
        level = levels[0] if levels else {}
        kind = level.get("kind", "")
        if kind == "list-level-style-number":
            fmt = level.get("num_format") or "1"
            start = int(level.get("start_value") or 1) if str(level.get("start_value") or "1").isdigit() else 1
            value = start + index
            if fmt in {"a", "A"}:
                number = value
                label = ""
                while number > 0:
                    number, rem = divmod(number - 1, 26)
                    label = chr((97 if fmt == "a" else 65) + rem) + label
            elif fmt in {"i", "I"}:
                number = value
                pairs = ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))
                label = ""
                for amount, symbol in pairs:
                    while number >= amount:
                        label += symbol
                        number -= amount
                if fmt == "i":
                    label = label.lower()
            else:
                label = str(value)
            return f"{level.get('num_prefix', '')}{label}{level.get('num_suffix', '.')} "
        return (level.get("bullet_char") or "•") + " "

    def insert_block(text_widget, block: TextBlock, depth=0, list_marker=None, compact=False):
        """Render the shared document model, including embedded media and styled tables."""
        if block.kind == "page_break":
            text_widget.insert(END, "\n\n" + "─" * 32 + "\n\n")
            return
        if block.attributes.get("break_before") in {"page", "column"}:
            text_widget.insert(END, "\n\n" + "─" * 32 + "\n\n")
        if block.kind == "list":
            list_style = block.attributes.get("list_style", {})
            for index, child in enumerate(block.children):
                marker = _list_marker(index, list_style)
                insert_block(text_widget, child, depth, marker if child.kind == "list_item" else None, compact)
            return
        if block.kind in {"section", "toc", "index", "list_item", "list_header"}:
            if block.kind == "list_item" and list_marker:
                text_widget.insert(END, "    " * depth + list_marker)
            elif block.kind == "list_header":
                text_widget.insert(END, "    " * depth)
            for child in block.children:
                insert_block(text_widget, child, depth + (1 if block.kind in {"list_item", "list"} else 0), compact=compact)
            return
        if block.kind == "table":
            table_tag = f"kwiddle_table_{id(block)}"
            max_columns = max((len(row.children) for row in block.children), default=1)
            available_width = max(360, text_widget.winfo_width() - 90)
            column_width = max(100, available_width // max(1, max_columns))
            tab_stops = tuple(column_width * index for index in range(1, max_columns + 1))
            text_widget.tag_configure(table_tag, lmargin1=8, rmargin=8, tabs=tab_stops)
            text_widget.insert(END, "\n")
            for row_index, row in enumerate(block.children):
                row_start = text_widget.index(END)
                for index, cell in enumerate(row.children):
                    if cell.attributes.get("covered"):
                        continue
                    if index:
                        text_widget.insert(END, "\t")
                    cell_start = text_widget.index(END)
                    for paragraph_index, paragraph in enumerate(cell.children):
                        if paragraph_index:
                            text_widget.insert(END, " ")
                        insert_block(text_widget, paragraph, depth, compact=True)
                    cell_end = text_widget.index(END)
                    cell_style = getattr(cell, "style", None) or TextStyle()
                    cell_tag = f"kwiddle_cell_{id(cell)}"
                    configure_text_tag(
                        text_widget, cell_tag, cell_style,
                        cell.attributes.get("text_align"),
                    )
                    options = {}
                    background = cell.attributes.get("background_color") or cell_style.background_color
                    if background and background != "transparent":
                        options["background"] = background
                    border = cell.attributes.get("border")
                    if border and border != "none":
                        options.update({"borderwidth": 1, "relief": "solid"})
                    if cell.attributes.get("vertical_align") == "middle":
                        options["offset"] = 1
                    if options:
                        text_widget.tag_configure(cell_tag, **options)
                    text_widget.tag_add(cell_tag, cell_start, cell_end)
                row_end = text_widget.index(END)
                text_widget.tag_add(table_tag, row_start, row_end)
                row_props = row.attributes.get("style_properties", {})
                row_bg = row_props.get("{urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0}background-color")
                if row_bg:
                    row_tag = f"kwiddle_row_{id(row)}"
                    text_widget.tag_configure(row_tag, background=row_bg)
                    text_widget.tag_add(row_tag, row_start, row_end)
                text_widget.insert(END, "\n")
                if row_index < len(block.children) - 1:
                    text_widget.insert(END, "─" * min(75, max(20, available_width // 9)) + "\n")
            text_widget.insert(END, "\n")
            return

        if block.kind == "image":
            _insert_image(text_widget, block.image)
            if not compact:
                text_widget.insert(END, "\n\n")
            return

        if block.kind == "heading":
            try:
                level = int(block.attributes.get("outline_level") or 1)
            except Exception:
                level = 1
            default_style = TextStyle(bold=True, size=max(14, 22 - (level - 1) * 2))
        else:
            default_style = TextStyle(size=14)

        block_style = getattr(block, "style", TextStyle())
        for index, run in enumerate(block.runs):
            if run.image is not None:
                _insert_image(text_widget, run.image)
                continue
            style = run.style
            effective_size = style.size if style.size is not None else (block_style.size if block_style.size is not None else default_style.size)
            if getattr(style, "superscript", False) or getattr(style, "subscript", False):
                effective_size = max(6, int((effective_size or 14) * 0.7))
            effective = TextStyle(
                bold=style.bold or block_style.bold or default_style.bold,
                italic=style.italic or block_style.italic or default_style.italic,
                underline=style.underline or block_style.underline or default_style.underline,
                size=effective_size,
                font=style.font or block_style.font or default_style.font,
                color=style.color or block_style.color,
                background_color=style.background_color or block_style.background_color,
                strike=getattr(style, "strike", False) or getattr(block_style, "strike", False),
                overline=getattr(style, "overline", False) or getattr(block_style, "overline", False),
                superscript=getattr(style, "superscript", False) or getattr(block_style, "superscript", False),
                subscript=getattr(style, "subscript", False) or getattr(block_style, "subscript", False),
            )
            tag_name = f"kwloader_{id(block)}_{index}"
            configure_text_tag(text_widget, tag_name, effective, block.align, block.attributes)
            if run.link:
                text_widget.tag_configure(tag_name, foreground="#1769aa", underline=True)
                text_widget.tag_bind(tag_name, "<Button-1>",
                                     lambda event, url=run.link: webbrowser.open(url))
            text_widget.insert(END, run.text, tag_name)

        if not compact:
            text_widget.insert(END, "\n\n")
        if block.attributes.get("break_after") in {"page", "column"}:
            text_widget.insert(END, "\n\n" + "─" * 32 + "\n\n")

    def build_document_pages(document: BookDocument):
        """
        Split a loaded document into readable pages.
        """
        if document is None:
            return [[]]

        blocks = [
            block for block in document.blocks
            if block.text.strip() or block.kind in {"image", "table", "list", "page_break"}
            or any(run.image is not None for run in block.runs)
        ]

        if not blocks:
            return [[]]

        pages = []
        current_page = []
        current_chars = 0

        max_blocks = 8
        max_characters = 1800

        for block in blocks:
            block_text = block.text.strip()

            would_overflow = bool(current_page) and (
                len(current_page) >= max_blocks
                or current_chars + len(block_text) > max_characters
            )

            if would_overflow:
                pages.append(current_page)
                current_page = []
                current_chars = 0

            current_page.append(block)
            current_chars += len(block_text)

        if current_page:
            pages.append(current_page)

        return pages or [[]]

    def scan_books():
        global books
        global book_files

        BOOKS_FOLDER.mkdir(
            parents=True,
            exist_ok=True,
        )

        new_books = {}
        new_files = {}

        print()
        print("=" * 60)
        print("[Kwiddle] Scanning book library")
        print(f"[Kwiddle] Books folder: {BOOKS_FOLDER}")
        print(f"[Kwiddle] Folder exists: {BOOKS_FOLDER.exists()}")
        print("=" * 60)

        all_files = sorted(
            BOOKS_FOLDER.rglob("*"),
            key=lambda path: str(path).lower(),
        )

        found_count = 0

        for file_path in all_files:
            if not file_path.is_file():
                continue

            if (
                file_path.name.startswith("~$")
                or file_path.name.startswith(".~lock.")
            ):
                continue

            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            found_count += 1

            print(f"[Kwiddle] Found book: {file_path}")

            try:
                document = load_book(file_path)
                title = document.title or file_path.stem

                original_title = title
                number = 2

                while title in new_books:
                    title = f"{original_title} ({number})"
                    number += 1

                new_books[title] = document
                new_files[title] = file_path

                print(f"[Kwiddle] Book ready: {title}")

            except Exception as error:
                print(f"[Kwiddle] ERROR loading {file_path}:")
                print(f"    {type(error).__name__}: {error}")

        books = new_books
        book_files = new_files

        print(f"[Kwiddle] Files found: {found_count}")
        print(f"[Kwiddle] Books loaded: {len(books)}")
        print("=" * 60)
        print()

        return books

    def get_library_signature():
        BOOKS_FOLDER.mkdir(
            parents=True,
            exist_ok=True,
        )

        signature = []

        for file_path in BOOKS_FOLDER.rglob("*"):
            if not file_path.is_file():
                continue

            if (
                file_path.name.startswith("~$")
                or file_path.name.startswith(".~lock.")
            ):
                continue

            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            try:
                stat = file_path.stat()
                relative_path = file_path.relative_to(BOOKS_FOLDER)

                signature.append(
                    (
                        str(relative_path),
                        stat.st_mtime_ns,
                        stat.st_size,
                    )
                )
            except OSError:
                continue

        return tuple(sorted(signature))

    def open_book(title):
        document = books.get(title)

        if document is None:
            messagebox.showerror(
                parent=window,
                title="Kwiddle",
                message=f"Could not find the loaded document for:\n\n{title}",
            )
            return

        file_path = book_files.get(title)

        if file_path is None:
            messagebox.showerror(
                parent=window,
                title="Kwiddle",
                message=f"Could not find the file for:\n\n{title}",
            )
            return

        print(f"[Kwiddle] Opening: {file_path}")

        book_window = Toplevel(window)
        book_window.title(f"Kwiddle - {title}")
        book_window.geometry("900x700")
        book_window.minsize(500, 400)

        reader_pane = PanedWindow(
            book_window,
            orient=VERTICAL,
            sashwidth=7,
            sashrelief=RAISED,
            showhandle=True,
        )
        reader_pane.pack(
            fill=BOTH,
            expand=True,
        )

        text_frame = Frame(reader_pane)
        navigation_frame = Frame(reader_pane)

        reader_pane.add(
            text_frame,
            minsize=250,
            stretch="always",
        )
        reader_pane.add(
            navigation_frame,
            minsize=75,
            stretch="never",
        )

        text = Text(
            text_frame,
            wrap="word",
            font=("Arial", 14),
            padx=20,
            pady=20,
            undo=False,
        )
        text.pack(
            side=LEFT,
            fill=BOTH,
            expand=True,
            padx=(10, 0),
            pady=10,
        )

        scrollbar = Scrollbar(
            text_frame,
            orient=VERTICAL,
            command=text.yview,
        )
        scrollbar.pack(
            side=RIGHT,
            fill=Y,
            padx=(0, 10),
            pady=10,
        )

        text.configure(
            yscrollcommand=scrollbar.set,
        )

        pages = build_document_pages(document)
        progress_key = str(file_path.resolve())
        saved = load_progress(progress_key)
        current_page = min(max(0, int(saved.get("page", 0) or 0)), len(pages) - 1)
        reader_font_size = 14
        reader_theme = "Light"

        page_label = Label(
            navigation_frame,
            font=("Arial", 12, "bold"),
        )
        page_label.pack(
            side=LEFT,
            expand=True,
        )

        def go_previous():
            nonlocal current_page

            if current_page > 0:
                current_page -= 1
                render_page()

        def go_next():
            nonlocal current_page

            if current_page < len(pages) - 1:
                current_page += 1
                render_page()

        def refresh_navigation():
            previous_button.config(
                state=(
                    NORMAL
                    if current_page > 0
                    else DISABLED
                )
            )
            next_button.config(
                state=(
                    NORMAL
                    if current_page < len(pages) - 1
                    else DISABLED
                )
            )
            page_label.config(
                text=(
                    f"{title}    "
                    f"Page {current_page + 1} "
                    f"of {len(pages)}"
                )
            )

        previous_button = Button(
            navigation_frame,
            text="Previous",
            command=go_previous,
            height=2,
            width=12,
        )
        previous_button.pack(
            side=LEFT,
            padx=15,
            pady=10,
        )

        Button(
            navigation_frame,
            text="Close",
            command=book_window.destroy,
            height=2,
            width=12,
        ).pack(
            side=LEFT,
            padx=15,
            pady=10,
        )

        Button(
            navigation_frame,
            text="Top",
            command=lambda: text.see("1.0"),
            height=2,
            width=12,
        ).pack(
            side=RIGHT,
            padx=15,
            pady=10,
        )

        next_button = Button(
            navigation_frame,
            text="Next",
            command=go_next,
            height=2,
            width=12,
        )
        next_button.pack(
            side=RIGHT,
            padx=15,
            pady=10,
        )

        def render_page():
            text.config(state=NORMAL)
            text.delete("1.0", END)
            palette = {"Light": ("#ffffff", "#202124"), "Dark": ("#202124", "#e8eaed"), "Sepia": ("#f4ecd8", "#433522")}
            bg, fg = palette.get(reader_theme, palette["Light"])
            text.configure(background=bg, foreground=fg, insertbackground=fg)
            fit_horizontal_margins(text)

            try:
                page_blocks = pages[current_page]

                if not page_blocks:
                    text.insert(
                        END,
                        "This book contains no readable text.",
                    )
                else:
                    for block in page_blocks:
                        insert_block(text, block)

            except Exception as error:
                text.insert(
                    END,
                    "Could not display this book.\n\n"
                    f"{type(error).__name__}: {error}",
                )

            text.config(state=DISABLED)
            text.configure(font=("Arial", reader_font_size))
            text.see("1.0")
            save_progress(progress_key, page=current_page)
            refresh_navigation()

        def change_zoom(delta):
            nonlocal reader_font_size
            reader_font_size = max(8, min(36, reader_font_size + delta))
            render_page()

        def change_theme(value):
            nonlocal reader_theme
            reader_theme = value
            render_page()

        def find_text():
            from tkinter import simpledialog
            query = simpledialog.askstring("Find in book", "Search for:", parent=book_window)
            if not query:
                return
            text.tag_remove("kwiddle_search", "1.0", END)
            start = "1.0"
            while True:
                found = text.search(query, start, stopindex=END, nocase=True)
                if not found:
                    break
                end = f"{found}+{len(query)}c"
                text.tag_add("kwiddle_search", found, end)
                start = end
            text.tag_configure("kwiddle_search", background="#ffe66d", foreground="#202124")
            ranges = text.tag_ranges("kwiddle_search")
            if ranges:
                text.config(state=NORMAL)
                text.see(ranges[0])
                text.config(state=DISABLED)
            else:
                messagebox.showinfo("Find in book", "No matches on this page.", parent=book_window)

        def show_fonts():
            from .reader_features import font_inventory
            names = font_inventory(document)
            messagebox.showinfo("Document fonts", "Fonts used in this document:\n\n" + ("\n".join(names) if names else "No explicit font family was declared."), parent=book_window)

        def show_outline():
            headings = document_headings(document)
            if not headings:
                messagebox.showinfo("Contents", "This document has no heading outline.", parent=book_window)
                return
            outline = Toplevel(book_window)
            outline.title("Document contents")
            outline.geometry("360x420")
            for heading, level in headings:
                Label(outline, text=("    " * (level - 1)) + heading, anchor="w").pack(fill="x", padx=10, pady=3)

        Button(navigation_frame, text="−", command=lambda: change_zoom(-1), width=3).pack(side=LEFT, padx=2)
        Button(navigation_frame, text="+", command=lambda: change_zoom(1), width=3).pack(side=LEFT, padx=2)
        Button(navigation_frame, text="Find", command=find_text, width=7).pack(side=LEFT, padx=2)
        Button(navigation_frame, text="Contents", command=show_outline, width=9).pack(side=LEFT, padx=2)
        Button(navigation_frame, text="Fonts", command=show_fonts, width=7).pack(side=LEFT, padx=2)
        from tkinter import OptionMenu, StringVar
        theme_var = StringVar(value=reader_theme)
        OptionMenu(navigation_frame, theme_var, "Light", "Dark", "Sepia", command=change_theme).pack(side=LEFT, padx=2)

        book_window.bind("<Left>", lambda event: go_previous())
        book_window.bind("<Right>", lambda event: go_next())
        book_window.bind("<Control-f>", lambda event: find_text())
        book_window.bind("<Control-plus>", lambda event: change_zoom(1))
        book_window.bind("<Control-minus>", lambda event: change_zoom(-1))

        render_page()

    def build_library_ui():
        global window
        global library_signature
        global empty_library_label
        global library_count_label
        global book_buttons

        if window is not None:
            return

        window = Tk()
        window.title("Kwiddle")
        window.geometry("600x650")
        window.minsize(400, 450)

        header = Frame(window)
        header.pack(
            fill="x",
            padx=15,
            pady=(15, 5),
        )

        Label(
            header,
            text="Kwiddle Books",
            font=("Arial", 22, "bold"),
        ).pack(side=LEFT)

        library_count_label = Label(
            header,
            text="0 books",
            font=("Arial", 11),
        )
        library_count_label.pack(
            side=RIGHT,
            pady=8,
        )

        library_frame = Frame(window)
        library_frame.pack(
            fill=BOTH,
            expand=True,
            padx=15,
            pady=10,
        )

        canvas = Canvas(
            library_frame,
            highlightthickness=0,
        )

        scrollbar = Scrollbar(
            library_frame,
            orient=VERTICAL,
            command=canvas.yview,
        )

        scrollable_frame = Frame(canvas)

        canvas_window = canvas.create_window(
            (0, 0),
            window=scrollable_frame,
            anchor="nw",
        )

        canvas.configure(
            yscrollcommand=scrollbar.set,
        )

        canvas.pack(
            side=LEFT,
            fill=BOTH,
            expand=True,
        )
        scrollbar.pack(
            side=RIGHT,
            fill=Y,
        )

        def update_canvas(_event=None):
            canvas.configure(
                scrollregion=canvas.bbox("all"),
            )

            try:
                canvas.itemconfigure(
                    canvas_window,
                    width=canvas.winfo_width(),
                )
            except Exception:
                pass

        scrollable_frame.bind(
            "<Configure>",
            update_canvas,
        )
        canvas.bind(
            "<Configure>",
            update_canvas,
        )

        canvas.bind_all(
            "<Button-4>",
            lambda event: canvas.yview_scroll(-3, "units"),
        )
        canvas.bind_all(
            "<Button-5>",
            lambda event: canvas.yview_scroll(3, "units"),
        )

        def clear_library_widgets():
            global empty_library_label
            global book_buttons

            for button in list(book_buttons.values()):
                try:
                    button.destroy()
                except Exception:
                    pass

            book_buttons.clear()

            if empty_library_label is not None:
                try:
                    empty_library_label.destroy()
                except Exception:
                    pass

                empty_library_label = None

            for child in list(scrollable_frame.winfo_children()):
                try:
                    child.destroy()
                except Exception:
                    pass

        def rebuild_book_buttons():
            global empty_library_label
            global library_count_label

            clear_library_widgets()

            count = len(books)

            if count == 0:
                extensions = ", ".join(
                    extension.lstrip(".")
                    for extension in sorted(SUPPORTED_EXTENSIONS)
                )

                empty_library_label = Label(
                    scrollable_frame,
                    text=(
                        "No books found.\n\n"
                        f"Put {extensions} files in:\n"
                        f"{BOOKS_FOLDER}"
                    ),
                    font=("Arial", 12),
                    justify="center",
                )
                empty_library_label.pack(pady=40)

            else:
                for title in books:
                    button = Button(
                        scrollable_frame,
                        text=title,
                        command=lambda name=title: open_book(name),
                        height=3,
                        width=30,
                    )
                    button.pack(pady=5)
                    book_buttons[title] = button

            count_text = "1 book" if count == 1 else f"{count} books"

            library_count_label.config(
                text=count_text,
            )

            canvas.configure(
                scrollregion=canvas.bbox("all"),
            )

        BOOKS_FOLDER.mkdir(
            parents=True,
            exist_ok=True,
        )

        scan_books()

        library_signature = get_library_signature()
        rebuild_book_buttons()

        def auto_update():
            global library_signature

            try:
                current_signature = get_library_signature()

                if current_signature != library_signature:
                    print(
                        "[Kwiddle] Book library changed. Reloading..."
                    )

                    library_signature = current_signature
                    scan_books()
                    rebuild_book_buttons()

            except Exception as error:
                print(
                    "[Kwiddle] Automatic library update error: "
                    f"{type(error).__name__}: {error}"
                )

            try:
                if window.winfo_exists():
                    window.after(
                        AUTO_UPDATE_INTERVAL,
                        auto_update,
                    )
            except Exception:
                pass

        window.after(
            AUTO_UPDATE_INTERVAL,
            auto_update,
        )

    def main():
        build_library_ui()
        window.mainloop()

    main()


if __name__ == "__main__":
    run()