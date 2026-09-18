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
    """Clifford
       By Norman Bridwell
       Publishing by : Scholastic""",

    """It's Clifford's bedtime.
       His mother helps him into bed.""",

    """But Clifford isn't ready.
       He needs his bear.""",

    """He needs his doll.
       He needs his blanket.""",

    """Now Clifford needs a drink of water.""",

    """But Clifford isn't sleepy yet.
       What does Clifford need now?""",

    """Clifford needs his goodnight kiss.""",

    """Sweet dreams,
        Clifford.""",

    """
    Clifford
    
    THE SMALL RED PUPPY
    
    All rights reserved. Published by Scholastic Inc.
    SCHOLASTIC and associated logos are trademarks and/or
    registered trademarks of Scholastic Inc.
    """
]

def book(bookname, content:list):
    global page
    bookwin = Toplevel(window)
    bookwin.title(f"Kwiddle - {bookname}")
    text = Text(bookwin)
    text.pack()
    text.insert(END, content[page])
    def nextpage():
        global page
        try:
            page += 1
            text.delete(1.0, END)
            text.insert(END, content[page])
        except IndexError:
            messagebox.showinfo(parent=bookwin, title="Bookreader", message="Book Completed")
    Button(bookwin, text="Next", command=nextpage).pack(anchor="ne", padx=10)

    def lastpage():
        global page
        try:
            page -= 1
            text.delete(1.0, END)
            text.insert(END, content[page])
        except IndexError:
            messagebox.showinfo(parent=bookwin, title="Bookreader", message="Book Completed")
    Button(bookwin, text="Previous", command=lastpage).pack(anchor="nw", pady=0, padx=10)

book(bookname="Clifford's Bedtime", content=clifford)

mainloop()