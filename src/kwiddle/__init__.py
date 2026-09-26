# src/kwiddle/__init__.py

from subprocess import call
from tkinter import *
from tkinter import messagebox
from pathlib import Path
import re
import threading
import time

from odf import teletype
from odf.opendocument import load
from odf.text import P, H, Span
from odf.style import Style
from odf.element import Element


# ============================================================
# Configuration
# ============================================================

window = Tk()
window.geometry("500x500")
window.title("Kwiddle")

REPO_URL = "https://github.com/cloudberrypitech/kwiddle"

# Folder containing .odt / .fodt books
BOOKS_FOLDER = Path(__file__).parent / "books"

# How often to check for new/changed books
AUTO_UPDATE_INTERVAL = 2000


# ============================================================
# Book storage
# ============================================================

books = {}
book_files = {}
book_buttons = {}

library_signature = None


# ============================================================
# Contribute
# ============================================================

def contribute_repo():
    answer = messagebox.askyesno(
        parent=window,
        title="Contribute",
        message="Do you want to star the Kwiddle repo on GitHub?"
    )

    if answer:
        call(
            f"open {REPO_URL}",
            shell=True
        )

        messagebox.showinfo(
            parent=window,
            title="Contribute",
            message="Thank you for contributing to Kwiddle."
        )


# ============================================================
# ODT helpers
# ============================================================

def get_element_text(element):
    """Get the text contained inside an ODT element."""

    try:
        return teletype.extractText(element)
    except Exception:
        return ""


def get_style_name(element):
    """Get the style name assigned to an ODT element."""

    try:
        return element.getAttribute("stylename") or ""
    except Exception:
        return ""


def get_style_properties(document, style_name):
    """
    Read basic formatting properties from an ODT style.
    """

    properties = {
        "bold": False,
        "italic": False,
        "underline": False,
        "size": None,
        "font": None,
        "align": None,
    }

    if not style_name:
        return properties

    try:
        styles = document.styles

        for style in styles.getElementsByType(Style):

            if style.getAttribute("name") != style_name:
                continue

            text_properties = None
            paragraph_properties = None

            for child in style.childNodes:

                if child.qname[1] == "text-properties":
                    text_properties = child

                elif child.qname[1] == "paragraph-properties":
                    paragraph_properties = child

            if text_properties is not None:

                font_weight = (
                    text_properties.getAttribute(
                        "fontweight"
                    )
                    or text_properties.getAttribute(
                        "font-weight"
                    )
                )

                font_style = (
                    text_properties.getAttribute(
                        "fontstyle"
                    )
                    or text_properties.getAttribute(
                        "font-style"
                    )
                )

                underline = (
                    text_properties.getAttribute(
                        "textunderlinestyle"
                    )
                    or text_properties.getAttribute(
                        "text-underline-style"
                    )
                )

                font_size = (
                    text_properties.getAttribute(
                        "fontsize"
                    )
                    or text_properties.getAttribute(
                        "font-size"
                    )
                )

                font_name = (
                    text_properties.getAttribute(
                        "fontfamily"
                    )
                    or text_properties.getAttribute(
                        "font-family"
                    )
                )

                if font_weight:
                    properties["bold"] = (
                        str(font_weight).lower()
                        in ("bold", "700", "800", "900")
                    )

                if font_style:
                    properties["italic"] = (
                        str(font_style).lower()
                        in ("italic", "oblique")
                    )

                if underline:
                    properties["underline"] = (
                        str(underline).lower()
                        not in ("none", "")
                    )

                if font_size:
                    properties["size"] = font_size

                if font_name:
                    properties["font"] = font_name

            if paragraph_properties is not None:

                align = (
                    paragraph_properties.getAttribute(
                        "textalign"
                    )
                    or paragraph_properties.getAttribute(
                        "text-align"
                    )
                )

                if align:
                    properties["align"] = str(align).lower()

            break

    except Exception:
        pass

    return properties


def size_to_tk(size):
    """Convert common ODT font sizes to Tkinter points."""

    if not size:
        return 14

    try:
        size = str(size).strip().lower()

        if size.endswith("pt"):
            return max(
                6,
                int(round(float(size[:-2])))
            )

        if size.endswith("px"):
            return max(
                6,
                int(round(float(size[:-2]) * 0.75))
            )

        if size.endswith("cm"):
            return max(
                6,
                int(round(float(size[:-2]) * 28.346))
            )

    except Exception:
        pass

    return 14


def make_font(properties):
    """Create a Tkinter font tuple from ODT properties."""

    font_name = properties.get("font") or "Arial"
    size = size_to_tk(properties.get("size"))

    if properties.get("bold") and properties.get("italic"):
        weight = "bold"
        slant = "italic"
    elif properties.get("bold"):
        weight = "bold"
        slant = "roman"
    elif properties.get("italic"):
        weight = "normal"
        slant = "italic"
    else:
        weight = "normal"
        slant = "roman"

    return (
        font_name,
        size,
        weight,
        slant
    )


# ============================================================
# Text formatting
# ============================================================

def configure_text_tag(text_widget, tag_name, properties):
    """Create/update a Tkinter Text formatting tag."""

    options = {
        "font": make_font(properties)
    }

    if properties.get("underline"):
        options["underline"] = True

    alignment = properties.get("align")

    if alignment == "center":
        options["justify"] = "center"

    elif alignment == "right":
        options["justify"] = "right"

    elif alignment == "left":
        options["justify"] = "left"

    text_widget.tag_configure(
        tag_name,
        **options
    )


def insert_odt_node(
    text_widget,
    document,
    node,
    inherited=None
):
    """
    Recursively insert an ODT element into the Tkinter Text widget.

    This preserves common Writer formatting such as:

    - bold
    - italic
    - underline
    - font size
    - font family
    - left/center/right alignment
    - headings
    - paragraphs
    """

    if inherited is None:
        inherited = {
            "bold": False,
            "italic": False,
            "underline": False,
            "size": None,
            "font": None,
            "align": None
        }

    properties = inherited.copy()

    style_name = get_style_name(node)

    if style_name:
        style_properties = get_style_properties(
            document,
            style_name
        )

        for key, value in style_properties.items():

            if value is not None:
                properties[key] = value

    # --------------------------------------------------------
    # Paragraph / heading
    # --------------------------------------------------------

    if isinstance(node, (P, H)):

        # Extract paragraph alignment
        alignment = properties.get("align")

        if alignment:
            properties["align"] = alignment

        tag_name = (
            f"style_{id(node)}"
        )

        configure_text_tag(
            text_widget,
            tag_name,
            properties
        )

        # Process children
        for child in node.childNodes:

            if isinstance(child, str):
                text_widget.insert(
                    END,
                    child,
                    tag_name
                )

            else:
                insert_odt_node(
                    text_widget,
                    document,
                    child,
                    properties
                )

        text_widget.insert(
            END,
            "\n\n",
            tag_name
        )

        return

    # --------------------------------------------------------
    # Span
    # --------------------------------------------------------

    if isinstance(node, Span):

        tag_name = (
            f"style_{id(node)}"
        )

        configure_text_tag(
            text_widget,
            tag_name,
            properties
        )

        for child in node.childNodes:

            if isinstance(child, str):

                text_widget.insert(
                    END,
                    child,
                    tag_name
                )

            else:

                insert_odt_node(
                    text_widget,
                    document,
                    child,
                    properties
                )

        return

    # --------------------------------------------------------
    # Generic element
    # --------------------------------------------------------

    for child in getattr(
        node,
        "childNodes",
        []
    ):

        if isinstance(child, str):

            tag_name = (
                f"style_{id(node)}"
            )

            configure_text_tag(
                text_widget,
                tag_name,
                properties
            )

            text_widget.insert(
                END,
                child,
                tag_name
            )

        else:

            insert_odt_node(
                text_widget,
                document,
                child,
                properties
            )


# ============================================================
# Load ODT book
# ============================================================

def load_odt_book(file_path):
    """
    Read an ODT/FODT file and return its document.
    """

    return load(
        str(file_path)
    )


def get_book_title(document, file_path):
    """
    Get the book title.

    Priority:
    1. First heading
    2. First paragraph
    3. Filename
    """

    try:

        headings = document.getElementsByType(H)

        if headings:

            title = get_element_text(
                headings[0]
            ).strip()

            if title:
                return title

    except Exception:
        pass

    try:

        paragraphs = document.getElementsByType(P)

        if paragraphs:

            title = get_element_text(
                paragraphs[0]
            ).strip()

            if title:
                return title

    except Exception:
        pass

    return file_path.stem.replace(
        "_",
        " "
    ).title()


# ============================================================
# Read book directory
# ============================================================

def scan_books():
    """
    Scan the books directory.

    Supported:
        .odt
        .fodt
        .odf
    """

    global books
    global book_files

    BOOKS_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    new_books = {}
    new_files = {}

    supported_extensions = {
        ".odt",
        ".fodt",
        ".odf"
    }

    for file_path in sorted(
        BOOKS_FOLDER.iterdir()
    ):

        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in supported_extensions:
            continue

        try:

            document = load_odt_book(
                file_path
            )

            title = get_book_title(
                document,
                file_path
            )

            # Make duplicate titles unique
            original_title = title
            counter = 2

            while title in new_books:

                title = (
                    f"{original_title} "
                    f"({counter})"
                )

                counter += 1

            new_books[title] = document
            new_files[title] = file_path

        except Exception as error:

            print(
                f"Could not load {file_path}: "
                f"{error}"
            )

    books = new_books
    book_files = new_files


# ============================================================
# Library signature
# ============================================================

def get_library_signature():
    """
    Generate a signature based on filenames and modification
    times.

    If anything changes, the library automatically refreshes.
    """

    BOOKS_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    files = []

    for file_path in BOOKS_FOLDER.iterdir():

        if (
            file_path.is_file()
            and file_path.suffix.lower()
            in {".odt", ".fodt", ".odf"}
        ):

            try:

                files.append(
                    (
                        file_path.name,
                        file_path.stat().st_mtime_ns,
                        file_path.stat().st_size
                    )
                )

            except OSError:
                pass

    return tuple(
        sorted(files)
    )


# ============================================================
# Open book
# ============================================================

def open_book(title):
    """Open a selected book."""

    document = books.get(title)

    if document is None:
        return

    file_path = book_files.get(
        title
    )

    if file_path is None:
        return

    book_window = Toplevel(
        window
    )

    book_window.title(
        f"Kwiddle - {title}"
    )

    book_window.geometry(
        "800x700"
    )

    book_window.minsize(
        450,
        400
    )

    # --------------------------------------------------------
    # Resizable vertical layout
    # --------------------------------------------------------

    reader_pane = PanedWindow(
        book_window,
        orient=VERTICAL,
        sashwidth=7,
        sashrelief=RAISED,
        showhandle=True
    )

    reader_pane.pack(
        fill=BOTH,
        expand=True
    )

    # --------------------------------------------------------
    # Text area
    # --------------------------------------------------------

    text_frame = Frame(
        reader_pane
    )

    # --------------------------------------------------------
    # Navigation
    # --------------------------------------------------------

    navigation_frame = Frame(
        book_window
    )

    reader_pane.add(
        text_frame,
        minsize=250,
        stretch="always"
    )

    reader_pane.add(
        navigation_frame,
        minsize=80,
        stretch="never"
    )

    # --------------------------------------------------------
    # Text widget
    # --------------------------------------------------------

    text = Text(
        text_frame,
        wrap="word",
        font=("Arial", 14),
        padx=20,
        pady=20
    )

    text.pack(
        side=LEFT,
        fill=BOTH,
        expand=True,
        padx=(10, 0),
        pady=10
    )

    scrollbar = Scrollbar(
        text_frame,
        orient=VERTICAL,
        command=text.yview
    )

    scrollbar.pack(
        side=RIGHT,
        fill=Y,
        padx=(0, 10),
        pady=10
    )

    text.configure(
        yscrollcommand=scrollbar.set
    )

    # --------------------------------------------------------
    # ODT content
    # --------------------------------------------------------

    text.config(
        state=NORMAL
    )

    text.delete(
        "1.0",
        END
    )

    try:

        body = document.text

        for child in body.childNodes:

            if isinstance(child, Element):

                insert_odt_node(
                    text,
                    document,
                    child
                )

    except Exception as error:

        text.insert(
            END,
            "Could not display this book.\n\n"
            f"{error}"
        )

    text.config(
        state=DISABLED
    )

    text.see(
        "1.0"
    )

    # --------------------------------------------------------
    # Navigation buttons
    # --------------------------------------------------------

    Button(
        navigation_frame,
        text="Close",
        command=book_window.destroy,
        height=2,
        width=12
    ).pack(
        side=LEFT,
        padx=15,
        pady=10
    )

    Label(
        navigation_frame,
        text=title,
        font=("Arial", 12, "bold")
    ).pack(
        side=LEFT,
        expand=True
    )

    Button(
        navigation_frame,
        text="Top",
        command=lambda: text.see("1.0"),
        height=2,
        width=12
    ).pack(
        side=RIGHT,
        padx=15,
        pady=10
    )


# ============================================================
# Main library UI
# ============================================================

title_label = Label(
    window,
    text="Kwiddle Books",
    font=("Arial", 22, "bold")
)

title_label.pack(
    pady=15
)


# ------------------------------------------------------------
# Library frame
# ------------------------------------------------------------

library_frame = Frame(
    window
)

library_frame.pack(
    fill=BOTH,
    expand=True,
    padx=15,
    pady=10
)

canvas = Canvas(
    library_frame
)

scrollbar = Scrollbar(
    library_frame,
    orient=VERTICAL,
    command=canvas.yview
)

scrollable_frame = Frame(
    canvas
)

canvas_window = canvas.create_window(
    (0, 0),
    window=scrollable_frame,
    anchor="nw"
)

canvas.configure(
    yscrollcommand=scrollbar.set
)

canvas.pack(
    side=LEFT,
    fill=BOTH,
    expand=True
)

scrollbar.pack(
    side=RIGHT,
    fill=Y
)


# ============================================================
# Canvas resizing
# ============================================================

def resize_scroll_region(event=None):

    canvas.configure(
        scrollregion=canvas.bbox(
            "all"
        )
    )

    canvas.itemconfigure(
        canvas_window,
        width=canvas.winfo_width()
    )


scrollable_frame.bind(
    "<Configure>",
    resize_scroll_region
)

canvas.bind(
    "<Configure>",
    resize_scroll_region
)


# ============================================================
# Create book buttons
# ============================================================

def rebuild_book_buttons():

    global book_buttons

    # Remove existing buttons
    for button in book_buttons.values():

        try:
            button.destroy()
        except Exception:
            pass

    book_buttons = {}

    # No books
    if not books:

        Label(
            scrollable_frame,
            text="No books found.\n\n"
                 "Put .odt, .fodt or .odf files in:\n"
                 f"{BOOKS_FOLDER}",
            font=("Arial", 12),
            justify="center"
        ).pack(
            pady=30
        )

        return

    # Create button for every book
    for title in books:

        button = Button(
            scrollable_frame,
            text=title,
            command=lambda name=title: open_book(name),
            height=3,
            width=30
        )

        button.pack(
            pady=5
        )

        book_buttons[title] = button


# ============================================================
# Automatic library update
# ============================================================

def auto_update():

    global library_signature

    try:

        current_signature = (
            get_library_signature()
        )

        if current_signature != library_signature:

            library_signature = (
                current_signature
            )

            scan_books()

            # Update Tkinter from the main thread
            window.after(
                0,
                rebuild_book_buttons
            )

    except Exception as error:

        print(
            f"Automatic library update error: {error}"
        )

    # Check again
    window.after(
        AUTO_UPDATE_INTERVAL,
        auto_update
    )


# ============================================================
# Mouse-wheel scrolling
# ============================================================

def mousewheel(event):

    canvas.yview_scroll(
        int(-1 * (event.delta / 120)),
        "units"
    )


canvas.bind_all(
    "<MouseWheel>",
    mousewheel
)


# ============================================================
# Start library
# ============================================================

BOOKS_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

scan_books()

library_signature = (
    get_library_signature()
)

rebuild_book_buttons()


# ============================================================
# Start automatic updates
# ============================================================

window.after(
    AUTO_UPDATE_INTERVAL,
    auto_update
)


# ============================================================
# Start application
# ============================================================

mainloop()