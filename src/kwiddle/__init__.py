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

from odf import teletype
from odf.opendocument import load
from odf.text import P, H, Span, S, Tab, LineBreak
from odf.style import Style
from odf.element import Element


# ============================================================
# GLOBAL SETTINGS
# ============================================================

window = None

REPO_URL = "https://github.com/cloudberrypitech/kwiddle"

# This file is:
#
# src/
#   kwiddle/
#       __init__.py
#       books/
#
# Therefore this resolves to:
#
# src/kwiddle/books/
BOOKS_FOLDER = (
    Path(__file__).resolve().parent / "books"
)

AUTO_UPDATE_INTERVAL = 2000

SUPPORTED_EXTENSIONS = {
    ".odt",
    ".fodt",
    ".odf",
}

books = {}
book_files = {}
book_buttons = {}

empty_library_label = None
library_count_label = None

library_signature = None


# ============================================================
# CONTRIBUTION
# ============================================================

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


# ============================================================
# ODT TEXT
# ============================================================

def get_element_text(element):
    """Safely extract text from an ODT element."""

    try:
        return teletype.extractText(element)
    except Exception:
        return ""


def get_style_name(element):
    """Return the ODT style name attached to an element."""

    try:
        return (
            element.getAttribute("stylename")
            or element.getAttribute("style-name")
            or ""
        )
    except Exception:
        return ""


# ============================================================
# ODT STYLE READING
# ============================================================

def get_style_properties(document, style_name):
    """
    Read common formatting information from ODT styles.
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

    style_collections = []

    for attribute_name in (
        "styles",
        "automaticstyles",
    ):
        collection = getattr(
            document,
            attribute_name,
            None,
        )

        if collection is not None:
            style_collections.append(collection)

    try:
        for collection in style_collections:

            for style in collection.getElementsByType(
                Style
            ):

                style_name_value = (
                    style.getAttribute("name")
                    or style.getAttribute("stylename")
                )

                if style_name_value != style_name:
                    continue

                text_properties = None
                paragraph_properties = None

                for child in getattr(
                    style,
                    "childNodes",
                    [],
                ):

                    qname = getattr(
                        child,
                        "qname",
                        None,
                    )

                    if not qname or len(qname) < 2:
                        continue

                    child_name = qname[1]

                    if child_name == "text-properties":
                        text_properties = child

                    elif child_name == "paragraph-properties":
                        paragraph_properties = child

                # ------------------------------------------------
                # TEXT PROPERTIES
                # ------------------------------------------------

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
                            in {
                                "bold",
                                "700",
                                "800",
                                "900",
                            }
                        )

                    if font_style:
                        properties["italic"] = (
                            str(font_style).lower()
                            in {
                                "italic",
                                "oblique",
                            }
                        )

                    if underline:
                        properties["underline"] = (
                            str(underline).lower()
                            not in {
                                "",
                                "none",
                            }
                        )

                    if font_size:
                        properties["size"] = font_size

                    if font_name:
                        properties["font"] = font_name

                # ------------------------------------------------
                # PARAGRAPH PROPERTIES
                # ------------------------------------------------

                if paragraph_properties is not None:

                    alignment = (
                        paragraph_properties.getAttribute(
                            "textalign"
                        )
                        or paragraph_properties.getAttribute(
                            "text-align"
                        )
                    )

                    if alignment:
                        properties["align"] = (
                            str(alignment).lower()
                        )

                return properties

    except Exception:
        pass

    return properties


# ============================================================
# FONT CONVERSION
# ============================================================

def size_to_tk(size):
    """Convert ODT size units into Tkinter font points."""

    if not size:
        return 14

    try:
        value = str(size).strip().lower()

        if value.endswith("pt"):
            return max(
                6,
                int(
                    round(
                        float(value[:-2])
                    )
                ),
            )

        if value.endswith("px"):
            return max(
                6,
                int(
                    round(
                        float(value[:-2])
                        * 0.75
                    )
                ),
            )

        if value.endswith("cm"):
            return max(
                6,
                int(
                    round(
                        float(value[:-2])
                        * 28.346
                    )
                ),
            )

        if value.endswith("mm"):
            return max(
                6,
                int(
                    round(
                        float(value[:-2])
                        * 2.8346
                    )
                ),
            )

    except Exception:
        pass

    return 14


def make_font(properties):
    """Create a Tkinter font tuple."""

    font_name = properties.get(
        "font"
    ) or "Arial"

    size = size_to_tk(
        properties.get("size")
    )

    bold = properties.get(
        "bold",
        False,
    )

    italic = properties.get(
        "italic",
        False,
    )

    if bold and italic:
        weight = "bold"
        slant = "italic"

    elif bold:
        weight = "bold"
        slant = "roman"

    elif italic:
        weight = "normal"
        slant = "italic"

    else:
        weight = "normal"
        slant = "roman"

    return (
        font_name,
        size,
        weight,
        slant,
    )


def configure_text_tag(
    text_widget,
    tag_name,
    properties,
):
    """Configure a Tkinter Text formatting tag."""

    options = {
        "font": make_font(
            properties
        ),
    }

    if properties.get(
        "underline",
        False,
    ):
        options["underline"] = True

    alignment = properties.get(
        "align"
    )

    if alignment == "center":
        options["justify"] = "center"

    elif alignment == "right":
        options["justify"] = "right"

    elif alignment == "left":
        options["justify"] = "left"

    text_widget.tag_configure(
        tag_name,
        **options,
    )


# ============================================================
# ODF ELEMENT CHECKING
# ============================================================

def is_odf_element(node, *factories):
    """Check whether an ODT node matches a given ODF type."""

    if node is None:
        return False

    node_qname = getattr(
        node,
        "qname",
        None,
    )

    if node_qname is None:
        return False

    for factory in factories:

        try:
            candidate = factory(
                check_grammar=False
            )

            if getattr(
                candidate,
                "qname",
                None,
            ) == node_qname:
                return True

        except Exception:
            continue

    return False


# ============================================================
# ODT RENDERING
# ============================================================

def insert_odt_node(
    text_widget,
    document,
    node,
    inherited=None,
):
    """
    Render an ODT node into a Tkinter Text widget.

    Supports:
    - headings
    - paragraphs
    - spans
    - bold
    - italic
    - underline
    - font family
    - font size
    - alignment
    - tabs
    - line breaks
    - spaces
    """

    if inherited is None:
        inherited = {
            "bold": False,
            "italic": False,
            "underline": False,
            "size": None,
            "font": None,
            "align": None,
        }

    properties = inherited.copy()

    style_name = get_style_name(
        node
    )

    if style_name:

        style_properties = (
            get_style_properties(
                document,
                style_name,
            )
        )

        for key, value in (
            style_properties.items()
        ):
            if value is not None:
                properties[key] = value

    # --------------------------------------------------------
    # PARAGRAPH / HEADING
    # --------------------------------------------------------

    if is_odf_element(
        node,
        P,
        H,
    ):

        tag_name = (
            f"odt_style_{id(node)}"
        )

        configure_text_tag(
            text_widget,
            tag_name,
            properties,
        )

        for child in getattr(
            node,
            "childNodes",
            [],
        ):

            # ODF text nodes are not always plain strings.
            if isinstance(
                child,
                Element,
            ):
                insert_odt_node(
                    text_widget,
                    document,
                    child,
                    properties,
                )

            else:
                text_value = str(
                    child
                )

                if text_value:
                    text_widget.insert(
                        END,
                        text_value,
                        tag_name,
                    )

        text_widget.insert(
            END,
            "\n\n",
            tag_name,
        )

        return

    # --------------------------------------------------------
    # SPAN
    # --------------------------------------------------------

    if is_odf_element(
        node,
        Span,
    ):

        tag_name = (
            f"odt_style_{id(node)}"
        )

        configure_text_tag(
            text_widget,
            tag_name,
            properties,
        )

        for child in getattr(
            node,
            "childNodes",
            [],
        ):

            if isinstance(
                child,
                Element,
            ):

                insert_odt_node(
                    text_widget,
                    document,
                    child,
                    properties,
                )

            else:

                text_value = str(
                    child
                )

                if text_value:
                    text_widget.insert(
                        END,
                        text_value,
                        tag_name,
                    )

        return

    # --------------------------------------------------------
    # SPACE
    # --------------------------------------------------------

    if is_odf_element(
        node,
        S,
    ):

        tag_name = (
            f"odt_style_{id(node)}"
        )

        configure_text_tag(
            text_widget,
            tag_name,
            properties,
        )

        count = 1

        try:
            count = int(
                node.getAttribute(
                    "c"
                ) or 1
            )
        except Exception:
            count = 1

        text_widget.insert(
            END,
            " " * max(
                1,
                count,
            ),
            tag_name,
        )

        return

    # --------------------------------------------------------
    # TAB
    # --------------------------------------------------------

    if is_odf_element(
        node,
        Tab,
    ):

        tag_name = (
            f"odt_style_{id(node)}"
        )

        configure_text_tag(
            text_widget,
            tag_name,
            properties,
        )

        text_widget.insert(
            END,
            "\t",
            tag_name,
        )

        return

    # --------------------------------------------------------
    # LINE BREAK
    # --------------------------------------------------------

    if is_odf_element(
        node,
        LineBreak,
    ):

        tag_name = (
            f"odt_style_{id(node)}"
        )

        configure_text_tag(
            text_widget,
            tag_name,
            properties,
        )

        text_widget.insert(
            END,
            "\n",
            tag_name,
        )

        return

    # --------------------------------------------------------
    # OTHER ELEMENTS
    # --------------------------------------------------------

    for child in getattr(
        node,
        "childNodes",
        [],
    ):

        if isinstance(
            child,
            Element,
        ):

            insert_odt_node(
                text_widget,
                document,
                child,
                properties,
            )

        else:

            tag_name = (
                f"odt_style_{id(node)}"
            )

            configure_text_tag(
                text_widget,
                tag_name,
                properties,
            )

            text_value = str(
                child
            )

            if text_value:
                text_widget.insert(
                    END,
                    text_value,
                    tag_name,
                )


# ============================================================
# LOAD ODT
# ============================================================

def load_odt_book(file_path):
    """Load one ODT/FODT/ODF file."""

    file_path = Path(
        file_path
    ).resolve()

    if not file_path.exists():
        raise FileNotFoundError(
            f"File does not exist: {file_path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Path is not a file: {file_path}"
        )

    print(
        f"[Kwiddle] Loading book: "
        f"{file_path}"
    )

    try:

        document = load(
            str(file_path)
        )

    except Exception as error:

        raise RuntimeError(
            f"Could not parse "
            f"{file_path.name}: "
            f"{type(error).__name__}: "
            f"{error}"
        ) from error

    if document is None:
        raise RuntimeError(
            f"ODT loader returned no "
            f"document for {file_path.name}"
        )

    print(
        f"[Kwiddle] Loaded successfully: "
        f"{file_path.name}"
    )

    return document


# ============================================================
# BOOK TITLE
# ============================================================

def get_book_title(
    document,
    file_path,
):
    """
    Determine the button title.

    Priority:
    1. First heading
    2. First paragraph
    3. Filename
    """

    try:

        headings = document.getElementsByType(
            H
        )

        for heading in headings:

            title = get_element_text(
                heading
            ).strip()

            if title:
                return title

    except Exception:
        pass

    try:

        paragraphs = document.getElementsByType(
            P
        )

        for paragraph in paragraphs:

            title = get_element_text(
                paragraph
            ).strip()

            if title:
                return title

    except Exception:
        pass

    return (
        Path(file_path)
        .stem
        .replace("_", " ")
        .replace("-", " ")
        .title()
    )


# ============================================================
# SCAN ALL BOOKS
# ============================================================

def scan_books():
    """
    Find every supported book in the books directory.

    Example:

    books/
        book1.odt
        book2.odt
        book3.fodt
        folder/
            book4.odt

    All four become separate books/buttons.
    """

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
    print(
        f"[Kwiddle] Books folder: "
        f"{BOOKS_FOLDER}"
    )
    print(
        f"[Kwiddle] Folder exists: "
        f"{BOOKS_FOLDER.exists()}"
    )
    print("=" * 60)

    # rglob means:
    # - files directly in books/
    # - files inside books/subfolder/
    # - files inside books/subfolder/subfolder/
    #
    # Everything supported is detected.

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
            or file_path.name.startswith(
                ".~lock."
            )
        ):
            continue

        if (
            file_path.suffix.lower()
            not in SUPPORTED_EXTENSIONS
        ):
            continue

        found_count += 1

        print(
            f"[Kwiddle] Found book: "
            f"{file_path}"
        )

        try:

            document = load_odt_book(
                file_path
            )

            title = get_book_title(
                document,
                file_path,
            )

            if not title:
                title = file_path.stem

            original_title = title
            number = 2

            # Every file must get a unique title.
            # Duplicate document titles therefore become:
            #
            # My Book
            # My Book (2)
            # My Book (3)

            while title in new_books:

                title = (
                    f"{original_title} "
                    f"({number})"
                )

                number += 1

            new_books[title] = document
            new_files[title] = file_path

            print(
                f"[Kwiddle] Book ready: "
                f"{title}"
            )

        except Exception as error:

            print(
                f"[Kwiddle] ERROR loading "
                f"{file_path}:"
            )

            print(
                f"    {type(error).__name__}: "
                f"{error}"
            )

    books = new_books
    book_files = new_files

    print(
        f"[Kwiddle] Files found: "
        f"{found_count}"
    )

    print(
        f"[Kwiddle] Books loaded: "
        f"{len(books)}"
    )

    print("=" * 60)
    print()

    return books


# ============================================================
# LIBRARY SIGNATURE
# ============================================================

def get_library_signature():
    """
    Detect changes in the books directory.
    """

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
            or file_path.name.startswith(
                ".~lock."
            )
        ):
            continue

        if (
            file_path.suffix.lower()
            not in SUPPORTED_EXTENSIONS
        ):
            continue

        try:

            stat = file_path.stat()

            relative_path = (
                file_path.relative_to(
                    BOOKS_FOLDER
                )
            )

            signature.append(
                (
                    str(relative_path),
                    stat.st_mtime_ns,
                    stat.st_size,
                )
            )

        except OSError:
            continue

    return tuple(
        sorted(signature)
    )


# ============================================================
# BUILD DOCUMENT PAGES
# ============================================================

def build_document_pages(document):
    """
    Split an ODT into readable pages.

    This does not modify the document.
    """

    if document is None:
        return [[]]

    blocks = []

    stack = [
        document.text
    ]

    while stack:

        node = stack.pop()

        if node is None:
            continue

        if not isinstance(
            node,
            Element,
        ):
            continue

        qname = getattr(
            node,
            "qname",
            None,
        )

        element_name = (
            qname[1]
            if qname
            else None
        )

        if element_name in {
            "p",
            "h",
        }:

            text_value = get_element_text(
                node
            ).strip()

            if text_value:
                blocks.append(
                    node
                )

            continue

        children = getattr(
            node,
            "childNodes",
            [],
        )

        for child in reversed(
            children
        ):

            if isinstance(
                child,
                Element,
            ):
                stack.append(
                    child
                )

    if not blocks:
        return [[]]

    pages = []

    current_page = []
    current_chars = 0

    # These are deliberately approximate because
    # Tkinter text layout depends on window size.

    max_blocks = 8
    max_characters = 1800

    for block in blocks:

        block_text = get_element_text(
            block
        ).strip()

        if not block_text:
            continue

        would_overflow = (
            current_page
            and (
                len(current_page)
                >= max_blocks
                or
                current_chars
                + len(block_text)
                > max_characters
            )
        )

        if would_overflow:

            pages.append(
                current_page
            )

            current_page = []
            current_chars = 0

        current_page.append(
            block
        )

        current_chars += len(
            block_text
        )

    if current_page:
        pages.append(
            current_page
        )

    return pages or [[]]


# ============================================================
# OPEN BOOK
# ============================================================

def open_book(title):
    """Open one selected book."""

    document = books.get(
        title
    )

    if document is None:
        messagebox.showerror(
            parent=window,
            title="Kwiddle",
            message=(
                f"Could not find the loaded "
                f"document for:\n\n{title}"
            ),
        )
        return

    file_path = book_files.get(
        title
    )

    if file_path is None:
        messagebox.showerror(
            parent=window,
            title="Kwiddle",
            message=(
                f"Could not find the file "
                f"for:\n\n{title}"
            ),
        )
        return

    print(
        f"[Kwiddle] Opening: "
        f"{file_path}"
    )

    book_window = Toplevel(
        window
    )

    book_window.title(
        f"Kwiddle - {title}"
    )

    book_window.geometry(
        "900x700"
    )

    book_window.minsize(
        500,
        400,
    )

    # ========================================================
    # PANED WINDOW
    #
    # IMPORTANT:
    # Frames are created WITH reader_pane as their parent.
    # This makes the sash/resizer work correctly.
    # ========================================================

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

    text_frame = Frame(
        reader_pane
    )

    navigation_frame = Frame(
        reader_pane
    )

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

    # ========================================================
    # TEXT AREA
    # ========================================================

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
        yscrollcommand=scrollbar.set
    )

    # ========================================================
    # PAGES
    # ========================================================

    pages = build_document_pages(
        document
    )

    current_page = 0

    # ========================================================
    # PAGE LABEL
    # ========================================================

    page_label = Label(
        navigation_frame,
        font=("Arial", 12, "bold"),
    )

    # ========================================================
    # RENDER CURRENT PAGE
    # ========================================================

    def render_page():

        text.config(
            state=NORMAL
        )

        text.delete(
            "1.0",
            END,
        )

        try:

            page_blocks = pages[
                current_page
            ]

            if not page_blocks:

                text.insert(
                    END,
                    "This book contains "
                    "no readable text.",
                )

            else:

                for block in page_blocks:

                    insert_odt_node(
                        text,
                        document,
                        block,
                    )

        except Exception as error:

            text.insert(
                END,
                "Could not display this book.\n\n"
                f"{type(error).__name__}: "
                f"{error}",
            )

        text.config(
            state=DISABLED
        )

        text.see(
            "1.0"
        )

        page_label.config(
            text=(
                f"{title}    "
                f"Page {current_page + 1} "
                f"of {len(pages)}"
            )
        )

        refresh_navigation()

    # ========================================================
    # NAVIGATION
    # ========================================================

    def go_previous():

        nonlocal current_page

        if current_page > 0:

            current_page -= 1

            render_page()

    def go_next():

        nonlocal current_page

        if current_page < (
            len(pages) - 1
        ):

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
                if current_page
                < len(pages) - 1
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

    # ========================================================
    # PREVIOUS
    # ========================================================

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

    # ========================================================
    # CLOSE
    # ========================================================

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

    # ========================================================
    # PAGE LABEL
    # ========================================================

    page_label.pack(
        side=LEFT,
        expand=True,
    )

    # ========================================================
    # TOP
    # ========================================================

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

    # ========================================================
    # NEXT
    # ========================================================

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

    render_page()


# ============================================================
# LIBRARY UI
# ============================================================

def build_library_ui():
    global window
    global library_signature
    global empty_library_label
    global library_count_label

    if window is not None:
        return

    # ========================================================
    # MAIN WINDOW
    # ========================================================

    window = Tk()

    window.title(
        "Kwiddle"
    )

    window.geometry(
        "600x650"
    )

    window.minsize(
        400,
        450,
    )

    # ========================================================
    # HEADER
    # ========================================================

    header = Frame(
        window
    )

    header.pack(
        fill="x",
        padx=15,
        pady=(15, 5),
    )

    Label(
        header,
        text="Kwiddle Books",
        font=(
            "Arial",
            22,
            "bold",
        ),
    ).pack(
        side=LEFT
    )

    library_count_label = Label(
        header,
        text="0 books",
        font=(
            "Arial",
            11,
        ),
    )

    library_count_label.pack(
        side=RIGHT,
        pady=8,
    )

    # ========================================================
    # LIBRARY FRAME
    # ========================================================

    library_frame = Frame(
        window
    )

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

    scrollable_frame = Frame(
        canvas
    )

    canvas_window = canvas.create_window(
        (0, 0),
        window=scrollable_frame,
        anchor="nw",
    )

    canvas.configure(
        yscrollcommand=scrollbar.set
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

    # ========================================================
    # CANVAS RESIZING
    # ========================================================

    def update_canvas(event=None):

        canvas.configure(
            scrollregion=canvas.bbox(
                "all"
            )
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

    # ========================================================
    # CLEAR LIBRARY UI
    # ========================================================

    def clear_library_widgets():

        global empty_library_label

        for button in list(
            book_buttons.values()
        ):

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

        # Remove any leftover children created
        # by an earlier empty state.

        for child in list(
            scrollable_frame.winfo_children()
        ):

            try:
                child.destroy()
            except Exception:
                pass

    # ========================================================
    # BUILD ONE BUTTON PER BOOK
    # ========================================================

    def rebuild_book_buttons():

        global empty_library_label
        global library_count_label

        clear_library_widgets()

        count = len(
            books
        )

        if count == 1:
            count_text = "1 book"
        else:
            count_text = f"{count} books"

        library_count_label.config(
            text=count_text
        )

        # ----------------------------------------------------
        # EMPTY
        # ----------------------------------------------------

        if count == 0:

            empty_library_label = Label(
                scrollable_frame,
                text=(
                    "No books found.\n\n"
                    "Put .odt, .fodt or .odf "
                    "files in:\n\n"
                    f"{BOOKS_FOLDER}"
                ),
                font=(
                    "Arial",
                    12,
                ),
                justify="center",
            )

            empty_library_label.pack(
                pady=40
            )

            update_canvas()

            return

        # ----------------------------------------------------
        # ONE BUTTON FOR EVERY LOADED BOOK
        # ----------------------------------------------------

        for title in sorted(
            books.keys(),
            key=str.lower,
        ):

            button = Button(
                scrollable_frame,
                text=title,
                command=lambda name=title: (
                    open_book(name)
                ),
                height=3,
                width=40,
                font=(
                    "Arial",
                    12,
                ),
            )

            button.pack(
                fill="x",
                padx=10,
                pady=5,
            )

            book_buttons[
                title
            ] = button

        update_canvas()

    # ========================================================
    # MOUSE WHEEL - LINUX / WINDOWS
    # ========================================================

    def mousewheel(event):

        try:

            if hasattr(
                event,
                "delta",
            ) and event.delta:

                canvas.yview_scroll(
                    int(
                        -1
                        * (
                            event.delta
                            / 120
                        )
                    ),
                    "units",
                )

        except Exception:
            pass

    canvas.bind_all(
        "<MouseWheel>",
        mousewheel,
    )

    # Linux Raspberry Pi / X11 scrolling
    canvas.bind_all(
        "<Button-4>",
        lambda event: canvas.yview_scroll(
            -3,
            "units",
        ),
    )

    canvas.bind_all(
        "<Button-5>",
        lambda event: canvas.yview_scroll(
            3,
            "units",
        ),
    )

    # ========================================================
    # INITIAL BOOK LOAD
    # ========================================================

    BOOKS_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    scan_books()

    library_signature = (
        get_library_signature()
    )

    rebuild_book_buttons()

    # ========================================================
    # AUTO UPDATE
    # ========================================================

    def auto_update():

        global library_signature

        try:

            current_signature = (
                get_library_signature()
            )

            if (
                current_signature
                != library_signature
            ):

                print(
                    "[Kwiddle] Book library "
                    "changed. Reloading..."
                )

                library_signature = (
                    current_signature
                )

                scan_books()

                rebuild_book_buttons()

        except Exception as error:

            print(
                "[Kwiddle] Automatic "
                "library update error: "
                f"{type(error).__name__}: "
                f"{error}"
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


# ============================================================
# MAIN
# ============================================================

def main():

    build_library_ui()

    window.mainloop()


if __name__ == "__main__":
    main()