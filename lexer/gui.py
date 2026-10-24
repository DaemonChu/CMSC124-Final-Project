import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, filedialog, simpledialog, messagebox

from draft import lex

# TODO:
# The parts of the GUI are as follows:
# File Explorer – DONE
# Text Editor – PARTIALLY DONE (wrap text needed)
# List of Tokens – DONE
# Symbol Table – TO DO
# Console – TO DO

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
        self.normal_font = tkFont.Font(family="Helvetica", size=11)
        self.header_font = tkFont.Font(family="Helvetica", size=16, weight="bold")
        self.subheader_font = tkFont.Font(family="Helvetica", size=12, weight="bold")
        self.info_font = tkFont.Font(family="Helvetica", size=11, slant="italic")
        self.code_font = tkFont.Font(family="Courier", size=11)
        self.error_font = tkFont.Font(family="Courier", size=11, weight="bold")

        # some other styling
        style = ttk.Style()
        style.configure("Treeview.Heading", font=self.normal_font)
        style.configure("Treeview", font=self.code_font, rowheight=24)

        # label
        title = tk.Label(root, text="LOLCODE Interpreter", font=self.header_font, pady=6)
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
            self.file_path_label.config(text=path, font=self.normal_font)
            self.editor.delete("1.0", tk.END) # delete any content first
            self.editor.insert("1.0", code) 

    def file_explorer(self):
        panel = tk.Frame(self.root)
        panel.grid(row=1, column=0, sticky="ew")
        panel.columnconfigure(0, weight=1)

        self.file_path_label = tk.Label(panel, text="(No File Opened)", font=self.info_font, anchor="w", relief="sunken")
        self.file_path_label.grid(row=0, column=0, sticky="ew")

        tk.Button(panel, text="Browse...", command=self.browse_file).grid(row=0, column=1)


    # === MAIN PANEL ===

    # search treeview (helper)
    def search_treeview(self, table, query):
        items = table.get_children()

        # nothing to search yet
        if len(items) == 0:
            messagebox.showinfo("Search", "There is nothing to search yet. Execute the program first.")
            return

        query = query.strip().lower()
        if query == "":
            return

        # start after the currently selected row, so searching again finds the next match
        start = 0
        selected = table.selection()
        if selected:
            start = items.index(selected[0]) + 1

        # find next matching item
        for item in items[start:] + items[:start]:
            values = " ".join(str(v) for v in table.item(item)["values"])
            if query in values.lower():
                table.selection_set(item)
                table.focus(item)
                table.see(item)
                return

        messagebox.showinfo("Search", f"No results found for '{query}'.")

    # serach token table wrapper
    def search_tokens(self, event=None):
        self.search_treeview(self.table, self.search_entry.get())

    # editor
    # TODO: wrap text when adjusting the panel
    def build_editor(self, frame):
        tk.Label(frame, text="Text Editor", font=self.subheader_font).pack(fill="x")

        self.editor = tk.Text(frame, wrap="none", undo=True, font=self.code_font)
        scroll  = ttk.Scrollbar(frame, command=self.editor.yview)
        self.editor.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.editor.pack(side="left", fill="both", expand=True)

    # list of tokens
    def build_tokens_list(self, frame):
        # src: https://pythonguides.com/python-tkinter-treeview/
        tk.Label(frame, text="Lexemes", font=self.subheader_font).pack(fill="x")

        # search bar
        search_bar = tk.Frame(frame)
        search_bar.pack(fill="x", pady=(0, 3))
        self.search_entry = ttk.Entry(search_bar)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<Return>", self.search_tokens)
        ttk.Button(search_bar, text="Search", command=self.search_tokens).pack(side="left", padx=(5,0))


        self.table = ttk.Treeview(frame, columns=("lexeme", "classification"), show="headings")
        self.table.column("lexeme", width=150)
        self.table.column("classification", width=200)
        self.table.heading("lexeme", text="Lexeme")
        self.table.heading("classification", text="Classificiation")

        scroll  = ttk.Scrollbar(frame, command=self.table.yview)
        self.table.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.table.pack(side="left", fill="both", expand=True)
        
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
        pw.add(token_frame, minsize=200, stretch="always")
        pw.add(symbol_frame, minsize=200, stretch="always")
        
    # execute button
    def execute_btn(self):
        self.execute_frame = tk.Frame(self.root)
        self.execute_frame.grid(row=3, column=0, sticky="ew")
        self.execute_frame.columnconfigure(0, weight=1)

        tk.Button(self.execute_frame, text="EXECUTE", font=self.subheader_font, command=self.execute).grid(
            row=0, column=0, sticky="ew"
        )  

    # what actually goes on when pressing execute  
    def execute(self):
        source = self.editor.get("1.0", "end-1c")

        # run lexical analyzer
        tokens, errors = lex(source)

        # refresh the token table
        for row in self.table.get_children():
            self.tbale.delete(row)

        for lexeme, classification, line_number in tokens:
            self.table.insert("", "end", values=(lexeme, classification))

        # TODO: implement console ; message box muna siyaa
        if len(errors) > 0:
            messagebox.showerror("Lexer errors", "\n".join(errors))

    def console(self):
        pass
        

if __name__ == "__main__":
    root = tk.Tk()
    interpreterGUI(root)
    root.mainloop()