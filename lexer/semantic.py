# Value types in Python:
#   NOOB = None, NUMBR = int, NUMBAR = float, YARN = str, TROOF = bool

import re
import sys
import math

from main import analyze
from lexer import is_plus
from syntax import (group_by_line, first_word, is_keyword, ARITH_OPS, BOOL_BIN_OPS, COMPARE_OPS, INFINITE_OPS)

# data of the program that is currently running (reset on every run)
PROGRAM = {}

# default value of each type (used by "ITZ A <type>" and by casting a NOOB)
DEFAULTS = {"NOOB": None, "NUMBR": 0, "NUMBAR": 0.0, "YARN": "", "TROOF": False}

# special characters inside a YARN, like :) for a newline
ESCAPES = {")": "\n", ">": "\t", "o": "\a", '"': '"', ":": ":"}


# stops the program, the message is caught in run_program()
def runtime_error(line, message):
    raise RuntimeError("Line " + str(line) + ": " + message)

# 1) TYPES AND TYPECASTING

def type_name(value):
    # check bool first because True is also an int in Python
    if value is None:
        return "NOOB"
    if type(value) is bool:
        return "TROOF"
    if type(value) is int:
        return "NUMBR"
    if type(value) is float:
        return "NUMBAR"
    return "YARN"


# NUMBAR -> YARN: cut to 2 decimal places, 3.14159 -> "3.14", 17.0 -> "17.0"
def float_to_yarn(number):
    sign = ""
    if number < 0:
        sign = "-"
    whole, decimals = format(abs(number), ".10f").split(".")
    decimals = decimals[:2].rstrip("0")
    if decimals == "":
        decimals = "0"
    return sign + whole + "." + decimals


# YARN -> number: with a "." it is a NUMBAR, without it is a NUMBR
def string_to_number(text, line):
    if re.fullmatch(r"-?[0-9]+", text):
        return int(text)
    if re.fullmatch(r"-?[0-9]+\.[0-9]+", text):
        return float(text)
    runtime_error(line, "cannot cast the YARN '" + text + "' to a number")


# implicit casts (happen automatically inside operations)
def to_number(value, line):
    kind = type_name(value)
    if kind == "NUMBR" or kind == "NUMBAR":
        return value
    if kind == "TROOF":
        if value:
            return 1
        return 0
    if kind == "YARN":
        return string_to_number(value, line)
    runtime_error(line, "cannot cast NOOB to a number")


def to_yarn(value, line):
    kind = type_name(value)
    if kind == "NOOB":
        runtime_error(line, "cannot cast NOOB to YARN")
    if kind == "TROOF":
        if value:
            return "WIN"
        return "FAIL"
    if kind == "NUMBR":
        return str(value)
    if kind == "NUMBAR":
        return float_to_yarn(value)
    return value


# anything can be cast to TROOF: NOOB, "" and zero are FAIL, everything else is WIN
def to_troof(value):
    if value is None:
        return False
    if type(value) is str:
        return value != ""
    return value != 0


# explicit cast (MAEK and IS NOW A)
def cast_explicit(value, type_word, line):
    # a NOOB turns into the empty/zero value of the type
    if value is None:
        return DEFAULTS[type_word]
    if type_word == "NOOB":
        return None
    if type_word == "TROOF":
        return to_troof(value)
    if type_word == "YARN":
        return to_yarn(value, line)
    if type_word == "NUMBR":
        return int(to_number(value, line))       # int() cuts the decimal part
    return float(to_number(value, line))         # NUMBAR


# turns the special characters of a YARN into real characters
def unescape(text):
    result = ""
    i = 0
    while i < len(text):
        if text[i] == ":" and i + 1 < len(text) and text[i + 1] in ESCAPES:
            result = result + ESCAPES[text[i + 1]]
            i = i + 2
        else:
            result = result + text[i]
            i = i + 1
    return result




# 2) OPERATIONS

# integer division that cuts towards zero (-7 / 2 = -3)
def int_divide(a, b):
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        q = -q
    return q


def arithmetic(word, a, b, line):
    a = to_number(a, line)
    b = to_number(b, line)
    both_numbr = type(a) is int and type(b) is int

    if word == "SUM OF":
        result = a + b
    elif word == "DIFF OF":
        result = a - b
    elif word == "PRODUKT OF":
        result = a * b
    elif word == "QUOSHUNT OF":
        if b == 0:
            runtime_error(line, "division by zero")
        if both_numbr:
            result = int_divide(a, b)
        else:
            result = a / b
    elif word == "MOD OF":
        if b == 0:
            runtime_error(line, "division by zero")
        if both_numbr:
            result = a - b * int_divide(a, b)
        else:
            result = math.fmod(a, b)
    elif word == "BIGGR OF":
        result = max(a, b)
    else:  # SMALLR OF
        result = min(a, b)

    # two NUMBRs give a NUMBR, if one is a NUMBAR the result is a NUMBAR
    if not both_numbr:
        result = float(result)
    return result


# BOTH SAEM / DIFFRINT: no typecasting, different types are never equal
# (NUMBR and NUMBAR can still be compared with each other)
def values_equal(a, b):
    numbers = ("NUMBR", "NUMBAR")
    if type_name(a) in numbers and type_name(b) in numbers:
        return a == b
    return type_name(a) == type_name(b) and a == b


def apply_binary(word, a, b, line):
    if word in ARITH_OPS:
        return arithmetic(word, a, b, line)
    if word == "BOTH OF":
        return to_troof(a) and to_troof(b)
    if word == "EITHER OF":
        return to_troof(a) or to_troof(b)
    if word == "WON OF":
        return to_troof(a) != to_troof(b)
    if word == "BOTH SAEM":
        return values_equal(a, b)
    return not values_equal(a, b)       # DIFFRINT




# 3) EXPRESSIONS

# evaluate() works like parse_expr() in the syntax analyzer, but it returns the VALUE.
# It starts at token i and returns (value, position after the expression).
def get_variable(variables, name, line):
    if name not in variables:
        runtime_error(line, "variable '" + name + "' is not declared")
    return variables[name]


# is there another item in the list (a AN b AN c)? "AN YR" is the next function argument instead
def more_items(tokens, i):
    if i >= len(tokens) or not is_keyword(tokens[i], "AN"):
        return False
    if i + 1 < len(tokens) and is_keyword(tokens[i + 1], "YR"):
        return False
    return True


def evaluate(tokens, i, variables, line):
    word = tokens[i][0]
    kind = tokens[i][1]

    # literals and variables
    if kind == "NUMBR Literal":
        return int(word), i + 1
    if kind == "NUMBAR Literal":
        return float(word), i + 1
    if kind == "TROOF Literal":
        return word == "WIN", i + 1
    if kind == "Type Literal":                # NOOB
        return None, i + 1
    if kind == "String Delimiter":            # 3 tokens: quote, text, quote
        return unescape(tokens[i + 1][0]), i + 3
    if kind == "Variable Identifier":
        return get_variable(variables, word, line), i + 1

    # <op> <expr> AN <expr>
    if word in ARITH_OPS or word in BOOL_BIN_OPS or word in COMPARE_OPS:
        left, i = evaluate(tokens, i + 1, variables, line)
        right, i = evaluate(tokens, i + 1, variables, line)     # i + 1 skips the AN
        return apply_binary(word, left, right, line), i

    # NOT <expr>
    if word == "NOT":
        value, i = evaluate(tokens, i + 1, variables, line)
        return not to_troof(value), i

    # ALL OF / ANY OF <expr> AN <expr> ... MKAY
    if word in INFINITE_OPS:
        results = []
        i = i + 1
        while True:
            value, i = evaluate(tokens, i, variables, line)
            results.append(to_troof(value))
            if not more_items(tokens, i):
                break
            i = i + 1                          # skip the AN
        i = i + 1                              # skip the MKAY
        if word == "ALL OF":
            return all(results), i
        return any(results), i

    # SMOOSH <expr> AN <expr> ... (MKAY is optional)
    if word == "SMOOSH":
        text = ""
        i = i + 1
        while True:
            value, i = evaluate(tokens, i, variables, line)
            text = text + to_yarn(value, line)
            if not more_items(tokens, i):
                break
            i = i + 1
        if i < len(tokens) and is_keyword(tokens[i], "MKAY"):
            i = i + 1
        return text, i

    # MAEK <expr> [A] <type>
    if word == "MAEK":
        value, i = evaluate(tokens, i + 1, variables, line)
        if is_keyword(tokens[i], "A"):
            i = i + 1
        return cast_explicit(value, tokens[i][0], line), i + 1

    # I IZ <function> [YR <expr> [AN YR <expr> ...]] MKAY
    if word == "I IZ":
        name = tokens[i + 1][0]
        i = i + 2
        arguments = []
        while i < len(tokens) and is_keyword(tokens[i], "YR"):
            value, i = evaluate(tokens, i + 1, variables, line)
            arguments.append(value)
            if i < len(tokens) and is_keyword(tokens[i], "AN"):
                i = i + 1                      # skip the AN, the next token is YR
        i = i + 1                              # skip the MKAY
        return call_function(name, arguments, line), i

    runtime_error(line, "cannot evaluate '" + word + "'")





# 4) FUNCTIONS

def call_function(name, arguments, line):
    functions = PROGRAM["functions"]
    if name not in functions:
        runtime_error(line, "function '" + name + "' is not defined")
    function = functions[name]
    parameters = function["params"]
    if len(parameters) != len(arguments):
        runtime_error(line, "function '" + name + "' needs " + str(len(parameters))
                      + " argument(s) but got " + str(len(arguments)))

    # a function only sees its own variables (its parameters and IT)
    local = {"IT": None}
    for k in range(len(parameters)):
        local[parameters[k]] = arguments[k]

    return run_lines(function["start"] + 1, function["end"], local)





# 5) PREPARING THE PROGRAM

# Finds where every block ends, so jumping is just setting the pc.
# Same idea as the stack in the syntax analyzer.
#   end_of[pc]  =  line of the closer (OIC, IM OUTTA YR, IF U SAY SO) of the block that the opener, YA RLY/MEBBE/NO WAI/OMG/OMGWTF or GTFO on line pc belongs to
#   marks[pc]   =   lines of the YA RLY/MEBBE/NO WAI (if) or OMG/OMGWTF (switch) of an opener
#   loop_start[pc] = for an IM OUTTA YR line: the line of its IM IN YR
def prepare():
    words = PROGRAM["words"]
    statements = PROGRAM["statements"]
    end_of = {}
    marks = {}
    loop_start = {}
    functions = {}
    stack = []

    for pc in range(len(words)):
        word = words[pc]

        if word in ("O RLY?", "WTF?", "IM IN YR", "HOW IZ I"):
            stack.append({"word": word, "start": pc, "marks": [], "gtfos": []})

        elif word in ("YA RLY", "MEBBE", "NO WAI", "OMG", "OMGWTF"):
            stack[-1]["marks"].append(pc)

        elif word == "GTFO":
            # GTFO belongs to the nearest loop / switch / function (never to an if)
            k = len(stack) - 1
            while stack[k]["word"] == "O RLY?":
                k = k - 1
            stack[k]["gtfos"].append(pc)

        elif word in ("OIC", "IM OUTTA YR", "IF U SAY SO"):
            block = stack.pop()
            start = block["start"]
            end_of[start] = pc
            marks[start] = block["marks"]
            for m in block["marks"]:
                end_of[m] = pc
            for g in block["gtfos"]:
                end_of[g] = pc

            if word == "IM OUTTA YR":
                loop_start[pc] = start
            if word == "IF U SAY SO":
                # header: HOW IZ I <name> [YR <param> [AN YR <param> ...]]
                header = statements[start]
                parameters = []
                for token in header[2:]:
                    if token[1] == "Variable Identifier":
                        parameters.append(token[0])
                functions[header[1][0]] = {"params": parameters, "start": start, "end": pc}

    PROGRAM["end_of"] = end_of
    PROGRAM["marks"] = marks
    PROGRAM["loop_start"] = loop_start
    PROGRAM["functions"] = functions





# 6) STATEMENTS

# The do_... functions that change the flow return the NEW pc.
# I HAS A <var> [ITZ <expr> | ITZ A <type>]
def declare(tokens, variables, line):
    name = tokens[1][0]
    value = None                                  # no ITZ means NOOB
    if len(tokens) > 2:
        if is_keyword(tokens[3], "A"):
            value = DEFAULTS[tokens[4][0]]
        else:
            value, i = evaluate(tokens, 3, variables, line)
    variables[name] = value


# VISIBLE <expr> [+ <expr> ...] [!]
def do_visible(tokens, variables, line):
    text = ""
    newline = True
    i = 1
    while i < len(tokens):
        if tokens[i][1] == "Output Suppressor":      # ! means no newline at the end
            newline = False
            i = i + 1
        elif is_plus(tokens[i]):
            i = i + 1
        else:
            value, i = evaluate(tokens, i, variables, line)
            text = text + to_yarn(value, line)
    if newline:
        text = text + "\n"
    PROGRAM["output"](text)


# assignment (R), recast (IS NOW A) or an expression whose result goes to IT
def do_simple(tokens, variables, line):
    first = tokens[0]
    if first[1] == "Variable Identifier" and len(tokens) > 1 and is_keyword(tokens[1], "R"):
        get_variable(variables, first[0], line)       # makes sure it is declared
        value, i = evaluate(tokens, 2, variables, line)
        variables[first[0]] = value
    elif first[1] == "Variable Identifier" and len(tokens) > 1 and is_keyword(tokens[1], "IS NOW A"):
        current = get_variable(variables, first[0], line)
        variables[first[0]] = cast_explicit(current, tokens[2][0], line)
    else:
        value, i = evaluate(tokens, 0, variables, line)
        variables["IT"] = value


# O RLY? : pick the branch using IT
def do_if(pc, variables):
    words = PROGRAM["words"]
    block_marks = PROGRAM["marks"][pc]           # YA RLY, then MEBBEs, then NO WAI

    if to_troof(variables["IT"]):
        return block_marks[0] + 1                # start of the YA RLY block

    for m in block_marks[1:]:
        if words[m] == "NO WAI":
            return m + 1
        condition, i = evaluate(PROGRAM["statements"][m], 1, variables, PROGRAM["numbers"][m])
        if to_troof(condition):
            return m + 1
    return PROGRAM["end_of"][pc] + 1             # nothing matched: skip the whole block


# WTF? : jump to the OMG that equals IT, or to OMGWTF (default), or past OIC
def do_switch(pc, variables):
    words = PROGRAM["words"]
    target = PROGRAM["end_of"][pc] + 1
    for m in PROGRAM["marks"][pc]:
        if words[m] == "OMGWTF":
            target = m + 1
        else:
            literal, i = evaluate(PROGRAM["statements"][m], 1, variables, PROGRAM["numbers"][m])
            if values_equal(variables["IT"], literal):
                return m + 1
    return target


# IM IN YR <label> <UPPIN|NERFIN> YR <var> [TIL|WILE <expr>]
# the TIL/WILE condition is checked at the start of every round
def do_loop_start(pc, variables):
    tokens = PROGRAM["statements"][pc]
    if len(tokens) > 5:
        condition, i = evaluate(tokens, 6, variables, PROGRAM["numbers"][pc])
        stop = to_troof(condition)               # TIL: stop when WIN
        if tokens[5][0] == "WILE":
            stop = not stop                      # WILE: stop when FAIL
        if stop:
            return PROGRAM["end_of"][pc] + 1
    return pc + 1


# IM OUTTA YR : UPPIN/NERFIN the variable, then go back to the loop start
def do_loop_end(pc, variables):
    start = PROGRAM["loop_start"][pc]
    header = PROGRAM["statements"][start]
    line = PROGRAM["numbers"][start]
    name = header[4][0]
    step = 1
    if header[2][0] == "NERFIN":
        step = -1
    variables[name] = to_number(get_variable(variables, name, line), line) + step
    return start





# 7) RUNNING THE PROGRAM

# runs the lines from pc up to (not including) end
# returns the value of FOUND YR, or None (NOOB) if the function returns nothing
def run_lines(pc, end, variables):
    statements = PROGRAM["statements"]
    numbers = PROGRAM["numbers"]
    words = PROGRAM["words"]
    end_of = PROGRAM["end_of"]

    while pc < end:
        tokens = statements[pc]
        line = numbers[pc]
        word = words[pc]

        if word == "HOW IZ I":                   # function definition: skip it
            pc = end_of[pc] + 1

        elif word == "I HAS A":
            declare(tokens, variables, line)
            pc = pc + 1

        elif word == "VISIBLE":
            do_visible(tokens, variables, line)
            pc = pc + 1

        elif word == "GIMMEH":
            get_variable(variables, tokens[1][0], line)       # makes sure it is declared
            variables[tokens[1][0]] = PROGRAM["input"]()      # input is always a YARN
            pc = pc + 1

        elif word == "O RLY?":
            pc = do_if(pc, variables)

        elif word == "MEBBE" or word == "NO WAI":
            # the branch before this one just finished, so skip to the end of the if
            pc = end_of[pc] + 1

        elif word == "WTF?":
            pc = do_switch(pc, variables)

        elif word == "OIC" or word == "OMG" or word == "OMGWTF":
            # for OMG/OMGWTF this is the fall-through into the next case
            pc = pc + 1

        elif word == "IM IN YR":
            pc = do_loop_start(pc, variables)

        elif word == "IM OUTTA YR":
            pc = do_loop_end(pc, variables)

        elif word == "GTFO":
            if words[end_of[pc]] == "IF U SAY SO":
                return None                      # GTFO in a function returns NOOB
            pc = end_of[pc] + 1                  # leave the loop / switch

        elif word == "FOUND YR":
            value, i = evaluate(tokens, 1, variables, line)
            return value

        else:
            do_simple(tokens, variables, line)
            pc = pc + 1

    return None


# runs a whole .lol file
#   read_input()     returns a YARN for GIMMEH (default: input())
#   write_output(t)  called for every VISIBLE (default: sys.stdout.write)

# returns a dictionary:
#   ok         True if the program finished without errors
#   stage      "lexical", "syntax" or "semantic" (where the error happened) or "done"
#   errors     list of error messages
#   tokens     list of tokens (for the lexemes table)
#   variables  variable name -> value (for the symbol table)
def run_program(source, read_input=None, write_output=None):
    result = {"ok": False, "stage": "done", "errors": [], "tokens": [], "variables": {"IT": None}}

    tokens, lex_errors, symbols, syntax_errors = analyze(source)
    result["tokens"] = tokens
    if len(lex_errors) > 0:
        result["stage"] = "lexical"
        result["errors"] = lex_errors
        return result
    if len(syntax_errors) > 0:
        result["stage"] = "syntax"
        result["errors"] = syntax_errors
        return result

    # one statement per line
    statements = []
    numbers = []
    words = []
    for line_number, line_tokens in group_by_line(tokens):
        # a lone MKAY on its own line belongs to the function call before it
        if len(line_tokens) == 1 and line_tokens[0][0] == "MKAY" and len(statements) > 0:
            statements[-1].extend(line_tokens)
            continue
        numbers.append(line_number)
        statements.append(line_tokens)
        words.append(first_word(line_tokens))

    PROGRAM["statements"] = statements
    PROGRAM["numbers"] = numbers
    PROGRAM["words"] = words
    if read_input is None:
        read_input = input
    if write_output is None:
        write_output = sys.stdout.write
    PROGRAM["input"] = read_input
    PROGRAM["output"] = write_output

    sys.setrecursionlimit(3000)
    variables = result["variables"]
    try:
        prepare()
        start = words.index("HAI") + 1
        end = words.index("KTHXBYE")

        # WAZZUP ... BUHBYE holds the global variable declarations
        if words[start] == "WAZZUP":
            start = start + 1
            while words[start] != "BUHBYE":
                declare(statements[start], variables, numbers[start])
                start = start + 1
            start = start + 1

        run_lines(start, end, variables)
        result["ok"] = True
    except RecursionError:       # must come first, RecursionError is also a RuntimeError
        result["stage"] = "semantic"
        result["errors"] = ["the program recursed too deeply"]
    except RuntimeError as e:
        result["stage"] = "semantic"
        result["errors"] = [str(e)]
    return result


# how a value is shown in the symbol table
def format_value(value):
    if value is None:
        return "NOOB"
    if type(value) is bool:
        if value:
            return "WIN"
        return "FAIL"
    return str(value)
