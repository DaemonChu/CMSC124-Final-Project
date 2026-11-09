import sys

from lexer import lex, build_symbol_table
from syntax import syntax_analyze

def analyze(source):
    tokens, errors = lex(source)
    symbols = build_symbol_table(tokens)
    syntax_errors = []
    #  Fix lexical errors first, then check the syntax since if unknown lexemes
    # are not in the token list, parsing would only give confusing follow-up errors
    if len(errors) == 0:
        syntax_errors = syntax_analyze(tokens)
    return tokens, errors, symbols, syntax_errors
    
def main():
    # which file to read?
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "sample.lol"
 
    try:
        # changed f = open(path, encoding="utf-8")
        # since files saved by Windows Notepad start with an invisible BOM character, which would make
        # "HAI" an unknown lexeme on line 1
        f = open(path, encoding="utf-8-sig")
    except FileNotFoundError:
        print("Cannot find the file: " + path)
        return
    code = f.read()
    f.close()
 
    # changed tokens, errors = lex(code)
    # since analyze() also runs the syntax analyzer
    tokens, errors, symbols, syntax_errors = analyze(code)
 
    # list of tokens
    print("LEXEMES")
    print("-" * 60)
    print(f"{'Lexeme':<25}{'Classification'}")
    print("-" * 60)
    for lexeme, kind, line_number in tokens:
        print(f"{lexeme:<25}{kind}")
 
    # symbol table
    # analyze() already builds it
    print()
    print("SYMBOL TABLE")
    print("-" * 60)
    print(f"{'Identifier':<25}{'Value'}")
    print("-" * 60)
    for name in symbols:
        print(f"{name:<25}{symbols[name]}")
 
    # errors
    if len(errors) > 0:
        print()
        print("LEXICAL ERRORS")
        print("-" * 60)
        for message in errors:
            print(message)
        print("(syntax analysis was skipped - fix the lexical errors first)")
        return
 
    # syntax errors
    print()
    print("SYNTAX ANALYSIS")
    print("-" * 60)
    if len(syntax_errors) > 0:
        for message in syntax_errors:
            print(message)
        return
    print("No syntax errors found.")
 
    # only a program with no lexical/syntax errors gets here, so the
    # semantic analysis / execution phase can be plugged in below later.
 
 
# changed from main() to if __name__ == "__main__": main()
# since main() ran on import, so the GUI could not import this file
if __name__ == "__main__":
    main()
