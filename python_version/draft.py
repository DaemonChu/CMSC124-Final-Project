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
    if not word[0].isalpha():
        return False
    for ch in word:
        if not (ch.isalnum() or ch == "_"):
            return False
    return True

