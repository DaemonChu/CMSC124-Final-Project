import re
import os
import sys
import subprocess
import shutil
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, filedialog, simpledialog, messagebox

from draft import lex, build_symbol_table as get_symbols

# TODO:
# The parts of the GUI are as follows:
# File Explorer – DONE
# Text Editor – PARTIALLY DONE (wrap text needed)
# List of Tokens – DONE
# Symbol Table – DONE
# Execute/Run Button - PARTIALLY DONE (Only up until symbol table so far)
# Console – PARTIALLY DONE (No dialog box pop up for user input yet)

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

        # dinaga ang code: click the title 5 times quickly
        self.title_clicks = 0
        self.reset_job = None
        title.bind("<Button-1>", self.on_title_click)

        # table row (lexeme, line number)
        self.token_info = {}

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
        self.update_line_numbers() # for the line numbers on the left

    def file_explorer(self):
        frame = tk.Frame(self.root)
        frame.grid(row=1, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)

        self.file_path_label = tk.Label(frame, text="(No File Opened)", font=self.info_font, anchor="w", relief="sunken")
        self.file_path_label.grid(row=0, column=0, sticky="ew")

        tk.Button(frame, text="Browse...", command=self.browse_file).grid(row=0, column=1)

    # === MAIN PANEL ===

    # search treeview (helper)
    def search_treeview(self, table, query, whole_word):
        items = table.get_children()

        # nothing to search yet
        if len(items) == 0:
            messagebox.showinfo("Search", "There is nothing to search yet. Execute the program first.")
            return

        query = query.strip().lower()
        if query == "":
            return

        # what if whole word matching?
        pattern = re.escape(query)
        if whole_word:
            pattern = r"(?<!\w)" + pattern + r"(?!\w)"

        # start after the currently selected row, so searching again finds the next match
        start = 0
        selected = table.selection()
        if selected:
            start = items.index(selected[0]) + 1

        # find next matching item
        for item in items[start:] + items[:start]:
            values = " ".join(str(v) for v in table.item(item)["values"])
            if re.search(pattern, values.lower()):
                table.selection_set(item)
                table.focus(item)
                table.see(item)
                return

        messagebox.showinfo("Search", f"No results found for '{query}'.")

    # highlight matched words (Helper)
    def clear_highlight(self):
        self.editor.tag_remove("highlight", "1.0", "end")

    # selecting a row in the token table highlights that lexeme on its line
    def highlight_token(self, event=None):
        selected = self.table.selection()
        if len(selected) == 0 or selected[0] not in self.token_info:
            return

        lexeme, line = self.token_info[selected[0]]
        self.clear_highlight()

        start = self.editor.search(lexeme, str(line) + ".0", str(line) + ".end")
        if start == "":
            return
        self.editor.tag_add("highlight", start, start + "+" + str(len(lexeme)) + "c")
        self.editor.see(start)

    # selecting a row in the symbol table highlights every use of that variable
    def highlight_symbol(self, event=None):
        selected = self.symbol_table.selection()
        if len(selected) == 0:
            return

        name = str(self.symbol_table.item(selected[0])["values"][0])
        self.clear_highlight()

        length = tk.IntVar()
        pattern = r"\m" + name + r"\M"      # \m and \M mark the start and end of a whole word
        start = self.editor.search(pattern, "1.0", "end", regexp=True, count=length)
        first = start
        while start != "":
            end = start + "+" + str(length.get()) + "c"
            self.editor.tag_add("highlight", start, end)
            start = self.editor.search(pattern, end, "end", regexp=True, count=length)

        if first != "":
            self.editor.see(first)

    # editor
    # TODO: wrap text when adjusting the panel

    # for updating the line numbers when scrolling the text editor
    def on_scroll(self, first, last):
        self.scroll.set(first, last)
        self.update_line_numbers()

    def update_line_numbers(self, event=None):
        self.editor.after_idle(self.draw_line_numbers)   # wait until Tk has laid out the text

    # editor line numbers
    def draw_line_numbers(self):
        # src https://stackoverflow.com/questions/76691615/get-start-and-end-index-of-visible-text-in-python-tkinter-text-widget
        # src https://stackoverflow.com/questions/24896747/how-to-display-line-numbers-in-tkinter-text-widget
        # src https://tedboy.github.io/python_stdlib/generated/generated/Tkinter.Text.dlineinfo.html
        self.line_numbers.delete("all")
        last_line = int(self.editor.index("end-1c").split(".")[0])

        index = self.editor.index("@0,0") # first visible line
        while True:
            info = self.editor.dlineinfo(index) # baseline pos of visible line
            line = int(index.split(".")[0])
            if info is None or line > last_line:
                break
            self.line_numbers.create_text(40, info[1], anchor="ne", text=line, font=self.code_font, fill="gray40")
            index = self.editor.index(index + "+1line") # move one line forward from index

    def build_editor(self, frame):
        tk.Label(frame, text="Text Editor", font=self.subheader_font).pack(fill="x")

        # ine numbers
        self.line_numbers = tk.Canvas(frame, width=50, bg="#f3f3f3", highlightthickness=0)        
        self.editor = tk.Text(frame, wrap="none", undo=True, font=self.code_font)
        self.scroll  = ttk.Scrollbar(frame, command=self.editor.yview)
        self.editor.config(yscrollcommand=self.on_scroll)
        
        #  styling for highlighed word
        self.editor.tag_configure("highlight", background="#ffe066", foreground="black")

        self.scroll.pack(side="right", fill="y")
        self.line_numbers.pack(side="left", fill="y")
        self.editor.pack(side="left", fill="both", expand=True)

        self.editor.bind("<KeyRelease>", self.update_line_numbers)   # typing, deleting
        self.editor.bind("<Configure>", self.update_line_numbers)   # panel resized

    # serach token table wrapper
    def search_tokens(self, event=None):
        self.search_treeview(self.table, self.search_entry.get(), self.token_whole.get())

    # list of tokens
    def build_tokens_list(self, frame):
        # src: https://pythonguides.com/python-tkinter-treeview/
        tk.Label(frame, text="Lexemes", font=self.subheader_font).pack(fill="x")

        # search bar
        search_bar = tk.Frame(frame)
        search_bar.pack(fill="x", pady=(0, 3))

        ttk.Button(search_bar, text="Search", command=self.search_tokens).pack(side="right", padx=(5,0))
        self.token_whole = tk.BooleanVar()
        ttk.Checkbutton(search_bar, text="Whole word", variable=self.token_whole).pack(side="right", padx=(5, 0))

        self.search_entry = ttk.Entry(search_bar)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<Return>", self.search_tokens)

        self.table = ttk.Treeview(frame, columns=("lexeme", "classification"), show="headings")
        self.table.column("lexeme", width=150)
        self.table.column("classification", width=200)
        self.table.heading("lexeme", text="Lexeme")
        self.table.heading("classification", text="Classification")
        self.table.bind("<<TreeviewSelect>>", self.highlight_token)

        scroll  = ttk.Scrollbar(frame, command=self.table.yview)
        self.table.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.table.pack(side="left", fill="both", expand=True)
        

    # serach symbol table wrapper
    def search_symbols(self, event=None):
        self.search_treeview(self.symbol_table, self.symbol_entry.get(), self.symbol_whole.get())

    # symbol table
    def build_symbol_table(self, frame):
        tk.Label(frame, text="Symbol Table", font=self.subheader_font).pack(fill="x")

        # search bar
        search_bar = tk.Frame(frame)
        search_bar.pack(fill="x", pady=(0, 3))

        ttk.Button(search_bar, text="Search", command=self.search_symbols).pack(side="right", padx=(5, 0))
        self.symbol_whole = tk.BooleanVar()
        ttk.Checkbutton(search_bar, text="Whole Word", variable=self.symbol_whole).pack(side="right", padx=(5, 0))

        self.symbol_entry = ttk.Entry(search_bar)
        self.symbol_entry.pack(side="left", fill="x", expand=True)
        self.symbol_entry.bind("<Return>", self.search_symbols)

        self.symbol_table = ttk.Treeview(frame, columns=("identifier", "value"), show="headings")
        self.symbol_table.column("identifier", width=150)
        self.symbol_table.column("value", width=200)
        self.symbol_table.heading("identifier", text="Identifier")
        self.symbol_table.heading("value", text="Value")
        self.symbol_table.bind("<<TreeviewSelect>>", self.highlight_symbol)

        scroll = ttk.Scrollbar(frame, command=self.symbol_table.yview)
        self.symbol_table.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.symbol_table.pack(side="left", fill="both", expand=True)

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
        
    # === EXECUTE ===
    def execute_btn(self):
        self.execute_frame = tk.Frame(self.root)
        self.execute_frame.grid(row=3, column=0, sticky="ew")
        self.execute_frame.columnconfigure(0, weight=1)

        tk.Button(self.execute_frame, text="EXECUTE", font=self.subheader_font, fg="#008000", activeforeground="#008000", command=self.execute).grid(row=0, column=0, sticky="ew")  

    # what actually goes on when pressing execute  
    def execute(self):
        source = self.editor.get("1.0", "end-1c")

        # run lexical analyzer
        tokens, errors = lex(source)

        # refresh the token table
        for row in self.table.get_children():
            self.table.delete(row)
        for row in self.symbol_table.get_children():
            self.symbol_table.delete(row)

        # remember each token's line for matching highlight
        self.token_info = {}
        self.clear_highlight()

        # only fill the symbol table when the program has tokens
        if len(tokens) > 0 :
            symbols = get_symbols(tokens)
            for name in symbols:
                self.symbol_table.insert("", "end", values=(name, symbols[name]))

            for lexeme, classification, line_number in tokens:
                item = self.table.insert("", "end", values=(lexeme, classification))
                self.token_info[item] = (lexeme, line_number)

        # console output here
        self.console_clear()

        if len(errors) > 0:
            for error in errors:
                self.console_write(error + "\n", "error")
            return

        self.console_write("Lexical analysis finished with no errors.\n")
        self.run_program(tokens)
    # === CONSOLE ===
    def console_clear(self):
        self.console_box.config(state="normal")
        self.console_box.delete("1.0", tk.END)
        self.console_box.config(state="disabled")

    def console_write(self, text, tag=None):
        self.console_box.config(state="normal")
        self.console_box.insert(tk.END, text, tag)
        self.console_box.see(tk.END)
        self.console_box.config(state="disabled")

    #  TODO: (GIMMEH) dialog box when asking user for input
    def console_input(self, prompt="Enter a value:"):
        value = simpledialog.askstring("GIMMEH", prompt, parent=self.root) 
        if value is None:  # user pressed Cancel
            return ""  # treat Cancel as empty input
        return value  

    # ADDED: walks the token list and runs VISIBLE and GIMMEH
    def run_program(self, tokens):
        # ADDED: start from the symbol table values and scan every token by position
        variables = dict(get_symbols(tokens))
        i = 0
        while i < len(tokens):
            lexeme, kind, line = tokens[i]

            # ADDED: VISIBLE collects every operand on its line and prints them together
            # variables show their value, literals print as-is, unknown variables show NOOB, and quotes, AN, and comments are skipped
            if lexeme == "VISIBLE":
                output = ""
                i += 1
                while i < len(tokens) and tokens[i][2] == line:
                    op_lexeme, op_kind, _ = tokens[i]
                    if op_kind == "Variable Identifier":
                        output += str(variables.get(op_lexeme, "NOOB"))
                    elif op_kind in ("YARN Literal", "NUMBR Literal", "NUMBAR Literal", "TROOF Literal"):
                        output += op_lexeme
                    i += 1
                self.console_write(output + "\n")
                continue

            #  GIMMEH shows the popup and stores the answer in the named variable, then skips past GIMMEH and the variable name
            if lexeme == "GIMMEH" and i + 1 < len(tokens):
                name = tokens[i + 1][0]
                variables[name] = self.console_input("Enter a value for " + name + ":")
                i += 2
                continue

            # any other token is ignored for now
            i += 1

    def console(self):
        frame = tk.Frame(self.root)
        frame.grid(row=4, column=0, sticky="nsew")
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        tk.Label(frame, text="Console", font=self.subheader_font).grid(row=0, column=0, columnspan=2, sticky="ew")
        self.console_box = tk.Text(frame, height=10, state="disabled", font=self.code_font)
        
        scroll = ttk.Scrollbar(frame, command=self.console_box.yview)
        self.console_box.config(yscrollcommand=scroll.set)
        self.console_box.grid(row=1, column=0, sticky="nsew")
        scroll.grid(row=1, column=1, sticky="ns")

        # a separate style for error lines
        self.console_box.tag_configure("error", font=self.error_font, foreground="red")
    
    # === hala may daga ===
    def on_title_click(self, event=None):
        self.title_clicks = self.title_clicks + 1

        # 2 second count down after a click
        if self.reset_job is not None:
            self.root.after_cancel(self.reset_job)
        self.reset_job = self.root.after(2000, self.reset_title_clicks)

        if self.title_clicks >= 5:
            self.title_clicks = 0
            self.mouse()

    def reset_title_clicks(self):
        self.title_clicks = 0
        self.reset_job = None

    def mouse(self):
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "example", "sqksqksqk.mp4")

        if not os.path.exists(path):
            return

        players = [
            ("mpv", ["mpv", "--keep-open=no", path]),                        
            ("vlc", ["vlc", "--play-and-exit", path]),
            ("ffplay", ["ffplay", "-autoexit", path]),
        ]
        for name, command in players:
            if shutil.which(name):          
                subprocess.Popen(command)
                return

        # use the default player
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
            
if __name__ == "__main__":
    root = tk.Tk()
    interpreterGUI(root)
    root.mainloop()