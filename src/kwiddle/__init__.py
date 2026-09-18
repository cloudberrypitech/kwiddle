# Imports
from tkinter import *
from tkinter import messagebox
from subprocess import call

# Window Attributes
window = Tk()
window.geometry("500x500")
window.title("Kwiddle")
window.iconphoto(True, PhotoImage("winlogo.png"))

# Variables
page = 0
star_repo = None
repo_path:str = "https://github.com/cloudberrypitech/kwiddle"

# Default Startup Functions
def contribute_repo():
    global star_repo
    star_repo = messagebox.askyesno(parent=window, title="Contribute", message="Do you want to star the Kwiddle repo on GitHub?")
    if star_repo:
        call(f"open {repo_path}", shell=True)
        star_repo = True
        messagebox.showinfo(parent=window, icon="info", title="Contribute", message="Thank you for contributing to Kwiddle.")
    else:
        star_repo = False

# Startup Functions Execution Script
#contribute_repo()

# 3 - 5 Offline Books Content
clifford = [
    """
    Clifford
    By Norman Bridwell
    Publishing by : Scholastic
    """,

    """
    It's Clifford's bedtime.
    His mother helps him into bed.
    """,

    """
    But Clifford isn't ready.
    He needs his bear.
    """,

    """
    He needs his doll.
    He needs his blanket.
    """,

    """
    Now Clifford needs a drink of water.
    """,

    """
    But Clifford isn't sleepy yet.
    What does Clifford need now?
    """,

    """
    Clifford needs his goodnight kiss.
    """,

    """
    Sweet dreams,
    Clifford.
    """,

    """
    Clifford
    
    THE SMALL RED PUPPY
    
    All rights reserved. Published by Scholastic Inc.
    SCHOLASTIC and associated logos are trademarks and/or
    registered trademarks of Scholastic Inc.
    """
]

cat = [
    """
Cat!
By Eleanor Farjeon
    """,
    """
From Whose Point Of View . . .
Opinions differ. Many of us love to keep cats as pets because cats take care of themselves unlike dogs. There are people who do not like cats at all! It's all a matter of opinion! Here are two differing point of view on cats. Which of the poets admires cats and probably has one as a pet?
    """,
    """
Scat!
Atter her, atter her,
Sleeky flatterer,
Spitfire chatterer,
Scatter her, scatter her
    Off her mat!
    Wuff!
    Wuff!
    Treat her rough!
    """,
    """
Git her, git her,
Whiskery spitter!
Catch her, catch her,
Green-eyed scratcher!
    Slathery
    Slithery
    Hisser,
    Don't miss her!
    """,

    """
Run till you're dithery,
    Hithery
    Thithery
    Pffits, pffits!
    How she spits!
    Spitch! Spatch!
    Can't she scratch!
    """,

    """
Scritching the bark
Of the sycamore - tree,
She's reacher her arc
And hissing at me
    Pffits! Pffits!
    Wuff! Wuff!
    Scat,
    Cat!
    That's
    That!
    """
]

def book(bookname, content:list):
    global page
    window.withdraw()
    book_window = Toplevel(window)
    book_window.title(f"Kwiddle - {bookname}")
    text = Text(book_window, wrap="word")
    text.pack(expand=YES, fill="both")
    text.insert(END, content[page])
    def nextpage():
        global page
        try:
            page += 1
            text.delete(1.0, END)
            text.insert(END, content[page])
        except IndexError:
            messagebox.showinfo(parent=book_window, title="Bookreader", message="Book Completed")
    Button(book_window, text="Next", command=nextpage).pack(anchor="ne", padx=10)

    def lastpage():
        global page
        try:
            page -= 1
            text.delete(1.0, END)
            text.insert(END, content[page])
        except IndexError:
            messagebox.showinfo(parent=book_window, title="Bookreader", message="Book Completed")
    Button(book_window, text="Previous", command=lastpage).pack(anchor="nw", pady=0, padx=10)

book(bookname="Cat!", content=cat)

mainloop()