# LOLCODE Interpreter

A Python-based LOLCODE interpreter developed as the final project for CMSC 124 – Design and Implementation of Programming Languages.

**Section:** ST-1L  
**Group:** [1] DIZGRUP  

## Project Description

This project implements a LOLCODE interpreter with a graphical user interface (GUI). It performs three main phases of language processing:

1. **Lexical Analysis** – Identifies lexemes and classifies them into tokens.
2. **Syntax Analysis** – Checks whether the source code follows the LOLCODE grammar.
3. **Semantic Analysis** – Evaluates expressions and executes valid LOLCODE statements.

The GUI allows users to open and edit LOLCODE programs, execute them, and view the tokens, symbol table, and console output.

## Requirements

- Python 3
- Tkinter (Python GUI library)

The interpreter is written in Python and uses Tkinter for its graphical interface.

## Installation and Execution

### Windows

1. Download and install Python 3 from https://www.python.org/downloads/.
2. Download or extract the project files.
3. Open Command Prompt or a terminal in the folder containing `gui.py`.
4. Run:

   ```bash
   py gui.py
   ```

### Linux

1. Make sure Python 3 and Tkinter are installed.
2. Open a terminal in the project directory.
3. Run:

   ```bash
   python3 gui.py
   ```

## How to Use

1. Launch the interpreter by running `gui.py`.
2. Use the file explorer to open a `.lol` file.
3. View or modify the LOLCODE program in the text editor.
4. Click the Execute/Run button to analyze and execute the program.
5. View the detected lexemes and their classifications in the token list.
6. Check the symbol table for program variables and their values.
7. View program output and error messages in the console.

## Project Structure

```text
CMSC124-Final-Project/
├── gui.py
├── main.py
├── src/
│   ├── __init__.py
│   ├── lexer.py
│   ├── syntax.py
│   └── semantic.py
├── example/
├── test_analyzer.py
├── contributors.txt
└── README.md
```

### File Descriptions

| File | Description |
|---|---|
| `gui.py` | Graphical user interface |
| `src/lexer.py` | Lexical analyzer |
| `src/syntax.py` | Syntax analyzer |
| `src/semantic.py` | Semantic analyzer and program execution |
| `src/__init__.py` | Python package initialization |
| `example/` | Sample LOLCODE programs |
| `contributors.txt` | List of group members |

### Note
This README was prepared with the assistance of AI for formatting. The project implementation was developed by the group members.