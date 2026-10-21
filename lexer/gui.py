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


    # === FILE EXPLORER ===

    # src : https://www.pythontutorial.net/tkinter/tkinter-open-file-dialog/
    def browse_file(self):
        filetypes=(
            ("LOLCODE files", "*.lol"),
            ('text files', '*.txt'),
            ('All files', '*.*')
        )

        path = filedialog.askopenfilename(
            title="Select a LOLCODE file",
            filetypes=filetypes
        )   

        if path == "":
            return

        with open(path, "r") as f:
            code = f.read()
            self.file_path_label.config(text=path) 
            self.editor.delete("1.0", tk.END) # delete any content first
            self.editor.insert("1.0", code) 

    def file_explorer(self):
        panel = tk.Frame(self.root)
        panel.grid(row=1, column=0, sticky="ew")
        panel.columnconfigure(0, weight=1)

        self.file_path_label = tk.Label(panel, text="(No File Opened)", anchor="w", relief="sunken")
        self.file_path_label.grid(row=0, column=0, sticky="ew")

        tk.Button(panel, text="Browse...", command=self.browse_file).grid(row=0, column=1)


    # === MAIN PANEL ===

    # editor
    def build_editor(self, frame):
        self.editor = tk.Text(frame, wrap="none", undo=True)
        scroll  = ttk.Scrollbar(frame, command=self.editor.yview)
        self.editor.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.editor.pack(side="left", fill="both", expand=True)

    # list of tokens
    def build_tokens_list(self, frame):
        pass

    # TODO: symbol table
    def build_symbol_table(self, frame):
        pass

    # src: https://www.pythontutorial.net/tkinter/tkinter-panedwindow/
    def main_panel(self):
        # use paned window
        pw = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief="raised")
        pw.grid(row=2, column=0, sticky="nsew")

        # frames
        editor_frame = tk.Frame(pw)
        token_frame = tk.Frame(pw)
        symbol_frame = tk.Frame(pw)

        self.build_editor(editor_frame)
        self.build_tokens_list(token_frame)
        self.build_symbol_table(symbol_frame)

        pw.add(editor_frame, minsize=200, stretch="always")
        pw.add(editor_frame, minsize=200, stretch="always")
        pw.add(editor_frame, minsize=200, stretch="always")
        

    def execute_btn(self):
        pass
    
    def console(self):
        pass
        

if __name__ == "__main__":
    root = tk.Tk()
    interpreterGUI(root)
    root.mainloop()