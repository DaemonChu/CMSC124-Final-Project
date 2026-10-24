# import re, sys
import re
import sys

KEYWORDS = [
    ("HAI", "Code Delimiter"),
    ("KTHXBYE", "Code Delimiter"),
    ("WAZZUP", "Variable Declaration Delimiter"),
    ("BUHBYE", "Variable Declaration Delimiter"),
    ("BTW", "Single-line Comment Keyword"),
    ("OBTW", "Multi-line Comment Delimiter"),
    ("TLDR", "Multi-line Comment Delimiter"),
    ("I HAS A", "Variable Declaration"),
    ("ITZ", "Variable Assignment"),
    ("R", "Assignment Operator"),
    ("SUM OF", "Arithmetic Operator"),
    ("DIFF OF", "Arithmetic Operator"),
    ("PRODUKT OF", "Arithmetic Operator"),
    ("QUOSHUNT OF", "Arithmetic Operator"),
    ("MOD OF", "Arithmetic Operator"),
    ("BIGGR OF", "Arithmetic Operator"),
    ("SMALLR OF", "Arithmetic Operator"),
    ("BOTH OF", "Boolean Operator"),
    ("EITHER OF", "Boolean Operator"),
    ("WON OF", "Boolean Operator"),
    ("NOT", "Boolean Operator"),
    ("ANY OF", "Boolean Operator"),
    ("ALL OF", "Boolean Operator"),
    ("BOTH SAEM", "Comparison Operator"),
    ("DIFFRINT", "Comparison Operator"),
    ("SMOOSH", "Concatenation Operator"),
    ("MAEK", "Typecast Operator"),
    ("A", "Typecast Keyword"),
    ("IS NOW A", "Typecast Operator"),
    ("VISIBLE", "Output Keyword"),
    ("GIMMEH", "Input Keyword"),
    ("O RLY?", "If-Else Delimiter"),
    ("YA RLY", "If-Else Keyword"),
    ("MEBBE", "If-Else Keyword"),
    ("NO WAI", "If-Else Keyword"),
    ("OIC", "Flow Control Delimiter"),
    ("WTF?", "Switch-Case Delimiter"),
    ("OMG", "Switch-Case Keyword"),
    ("OMGWTF", "Switch-Case Keyword"),
    ("IM IN YR", "Loop Delimiter"),
    ("IM OUTTA YR", "Loop Delimiter"),
    ("UPPIN", "Loop Operator"),
    ("NERFIN", "Loop Operator"),
    ("YR", "Parameter Keyword"),
    ("TIL", "Loop Condition"),
    ("WILE", "Loop Condition"),
    ("HOW IZ I", "Function Delimiter"),
    ("IF U SAY SO", "Function Delimiter"),
    ("GTFO", "Break/Return Keyword"),
    ("FOUND YR", "Return Keyword"),
    ("I IZ", "Function Call Keyword"),
    ("MKAY", "Argument Delimiter"),
    ("AN", "Operand Separator"),
]
#always check LONGEST keywords first, since BOTH SAEM can be read as BOTH OF
KEYWORDS.sort(key=lambda pair: len(pair[0]), reverse=True)

# set of every classification that belongs to a keyword
# syntax analyzer uses it to tell a real keyword token apart from YARNs like "HAI"
KEYWORD_KINDS = set(kind for word, kind in KEYWORDS)

def match_keyword(rest):
    #if rest starts with a keyword, return (keyword, class). Else None
    for word, kind in KEYWORDS:
        if rest.startswith(word):
            after = rest[len(word):]
            #the keyword must END here. "ITZ" is a kyword, but "ITZ..." arent
            if after == "" or not (after[0].isalnum() or after[0] == "_"):
                return word, kind
    return None

TYPES = ["NOOB", "NUMBR", "NUMBAR", "YARN", "TROOF"]
TROOFS = ["WIN", "FAIL"]

def read_string(rest):
    #strings start with quotes, return the stuff inside the quotes, return None if there are no end qutoes
    i = 1
    while i < len(rest):
        if rest[i] == '"':
            return rest[1:i]
        else:
            i += 1
    return None


def get_word(rest):
    #return chracters up to next sapce
    return rest.split()[0]


def is_numbr(word):
    # changed return word.lstrip("-").isdigit()
    # since lstrip("-") removes ALL leading hyphens so "--5" will be counted as a NUMBR,
    # and isdigit() also accepts non-ASCII digits. 
    return re.fullmatch(r"-?[0-9]+", word) is not None


def is_numbar(word):
    #one dot, digits on both sides, optional minus at the srtart
    # changed parts = word.lstrip("-").split(".") + isdigit() checks
    # due to same lstrip("-") & isdigit() problem as is_numbr (--1.5 would've been accepted)
    return re.fullmatch(r"-?[0-9]+\.[0-9]+", word) is not None


def is_identifier(word):
    #starts with a letter,then letters,digitsor underscores
    # FIX: reject non-ASCII characters too for consistency : ^[a-zA-Z][a-zA-Z0-9_]*$
    if len(word) == 0 or not word[0].isascii() or not word[0].isalpha():
        return False
    for ch in word:
        if not (ch.isascii() and (ch.isalnum() or ch == "_")):
            return False
    return True

def lex(source):
    #turn code into list of tokens + erros
    #A token is (lexeme, classification, line_number)
    tokens = []
    errors = []
    in_multiline_comment = False#True between OBTW and TLDR
    obtw_line = 0 # remembers which line the OBTW started on (for the "never closed" error)

    lines = source.split("\n")
    for line_number in range(1, len(lines) + 1):
        rest = lines[line_number - 1].strip()

        # --- inside an OBTW ... TLDR comment ---
        if in_multiline_comment:
            # FIX: .startswith("TLDR") alone can catch something like TLDRhello123
            if rest == "TLDR" or rest.startswith("TLDR "):
                tokens.append(("TLDR", "Multi-line Comment Delimiter", line_number))
                in_multiline_comment = False
                rest = rest[4:].strip()
            else:
                if rest != "":
                    tokens.append((rest, "Comment", line_number))
                continue
        while rest != "":

            # 1) string literal
            if rest[0] == '"':
                text = read_string(rest)
                if text is None:
                    errors.append("Line " + str(line_number) + ": string is missing its closing quote")
                    break
                tokens.append(('"', "String Delimiter", line_number))
                tokens.append((text, "YARN Literal", line_number))
                tokens.append(('"', "String Delimiter", line_number))
                rest = rest[len(text) + 2:].strip()
                continue

            # 2) keyword
            found = match_keyword(rest)
            if found is not None:
                word, kind = found
               
                # a TLDR that reaches this point has no OBTW before it
                if word == "TLDR":
                    errors.append("Line " + str(line_number) + ": TLDR has no matching OBTW")
                
                tokens.append((word, kind, line_number))
                rest = rest[len(word):].strip()
                if word == "BTW":#rest of line is a comment
                    if rest != "":
                        tokens.append((rest, "Comment", line_number))
                    rest = ""
                elif word == "OBTW":#comment until TLDR
                    # changed in_multiline_comment = True 
                    # since "OBTW some comment TLDR" on one line is a valid comment
                    text_with_spaces = " " + rest + " "
                    tldr_position = text_with_spaces.find(" TLDR ")
                    
                    # if multi-line
                    if tldr_position == -1:
                        in_multiline_comment = True
                        obtw_line = line_number
                        # keep the text after OBTW as a Comment token, then rest = ""
                        # since spec allows comment text on the OBTW line ("OBTW what way?")
                        if rest != "":
                            tokens.append((rest, "Comment", line_number))
                        rest = ""
                    
                    # if single line
                    else:
                        # get the text between obtw and tldr
                        comment = rest[:tldr_position].strip()
                        
                        # if comment isn't empty, add it to tokens list
                        if comment != "":
                            tokens.append((comment, "Comment", line_number))
                            
                        # append tldr as well
                        tokens.append(("TLDR", "Multi-line Comment Delimiter", line_number))
                        rest = ""
                continue
 
            # 3) everything else is a single word
            word = get_word(rest)
            if is_numbar(word):
                tokens.append((word, "NUMBAR Literal", line_number))
            elif is_numbr(word):
                tokens.append((word, "NUMBR Literal", line_number))
            elif word in TROOFS:
                tokens.append((word, "TROOF Literal", line_number))
            elif word in TYPES:
                tokens.append((word, "Type Literal", line_number))
            elif is_identifier(word):
                #what kind of identifier? look at the token before it
                before = ""
                if len(tokens) > 0:
                    before = tokens[-1][0]
                if before == "HOW IZ I" or before == "I IZ":
                    tokens.append((word, "Function Identifier", line_number))
                elif before == "IM IN YR" or before == "IM OUTTA YR":
                    tokens.append((word, "Loop Identifier", line_number))
                else:
                    tokens.append((word, "Variable Identifier", line_number))
            else:
                errors.append("Line " + str(line_number) + ": unknown lexeme '" + word + "'")
            rest = rest[len(word):].strip()
 
    if in_multiline_comment:
        # changed errors.append("OBTW comment was never closed with TLDR")
        # since every other error message starts with the line number
        errors.append("Line " + str(obtw_line) + ": OBTW comment was never closed with TLDR")
    return tokens, errors
 
 

# add default values per type, used for "ITZ A <type>"
# since "I HAS A x ITZ A NUMBR" is valid per the grammar and used to show a wrong placeholder
DEFAULT_VALUES = {"NOOB": "NOOB", "NUMBR": 0, "NUMBAR": 0.0, "YARN": "", "TROOF": "FAIL"}
 
def build_symbol_table(tokens):
    """Return a dictionary:  variable name -> value."""
    table = {"IT": "NOOB"}# IT always exists in LOLCODE
 
    for i in range(len(tokens)):
        # also check the classification of this token and of the name after it
        # since a comment whose text is exactly "I HAS A" (or "I HAS A 5") would be treated
        # as a declaration and add a junk row to the symbol table
        if (tokens[i][0] == "I HAS A" and tokens[i][1] == "Variable Declaration"
                and i + 1 < len(tokens) and tokens[i + 1][1] == "Variable Identifier"):
            name = tokens[i + 1][0]
            value = "NOOB" # no ITZ means no value yet
 
            #is there an "ITZ <something>" after the name?
            if i + 3 < len(tokens) and tokens[i + 2][0] == "ITZ":
                next_kind = tokens[i + 3][1]
                if next_kind == "String Delimiter":
                    value = tokens[i + 4][0] # the text inside the quotes
                    
                elif next_kind == "NUMBR Literal":
                    value = int(tokens[i + 3][0])
                    
                elif next_kind == "NUMBAR Literal":
                    value = float(tokens[i + 3][0])
                    
                elif next_kind == "TROOF Literal":
                    value = tokens[i + 3][0]
                    
                # ITZ A <type>  -> default value of that type
                elif next_kind == "Typecast Keyword" and i + 4 < len(tokens) and tokens[i + 4][0] in DEFAULT_VALUES:
                    value = DEFAULT_VALUES[tokens[i + 4][0]]
                    
                # ITZ <other variable> -> copy that variable's value 
                elif next_kind == "Variable Identifier" and tokens[i + 3][0] in table:
                    value = table[tokens[i + 3][0]]
                    
                else:
                    value = "(computed when the program runs)"
            table[name] = value
    return table
 
 







# SYNTAX ANALYZER

# separation for convenience of checking syntax
IGNORED_KINDS = ("Comment", "Single-line Comment Keyword", "Multi-line Comment Delimiter")
ARITH_OPS = ("SUM OF", "DIFF OF", "PRODUKT OF", "QUOSHUNT OF", "MOD OF", "BIGGR OF", "SMALLR OF")
BOOL_BIN_OPS = ("BOTH OF", "EITHER OF", "WON OF")
COMPARE_OPS = ("BOTH SAEM", "DIFFRINT")
INFINITE_OPS = ("ANY OF", "ALL OF")
LITERAL_KINDS = ("NUMBR Literal", "NUMBAR Literal", "TROOF Literal")

# for shorthand checking if the start of the expression is valid
EXPR_STARTERS = ARITH_OPS + BOOL_BIN_OPS + COMPARE_OPS + INFINITE_OPS + ("NOT", "SMOOSH", "MAEK", "I IZ")
 
 
def group_by_line(tokens):
    #[(line_number, [tokens of that line without comments]), ...]
    lines = []
    for t in tokens:
        if t[1] in IGNORED_KINDS:
            continue
        
        # if the last line's line number is same as the that of this token
        if len(lines) > 0 and lines[-1][0] == t[2]:
            # add the token to the tokens list of the last line
            lines[-1][1].append(t)
        else:
        
        # create a new entry w/ line no. and list of tokens
            lines.append((t[2], [t]))
    return lines
 

# if a line has an error, stop checking it 
def fail(line, message):
    # the message is caught in syntax_analyze()
    raise ValueError("Line " + str(line) + ": " + message)
 

# safely access tokens 
def get(tokens, i):
    #tokens[i], or None if the line has no more tokens
    if i < len(tokens):
        return tokens[i]
    return None
 
def is_keyword(token, word):
    #is this token the keyword `word`? (a YARN with the same text doesn't count)
    if token is not None and token[0] == word and token[1] in KEYWORD_KINDS:
        return token
    return None
 
def describe(token):
    #how a token is shown in an error message
    if token is None:
        return "end of the line"
    if token[1] == "String Delimiter":
        return "a string"
    if token[1] in KEYWORD_KINDS:
        return "the keyword '" + token[0] + "'"
    
    # if variable, number, etc. just put inside quotes
    return "'" + token[0] + "'"
 
 
def check_end(tokens, i, line, hint="the statement should have ended here"):
    #nothing should be left on the line after position i
    if i < len(tokens):
        fail(line, "unexpected " + describe(tokens[i]) + " - " + hint)
 

# dapat TYPE (NOOB/NUMBR/NUMBAR/YARN/TROOF) ang nasa position i 
def expect_type(tokens, i, line, after):
    t = get(tokens, i)
    if t is None or t[1] != "Type Literal":
        fail(line, "expected a type (NOOB, NUMBR, NUMBAR, YARN or TROOF) after " + after + ", but found " + describe(t))
    return i + 1
 
 
def parse_expr(tokens, i, line, in_inf, after=""):
    #checks ONE expression starting at tokens[i] & returns the position right after it
    #in_inf = True when we're inside ALL OF / ANY OF (since they can't be nested in each other)
    #after = only used in the error message, like "'SUM OF'"
    t = get(tokens, i)
    
    # error message formatting only
    if after != "":
        after = " after " + after
    
    # if line is incomplete
    if t is None:
        fail(line, "expected an expression" + after + ", but the line ended")
    
    # token itself
    word = t[0]
    
    # token classification
    kind = t[1]
 
    # literal or variable
    if kind in LITERAL_KINDS or kind == "Variable Identifier":
        # since we're done checking this position, return the next
        return i + 1
    if kind == "String Delimiter":
        return i + 3 # skip 3 tokens: opening quote, the text, closing quote
 
    if kind in KEYWORD_KINDS:
        
        
        # check if its an operation
        # <op> <expr> AN <expr>
        if word in ARITH_OPS or word in BOOL_BIN_OPS or word in COMPARE_OPS:
            i = parse_expr(tokens, i + 1, line, in_inf, "'" + word + "'")
            
            # after first op, next token should be AN
            if not is_keyword(get(tokens, i), "AN"):
                fail(line, "expected 'AN' between the two operands of '" + word + "', but found " + describe(get(tokens, i)))
            return parse_expr(tokens, i + 1, line, in_inf, "the 'AN' of '" + word + "'")
 
 
 
        # NOT <expr>
        if word == "NOT":
            return parse_expr(tokens, i + 1, line, in_inf, "'NOT'")
 
 
 
        # ALL OF / ANY OF <expr> AN <expr> ... MKAY
        if word in INFINITE_OPS:
            # no to nesting of ALL OF / ANY OF
            if in_inf:
                fail(line, "'" + word + "' cannot be nested inside another 'ALL OF' / 'ANY OF'")
            
            # read the list of operands (True = we're inside the ALL OF/ANY OF block)
            i = parse_expr_list(tokens, i + 1, line, True, "'" + word + "'")
            
            # after first op, next token should be MKAY
            if not is_keyword(get(tokens, i), "MKAY"):
                fail(line, "'" + word + "' must end with 'MKAY', but found " + describe(get(tokens, i)))
            return i + 1
 
 
 
        # SMOOSH <expr> AN <expr> ...   (MKAY is optional)
        if word == "SMOOSH":
            i = parse_expr_list(tokens, i + 1, line, in_inf, "'SMOOSH'")
            
            # since MKAY is optional, just skip it regardless if it exists or not
            if is_keyword(get(tokens, i), "MKAY"):
                i += 1
                
            # return original position
            return i
 
 
 
        # MAEK <expr> [A] <type>
        if word == "MAEK":
            i = parse_expr(tokens, i + 1, line, in_inf, "'MAEK'")
            
            # "A" is optional so just skip
            if is_keyword(get(tokens, i), "A"):
                i += 1
            
            # but it should be followed by a type then return its position after
            return expect_type(tokens, i, line, "'MAEK <expression>'")
 
 
 
        # I IZ <function> [YR <expr> [AN YR <expr> ...]] MKAY
        if word == "I IZ":
            f = get(tokens, i + 1)
            if f is None or f[1] != "Function Identifier":
                fail(line, "expected a function name after 'I IZ', but found " + describe(f))
            
            # skip I IZ and function name
            i += 2
            
            # while keyword is YR
            while is_keyword(get(tokens, i), "YR"):
                # read the expression after YR
                i = parse_expr(tokens, i + 1, line, in_inf, "'YR' in the call to '" + f[0] + "'")
                
                # if there's a succeeding AN, there's also a succeeding argument
                if is_keyword(get(tokens, i), "AN"):
                    
                    # but after AN should be another YR
                    if not is_keyword(get(tokens, i + 1), "YR"):
                        fail(line, "expected 'YR' after 'AN' before the next argument of '" + f[0] + "', but found " + describe(get(tokens, i + 1)))
                    
                    # skip AN since YR na ulit kasunod
                    i += 1
            
            # after all expressions must be an MKAY
            if not is_keyword(get(tokens, i), "MKAY"):
                fail(line, "call to '" + f[0] + "' must end with 'MKAY' (arguments are written 'YR <expr> AN YR <expr>'), but found " + describe(get(tokens, i)))
            return i + 1
    
    # if this is reached, the word isn't a valid keyword
    fail(line, "expected an expression" + after + ", but found " + describe(t))
 
 
 
 
def parse_expr_list(tokens, i, line, in_inf, after):
    #<expr> AN <expr> AN <expr> ...   (for SMOOSH, ALL OF, ANY OF)
    
    # read the first expression
    i = parse_expr(tokens, i, line, in_inf, after)
    
    # "AN YR" starts the next function expression, so it is not part of this list
    while is_keyword(get(tokens, i), "AN") and not is_keyword(get(tokens, i + 1), "YR"):
        i = parse_expr(tokens, i + 1, line, in_inf, "'AN'")
    
    # return the position after the last expression
    return i
 
 
 
 
def check_varident(tokens, line):
    # I HAS A <var> [ITZ <expr> | ITZ A <type>]
    
    # get token after "I HAS A" (it should be a variable name)
    t = get(tokens, 1)
    
    if t is None or t[1] != "Variable Identifier":
        fail(line, "expected a variable name after 'I HAS A', but found " + describe(t))
    
    # else, go to the position after the keyword and varident
    i = 2
    
    # if it's "ITZ" check if may kasunod
    if is_keyword(get(tokens, i), "ITZ"):
        if is_keyword(get(tokens, i + 1), "A"):
            i = expect_type(tokens, i + 2, line, "'ITZ A'")
        else:
            i = parse_expr(tokens, i + 1, line, False, "'ITZ'")
    
    # wala na dapat kasunod sa same line
    check_end(tokens, i, line, "a declaration looks like 'I HAS A x' or 'I HAS A x ITZ <value>'")
 
 
 
# kulang pang functions: 

# 1)
# def check_loop_header(tokens, line):
#     IM IN YR <label> [UPPIN|NERFIN YR <var> [TIL|WILE <expr>]]
 
# 2) 
# def check_func_header(tokens, line):
#     HOW IZ I <name> [YR <var> [AN YR <var> ...]]

# 3)  
# def check_simple(tokens, line):
#     #statements that fit on one line: VISIBLE, GIMMEH, assignment, recast, expression

# 4) 
# def close_block(stack, names, word, line, errors):
#     # if a closer (OIC, IM OUTTA YR, ...) was found, find the open block it belongs to and remove it
#     #from the stack. if Blocks opened after it were never closed -> report them.
 
# 5) pang overall (outline muna)
# def syntax_analyze(tokens):
#     #returns a list of error messages (empty list = syntax is correct)
#     errors = []
#     lines = group_by_line(tokens)
#     if len(lines) == 0:
#         return ["Line 1: the program is empty - it must start with 'HAI' and end with 'KTHXBYE'"]
 
#     phase = "start"   # start -> body (after HAI) -> end (after KTHXBYE)
#     stack = []        # open blocks. Each one is [name, line it started on, extra info]
#     last_word = ""    # keyword that started the previous line (WAZZUP must come right after HAI)
 
#     for line, tokens in lines:
#         first = tokens[0]
#         word = ""     # the keyword this line starts with ("" if it starts with something else)
#         if first[1] in KEYWORD_KINDS:
#             word = first[0]
#         top = None    # the block we're currently inside
#         if len(stack) > 0:
#             top = stack[-1]
 
#         # --- outside HAI ... KTHXBYE only function definitions are allowed (per spec) ---
#         if phase == "start" and len(stack) == 0 and word not in ("HAI", "HOW IZ I"):

#         if phase == "end" and len(stack) == 0 and word != "HOW IZ I":

#             # --- first line inside O RLY? / WTF? / WAZZUP must be the right one ---
#             if top is not None and top[0] == "O RLY?" and top[2] == "need YA RLY" and word != "YA RLY":

#             if top is not None and top[0] == "WTF?" and top[2] == "need OMG" and word != "OMG":

#             if top is not None and top[0] == "WAZZUP" and word not in ("I HAS A", "BUHBYE", "KTHXBYE"):

#             if word == "HAI":
#                
#             elif word == "KTHXBYE":
#                 
#             elif word == "WAZZUP":
#                 
#             elif word == "BUHBYE":
#                
#             elif word == "I HAS A":
#                 
#             elif word == "O RLY?":
#                 
#             elif word == "YA RLY":
#                 
#             elif word == "MEBBE":
#                 
#             elif word == "NO WAI":
#                 
#             elif word == "OIC":
#                 
#             elif word == "WTF?":
#                 
#             elif word == "OMG":
#                 
#             elif word == "IM IN YR":
#                 
#             elif word == "IM OUTTA YR":
#                 
#             elif word == "HOW IZ I":
#                
#             elif word == "IF U SAY SO":
#                
#             elif word == "GTFO":
#                 
#             elif word == "FOUND YR":
#                 
#             else:
#                 check_simple(tokens, line)
 
# one function that does everything, so the GUI can call it later too
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