import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, filedialog, simpledialog

from draft import lex


class interpreterGUI:
    
    def __init__(self, root):
        self.root = root
        root.title("LOLCODE Interpreter [CMSC 124 | DIZGRUP]")
        root.geometry("1200x800")

        # layout grid
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=3) # for the "main panel" (editor, tokens list, symbol table)
        root.rowconfigure(4, weight=2) # for the console

        # fonts
        normal_font = tkFont.Font(family="Segoe UI", size=10)
        header_font = tkFont.Font(family="Segoe UI", size=16, weight="bold")
        subheader_font = tkFont.Font(family="Segoe UI", size=12, weight="bold")
        code_font = tkFont.Font(family="Consolas", size=11)            
        error_font = tkFont.Font(family="Consolas", size=11, weight="bold")
        comment_font = tkFont.Font(family="Consolas", size=11, slant="italic")

        # label
        title = tk.Label(root, text="LOLCODE Interpreter", font=header_font, pady=6)
        title.grid(row=0, column=0, sticky="ew")

        # build the other panels
        self.file_explorer()
        self.main_panel()
        self.execute_btn()
        self.console()


    def file_explorer(self):
        pass

    # txt editor, list of tokens, symbol table
    def main_panel(self):
        pass

    def execute_btn(self):
        pass
    
    def console(self):
        pass
        

if __name__ == "__main__":
    root = tk.Tk()
    interpreterGUI(root)
    root.mainloop()