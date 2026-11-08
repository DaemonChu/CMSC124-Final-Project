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
    # skip escaped characters before checking for the closing quote
    i = 1
    while i < len(rest):
        if rest[i] == ":" and i + 1 < len(rest):
            i += 2
            continue
        if rest[i] == '"':
            return rest[1:i]
        i += 1
    return None


def get_word(rest):
    return re.match(r"[^,\s+!]+", rest).group(0)


def is_plus(token):
    return token is not None and token[0] == "+" and token[1] == "Concatenation Operator"


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
    source = source.replace("\u201c", '"').replace("\u201d", '"')
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
            if rest[0] == ",":
                tokens.append((",", "Soft linebreak", line_number))
                rest = rest[1:].strip()
                continue

            if rest[0] == "+":
                tokens.append(("+", "Concatenation Operator", line_number))
                rest = rest[1:].strip()
                continue

            if rest[0] == "!":
                tokens.append(("!", "Output Suppressor", line_number))
                rest = rest[1:].strip()
                continue

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
