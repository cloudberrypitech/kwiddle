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
repo_path: str = "https://github.com/cloudberrypitech/kwiddle"


# Default Startup Functions
def contribute_repo():
    global star_repo
    star_repo = messagebox.askyesno(parent=window, title="Contribute",
                                    message="Do you want to star the Kwiddle repo on GitHub?")
    if star_repo:
        call(f"open {repo_path}", shell=True)
        star_repo = True
        messagebox.showinfo(parent=window, icon="info", title="Contribute",
                            message="Thank you for contributing to Kwiddle.")
    else:
        star_repo = False


# Startup Functions Execution Script
#contribute_repo()

def book(bookname, content:list):
    global page
    window.withdraw()
    book_window = Toplevel(window)
    book_window.title(f"Kwiddle - {bookname}")
    text = Text(book_window, wrap="word")
    text.pack(expand=YES, fill="both")
    text.insert(END, content[page])
    text.config(state=DISABLED)
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

book(bookname="clifford", content=clifford)

mainloop()
