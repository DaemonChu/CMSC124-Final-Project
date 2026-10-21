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
    return word.lstrip("-").isdigit()


def is_numbar(word):
    #one dot, digits on both sides, optional minus at the srtart
    parts = word.lstrip("-").split(".")
    return len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit()


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
                tokens.append((word, kind, line_number))
                rest = rest[len(word):].strip()
                if word == "BTW":#rest of line is a comment
                    if rest != "":
                        tokens.append((rest, "Comment", line_number))
                    rest = ""
                elif word == "OBTW":#comment until TLDR
                    in_multiline_comment = True
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
        errors.append("OBTW comment was never closed with TLDR")
    return tokens, errors

