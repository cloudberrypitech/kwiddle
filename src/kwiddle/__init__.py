# Imports
from subprocess import call
from tkinter import *
from tkinter import messagebox
import json
import re


# ============================================================
# Window
# ============================================================

window = Tk()
window.geometry("500x500")
window.title("Kwiddle")


# ============================================================
# Variables
# ============================================================

repo_path = "https://github.com/cloudberrypitech/kwiddle"
star_repo = None


# ============================================================
# Contribute
# ============================================================

def contribute_repo():
    global star_repo

    star_repo = messagebox.askyesno(
        parent=window,
        title="Contribute",
        message="Do you want to star the Kwiddle repo on GitHub?"
    )

    if star_repo:
        call(f"open {repo_path}", shell=True)

        messagebox.showinfo(
            parent=window,
            icon="info",
            title="Contribute",
            message="Thank you for contributing to Kwiddle."
        )


# ============================================================
# Load Books
# ============================================================

def load_books(file_path):
    """Load all books from books.json."""

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            messagebox.showerror(
                "Error",
                "books.json must contain a JSON object."
            )
            return {}

        return data

    except FileNotFoundError:
        messagebox.showerror(
            "Error",
            f"File not found: {file_path}"
        )
        return {}

    except json.JSONDecodeError as error:
        messagebox.showerror(
            "Error",
            f"Invalid JSON format in {file_path}:\n\n{error}"
        )
        return {}


# ============================================================
# Formatting
# ============================================================

def insert_formatted_text(text_widget, content):
    """
    Insert book content into a Text widget and interpret
    formatting tags such as:

        [title]
        [subtitle]
        [heading]
        [bold]
        [italic]
        [center]
        [right]
        [normal]

    Closing tags are also supported:

        [bold]text[/bold]
        [italic]text[/italic]
    """

    # Make sure everything is a string
    content = str(content)

    # --------------------------------------------------------
    # Text tags
    # --------------------------------------------------------

    text_widget.tag_configure(
        "title",
        font=("Arial", 24, "bold"),
        justify="center",
        spacing3=15
    )

    text_widget.tag_configure(
        "subtitle",
        font=("Arial", 15, "italic"),
        justify="center",
        spacing3=20
    )

    text_widget.tag_configure(
        "heading",
        font=("Arial", 19, "bold"),
        spacing1=10,
        spacing3=10
    )

    text_widget.tag_configure(
        "bold",
        font=("Arial", 14, "bold")
    )

    text_widget.tag_configure(
        "italic",
        font=("Arial", 14, "italic")
    )

    text_widget.tag_configure(
        "center",
        justify="center"
    )

    text_widget.tag_configure(
        "right",
        justify="right"
    )

    text_widget.tag_configure(
        "normal",
        font=("Arial", 14),
        justify="left"
    )

    # --------------------------------------------------------
    # Check for complete tagged blocks
    # --------------------------------------------------------

    block_pattern = re.compile(
        r"\[(title|subtitle|heading|bold|italic|center|right|normal)\]"
        r"(.*?)"
        r"\[/\1\]",
        re.DOTALL | re.IGNORECASE
    )

    position = 0

    for match in block_pattern.finditer(content):

        # Insert text before the formatted block
        before = content[position:match.start()]

        if before:
            text_widget.insert(
                END,
                before,
                "normal"
            )

        tag = match.group(1).lower()
        value = match.group(2)

        text_widget.insert(
            END,
            value,
            tag
        )

        position = match.end()

    # --------------------------------------------------------
    # Handle remaining text
    # --------------------------------------------------------

    remaining = content[position:]

    if remaining:
        # Handle single-line tags such as:
        #
        # [title]My Book
        #
        # without requiring [/title]

        lines = remaining.splitlines(keepends=True)

        for line in lines:

            stripped = line.strip()

            tag_match = re.match(
                r"^\[(title|subtitle|heading|bold|italic|center|right|normal)\](.*)$",
                stripped,
                re.IGNORECASE
            )

            if tag_match:

                tag = tag_match.group(1).lower()
                value = tag_match.group(2)

                # Preserve newline
                if line.endswith("\n"):
                    value += "\n"

                text_widget.insert(
                    END,
                    value,
                    tag
                )

            else:
                text_widget.insert(
                    END,
                    line,
                    "normal"
                )


# ============================================================
# Book Reader
# ============================================================

def book(bookname, content):
    """
    Open a book reader.

    The text area and navigation area are separated by a
    draggable PanedWindow sash.
    """

    # --------------------------------------------------------
    # Book window
    # --------------------------------------------------------

    book_window = Toplevel(window)

    book_window.title(
        f"Kwiddle - {bookname}"
    )

    book_window.geometry(
        "750x650"
    )

    book_window.minsize(
        400,
        350
    )

    # --------------------------------------------------------
    # Make sure content is a list
    # --------------------------------------------------------

    if not isinstance(content, list):
        content = [content]

    # Convert dictionary-style JSON entries to strings
    cleaned_content = []

    for item in content:

        if isinstance(item, dict):

            # Support objects such as:
            #
            # {"text": "Hello"}
            #
            # or the old malformed-style structure
            # if it contains a single value.

            if "text" in item:
                cleaned_content.append(
                    str(item["text"])
                )

            elif len(item) == 1:
                cleaned_content.append(
                    str(next(iter(item.values())))
                )

            else:
                cleaned_content.append(
                    " ".join(
                        str(value)
                        for value in item.values()
                    )
                )

        else:
            cleaned_content.append(
                str(item)
            )

    if not cleaned_content:
        cleaned_content = [
            "[title]Empty Book"
        ]

    # --------------------------------------------------------
    # Current page
    # --------------------------------------------------------

    current_page = [0]

    # --------------------------------------------------------
    # Resizable reader
    #
    # The sash between these two panes can be dragged.
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
    # Text pane
    # --------------------------------------------------------

    text_frame = Frame(
        reader_pane
    )

    # --------------------------------------------------------
    # Navigation pane
    # --------------------------------------------------------

    navigation_frame = Frame(
        reader_pane,
        height=70
    )

    reader_pane.add(
        text_frame,
        minsize=200,
        stretch="always"
    )

    reader_pane.add(
        navigation_frame,
        minsize=60,
        stretch="never"
    )

    # --------------------------------------------------------
    # Text widget
    # --------------------------------------------------------

    text = Text(
        text_frame,
        wrap="word",
        font=("Arial", 14),
        undo=False
    )

    text.pack(
        side=LEFT,
        fill=BOTH,
        expand=True,
        padx=(10, 0),
        pady=10
    )

    # --------------------------------------------------------
    # Scrollbar
    # --------------------------------------------------------

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
    # Page label
    # --------------------------------------------------------

    page_label = Label(
        navigation_frame,
        text="",
        font=("Arial", 11)
    )

    page_label.pack(
        side=TOP,
        pady=(5, 2)
    )

    # --------------------------------------------------------
    # Navigation buttons
    # --------------------------------------------------------

    button_frame = Frame(
        navigation_frame
    )

    button_frame.pack(
        fill=X,
        expand=True
    )

    # --------------------------------------------------------
    # Update page
    # --------------------------------------------------------

    def display_page():

        text.config(
            state=NORMAL
        )

        text.delete(
            "1.0",
            END
        )

        insert_formatted_text(
            text,
            cleaned_content[current_page[0]]
        )

        text.config(
            state=DISABLED
        )

        text.see(
            "1.0"
        )

        page_label.config(
            text=f"Page {current_page[0] + 1} / {len(cleaned_content)}"
        )

        # Disable Previous on first page
        if current_page[0] == 0:
            previous_button.config(
                state=DISABLED
            )
        else:
            previous_button.config(
                state=NORMAL
            )

        # Disable Next on last page
        if current_page[0] >= len(cleaned_content) - 1:
            next_button.config(
                state=DISABLED
            )
        else:
            next_button.config(
                state=NORMAL
            )

    # --------------------------------------------------------
    # Previous page
    # --------------------------------------------------------

    def previous_page():

        if current_page[0] > 0:
            current_page[0] -= 1
            display_page()

    # --------------------------------------------------------
    # Next page
    # --------------------------------------------------------

    def next_page():

        if current_page[0] < len(cleaned_content) - 1:
            current_page[0] += 1
            display_page()

        else:
            messagebox.showinfo(
                parent=book_window,
                title="Bookreader",
                message="Book Completed"
            )

    # --------------------------------------------------------
    # Previous button
    # --------------------------------------------------------

    previous_button = Button(
        button_frame,
        text="Previous",
        command=previous_page,
        height=2,
        width=12
    )

    previous_button.pack(
        side=LEFT,
        padx=10,
        pady=5
    )

    # --------------------------------------------------------
    # Next button
    # --------------------------------------------------------

    next_button = Button(
        button_frame,
        text="Next",
        command=next_page,
        height=2,
        width=12
    )

    next_button.pack(
        side=RIGHT,
        padx=10,
        pady=5
    )

    # --------------------------------------------------------
    # Initial page
    # --------------------------------------------------------

    display_page()

    # --------------------------------------------------------
    # Close book
    # --------------------------------------------------------

    def close_book():
        book_window.destroy()

    book_window.protocol(
        "WM_DELETE_WINDOW",
        close_book
    )


# ============================================================
# Load books.json
# ============================================================

books_file = "./src/kwiddle/books.json"

books = load_books(
    books_file
)


# ============================================================
# Main Window UI
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
# Scrollable book list
# ------------------------------------------------------------

book_list_frame = Frame(
    window
)

book_list_frame.pack(
    fill=BOTH,
    expand=True,
    padx=15,
    pady=10
)

canvas = Canvas(
    book_list_frame
)

scrollbar = Scrollbar(
    book_list_frame,
    orient=VERTICAL,
    command=canvas.yview
)

scrollable_frame = Frame(
    canvas
)

scrollable_frame.bind(
    "<Configure>",
    lambda event: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
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
# Automatically create a button for every book
# ============================================================

for book_id, book_content in books.items():

    # Get a readable name from the ID
    display_name = book_id.replace(
        "_",
        " "
    ).title()

    # Try to get the actual title from [title]
    if isinstance(book_content, list):

        for item in book_content:

            if isinstance(item, str):

                match = re.match(
                    r"^\[title\](.*)$",
                    item,
                    re.IGNORECASE
                )

                if match:
                    display_name = match.group(1).strip()
                    break

                # Also support [title]Title[/title]
                match = re.match(
                    r"^\[title\](.*?)\[/title\]$",
                    item,
                    re.IGNORECASE | re.DOTALL
                )

                if match:
                    display_name = match.group(1).strip()
                    break

    # --------------------------------------------------------
    # Create button
    # --------------------------------------------------------

    def open_book(
        book_name=display_name,
        book_data=book_content
    ):
        book(
            book_name,
            book_data
        )

    Button(
        scrollable_frame,
        text=display_name,
        command=open_book,
        height=3,
        width=25
    ).pack(
        pady=5
    )


# ============================================================
# No books message
# ============================================================

if not books:

    Label(
        scrollable_frame,
        text="No books found.",
        font=("Arial", 14)
    ).pack(
        pady=20
    )


# ============================================================
# Start Application
# ============================================================

mainloop()