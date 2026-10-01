from subprocess import call
from pathlib import Path
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
from kwloader import (
    SUPPORTED_EXTENSIONS,
    BookDocument,
    TextBlock,
    TextStyle,
    load_book,
)

def run():
    window = None

    REPO_URL = "https://github.com/cloudberrypitech/kwiddle"
    BOOKS_FOLDER = Path(__file__).resolve().parent / "books"
    AUTO_UPDATE_INTERVAL = 2000

    books: dict[str, BookDocument] = {}
    book_files: dict[str, Path] = {}
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
            call(
                f'xdg-open "{REPO_URL}"',
                shell=True,
            )
        except Exception:
            try:
                call(
                    f'open "{REPO_URL}"',
                    shell=True,
                )
            except Exception:
                pass

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


    def configure_text_tag(text_widget, tag_name, style, align=None):
        options = {
            "font": make_font(style),
        }

        if style.underline:
            options["underline"] = True

        if align == "center":
            options["justify"] = "center"
        elif align == "right":
            options["justify"] = "right"
        elif align == "left":
            options["justify"] = "left"
        elif align == "justify":
            options["justify"] = "left"

        text_widget.tag_configure(tag_name, **options)


    def insert_block(text_widget, block: TextBlock):
        """
        Render one kwloader TextBlock into a Tkinter Text widget.

        All document-format-specific parsing has already happened in kwloader.
        """
        if block.kind == "heading":
            default_style = TextStyle(
                bold=True,
                size=18,
            )
        else:
            default_style = TextStyle(
                size=14,
            )

        block_style = TextStyle(
            bold=default_style.bold,
            italic=default_style.italic,
            underline=default_style.underline,
            size=default_style.size,
            font=default_style.font,
        )

        for index, run in enumerate(block.runs):
            style = run.style

            # A missing/zero value falls back to the block's readable default.
            effective = TextStyle(
                bold=style.bold or block_style.bold,
                italic=style.italic or block_style.italic,
                underline=style.underline or block_style.underline,
                size=style.size if style.size is not None else block_style.size,
                font=style.font or block_style.font,
            )

            tag_name = f"kwloader_{id(block)}_{index}"
            configure_text_tag(
                text_widget,
                tag_name,
                effective,
                block.align,
            )

            text_widget.insert(END, run.text, tag_name)

        # Keep paragraph separation similar to the previous ODT renderer.
        text_widget.insert(END, "\n\n")


    def build_document_pages(document: BookDocument):
        """
        Split a loaded document into readable pages.

        Pagination is deliberately kept in kwiddle because it is a UI concern,
        not a document-format concern.
        """
        if document is None:
            return [[]]

        blocks = [
            block
            for block in document.blocks
            if block.text.strip()
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
        current_page = 0

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
            text.see("1.0")
            refresh_navigation()

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


if __name__ == "__main__":
    main()
