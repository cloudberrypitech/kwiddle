# Imports
from subprocess import call
from tkinter import * # type: ignore
from tkinter import messagebox

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
tlsun = [
    """
The Little Sun
by Kwiddle Books

    """,

    """
The little sun wakes up each day,
And sends its golden beams our way.
It paints the sky with shades so bright,
And fills the world with happy light.
    """,

    """
The flowers open, fresh and sweet,
The birds begin their morning treat.
The children laugh and run outside,
With sunshine dancing by their side.
    """,

    """
When evening comes, the sun goes down,
And paints the clouds with golden brown.
It waves goodbye beyond the hill,
While sleepy stars begin to fill.
    """,

    """
The Little Sun
By Kwiddle Word Press / Kwiddle Books.

Any book in this program starting with the word Kwiddle is belonging to Kwiddle Book Foundations and has strict copyrights.

BIN / Book Identification Number - 311032
    """,
]

my_little_garden = [
    """
My Little Garden
By Kwiddle Books

    """,
    """
I have a garden small and neat,
With lovely flowers, soft and sweet.
The roses bloom in colors bright,
And butterflies are a pretty sight.
    """,
    """
I water plants both every day,
And pull the little weeds away.
The bees hum softly as they fly,
And busy birds sing from nearby.
    """,
    """
My garden gives me joy each day,
And teaches me to care and stay.
I love each flower, tree, and seed,
For growing plants is a lovely deed.
    """,
    """
My Little Garden
By Kwiddle Word Press

Any book in this program starting with the word Kwiddle is belonging to Kwiddle Word Press and has strict copyrights.

BIN / Book Identification Number - 311023
    """
]

the_friendly_little_bird = [
    """
The Friendly Little Bird
By Kwiddle Wordpress
    """,

    """
A little bird sits in a tree,
And sings a happy song for me.
It hops around from branch to branch,
Then spreads its wings and starts to dance.
    """,

    """
It flies above the houses bright,
And circles gently in the light.
It finds some food and drinks some rain,
Then flies back to its tree again.
    """,

    """
At sunset, when the day is through,
The little bird says, “Tweet, tweet, to you!”
It closes its eyes and rests its head,
And sleeps peacefully in its bed.
    """,

    """
The Friendly Little Bird
By Kwiddle Wordpress

Any book in this program starting with the word Kwiddle is belonging to Kwiddle Word Press and has strict copyrights.

BIN / Book Identification Number - 311022
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
    Button(book_window, text="Next", command=nextpage, height=5, width=10).pack(anchor="ne", padx=10)

    def lastpage():
        global page
        try:
            page -= 1
            text.delete(1.0, END)
            text.insert(END, content[page])
        except IndexError:
            messagebox.showinfo(parent=book_window, title="Bookreader", message="Book Completed")
    Button(book_window, text="Previous", command=lastpage, height=5, width=10).pack(anchor="nw", pady=0, padx=10)

book("The friendly little bird", the_friendly_little_bird)

mainloop()