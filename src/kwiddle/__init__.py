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
contribute_repo()

mainloop()