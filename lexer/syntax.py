from lexer import KEYWORD_KINDS, is_plus

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
    current_line = None
    current_tokens = []

    for t in tokens:
        if t[1] in IGNORED_KINDS:
            continue

        if t[1] == "Soft linebreak":
            if current_tokens:
                lines.append((current_line, current_tokens))
            current_line = None
            current_tokens = []
            continue

        if current_line is not None and current_line != t[2]:
            lines.append((current_line, current_tokens))
            current_tokens = []

        current_line = t[2]
        current_tokens.append(t)

    if current_tokens:
        lines.append((current_line, current_tokens))

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
    if kind in LITERAL_KINDS or kind == "Variable Identifier" or (word == "NOOB" and kind == "Type Literal"):
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
 
 
 
def check_visible(tokens, line):
    # accept adjacent output expressions, with or without '+' separators
    i = parse_expr(tokens, 1, line, False, "'VISIBLE'")

    while get(tokens, i) is not None and get(tokens, i)[1] != "Output Suppressor":
        if is_plus(get(tokens, i)):
            i = parse_expr(tokens, i + 1, line, False, "'+'")
        else:
            i = parse_expr(tokens, i, line, False, "'VISIBLE'")

    if get(tokens, i) is not None and get(tokens, i)[1] == "Output Suppressor":
        i += 1

    check_end(tokens, i, line, "the output suppressor must be at the end of VISIBLE")
 
 
def check_gimmeh(tokens, line):
    # GIMMEH <variable>
    variable = get(tokens, 1)
    if variable is None or variable[1] != "Variable Identifier":
        fail(line, "expected a variable after 'GIMMEH', but found " + describe(variable))
    check_end(tokens, 2, line, "GIMMEH takes exactly one variable")
 
 
def check_loop_header(tokens, line):
    # IM IN YR <label> <UPPIN|NERFIN> YR <var> [TIL|WILE <expr>]
    # positions: 0 = IM IN YR | 1 = label | 2 = UPPIN/NERFIN | 3 = YR | 4 = variable | 5 = TIL/WILE | 6... = expression
    
    # the label comes right after IM IN YR
    label = get(tokens, 1)
    if label is None or label[1] != "Loop Identifier":
        fail(line, "expected a loop label after 'IM IN YR', but found " + describe(label))
    
    # spec: the <operation> (UPPIN/NERFIN) is NOT optional, only TIL/WILE is
    operation = get(tokens, 2)
    if not is_keyword(operation, "UPPIN") and not is_keyword(operation, "NERFIN"):
        fail(line, "expected 'UPPIN' or 'NERFIN' after the loop label, but found " + describe(operation))
    
    # then YR
    if not is_keyword(get(tokens, 3), "YR"):
        fail(line, "expected 'YR' after '" + operation[0] + "', but found " + describe(get(tokens, 3)))
    
    # then the variable that gets counted
    variable = get(tokens, 4)
    if variable is None or variable[1] != "Variable Identifier":
        fail(line, "expected a variable after '" + operation[0] + " YR', but found " + describe(variable))
    
    # then (optional) TIL or WILE followed by an expression
    i = 5
    condition = get(tokens, 5)
    if is_keyword(condition, "TIL") or is_keyword(condition, "WILE"):
        i = parse_expr(tokens, 6, line, False, "'" + condition[0] + "'")
    
    # nothing should be left on the line
    check_end(tokens, i, line, "a loop header looks like 'IM IN YR <label> UPPIN YR <var> TIL <expr>'")
 
 
def check_func_header(tokens, line):
    # HOW IZ I <name> [YR <var> [AN YR <var> ...]]
    # positions: 0 = HOW IZ I | 1 = name | then pairs of (YR, variable) separated by AN
    
    # the function name comes right after HOW IZ I
    name = get(tokens, 1)
    if name is None or name[1] != "Function Identifier":
        fail(line, "expected a function name after 'HOW IZ I', but found " + describe(name))
    
    # every YR starts one parameter: YR x   (so "YR x AN YR y" = 2 parameters)
    i = 2
    while is_keyword(get(tokens, i), "YR"):
        parameter = get(tokens, i + 1)
        if parameter is None or parameter[1] != "Variable Identifier":
            fail(line, "expected a parameter name after 'YR', but found " + describe(parameter))
        i += 2     # skip YR and the parameter name
        
        # an AN means another parameter follows, and it must start with YR
        if is_keyword(get(tokens, i), "AN"):
            if not is_keyword(get(tokens, i + 1), "YR"):
                fail(line, "expected 'YR' after 'AN' before the next parameter, but found " + describe(get(tokens, i + 1)))
            i += 1     # skip AN (the while loop then sees the YR)
    
    check_end(tokens, i, line, "parameters are written 'YR x AN YR y'")
 
 
def check_simple(tokens, line):
    # statements that fit on one line and don't start with a statement keyword:
    # assignment, recast, or an expression (its result goes to IT)
    first = tokens[0]
 
    # line starts with a variable: assignment, recast, or the variable alone
    if first[1] == "Variable Identifier":
        second = get(tokens, 1)
        if is_keyword(second, "R"):
            # <variable> R <expression>
            i = parse_expr(tokens, 2, line, False, "'R'")
            check_end(tokens, i, line, "operands of an operation must be separated by 'AN'")
        elif is_keyword(second, "IS NOW A"):
            # <variable> IS NOW A <type>
            i = expect_type(tokens, 2, line, "'IS NOW A'")
            check_end(tokens, i, line)
        elif second is not None:
            fail(line, "unexpected " + describe(second) + " after the variable '" + first[0] + "' - expected 'R' (assignment) or 'IS NOW A' (recast)")
        # if second is None, the variable is alone on its line. That's allowed (it's an expression, result goes to IT)
        return
 
    # line starts like an expression (SUM OF 1 AN 2, a literal, a string, SMOOSH ...)
    starts_expression = (first[1] in LITERAL_KINDS or first[1] == "String Delimiter"
                         or (first[1] in KEYWORD_KINDS and first[0] in EXPR_STARTERS))
    if not starts_expression:
        fail(line, "unexpected " + describe(first) + " at the start of a statement")
 
    i = parse_expr(tokens, 0, line, False)
    check_end(tokens, i, line, "operands of an operation must be separated by 'AN'")
 
 
# Same idea as checking balanced brackets with a stack:
#   opener  -> push it on the stack
#   closer  -> it must match the most recent opener that is still open
#   the end -> anything still on the stack was never closed
# ref : cmsc 141
 
def new_block(name, line, label=None):
    # one open block = a small dictionary
    #   name  : "O RLY?", "WTF?", "IM IN YR", "HOW IZ I" or "WAZZUP"
    #   line  : the line number where it was opened (used in error messages)
    #   label : the loop label (only for loops, otherwise None)
    #   done  : O RLY? -> True after NO WAI was seen | WTF? -> True after OMGWTF was seen
    return {"name": name, "line": line, "label": label, "done": False}
 
 
def inside(stack, names):
    # is any open block one of `names`?  (used for GTFO and FOUND YR)
    for block in stack:
        if block["name"] in names:
            return True
    return False
 
 
def close_block(stack, names, word, line, errors):
    # if a closer (OIC, IM OUTTA YR, ...) was found, find the open block it belongs to and remove it
    # from the stack. if Blocks opened after it were never closed -> report them.
    # `word` is the closer we just found
    # `names` = the openers it is allowed to close, like ("O RLY?", "WTF?") for OIC
 
    # look for the matching opener, starting from the top (the most recent one)
    position = len(stack) - 1
    while position >= 0:
        if stack[position]["name"] in names:
            break
        position = position - 1
 
    # nothing matched: this closer has no opener
    if position < 0:
        fail(line, "'" + word + "' has no matching " + " or ".join(names))
 
    # blocks that were opened AFTER the matching one were never closed
    while len(stack) - 1 > position:
        unclosed = stack.pop()
        errors.append("Line " + str(unclosed["line"]) + ": '" + unclosed["name"] + "' is never closed")
 
    # remove the matching block itself and give it back (loops need its label)
    return stack.pop()
 
 
# COMMENT PLACEMENT (spec: OBTW and TLDR must have their own lines)
# runs on ALL tokens, since group_by_line() throws the comment tokens away
def check_comment_placement(tokens):
    errors = []
    
    # tokens of each line, comments included
    per_line = {}
    for t in tokens:
        per_line.setdefault(t[2], []).append(t)
    
    for line in per_line:
        toks = per_line[line]
        for j in range(len(toks)):
            t = toks[j]
            
            # OBTW must be the FIRST thing on its line (comment text may come after it)
            if t[0] == "OBTW" and t[1] == "Multi-line Comment Delimiter" and j != 0:
                errors.append("Line " + str(line) + ": 'OBTW' must be on its own line (only a comment may share it)")
            
            # TLDR may only share its line with comments
            if t[0] == "TLDR" and t[1] == "Multi-line Comment Delimiter":
                for other in toks[:j] + toks[j + 1:]:
                    if other[1] not in IGNORED_KINDS:
                        errors.append("Line " + str(line) + ": 'TLDR' must be on its own line (only a comment may share it)")
                        break
    return errors
 
 
# syntax_analyze (the main loop)
# go through the program ONE LINE AT A TIME, look at the FIRST KEYWORD
# of the line, and run the check for that kind of statement.
# If a check calls fail(), we catch it, save the message, and move on to the
# next line. 
# ref: https://www.cs.montana.edu/courses/spring2004/450-01/lectures/3-10.html
 
def error_line_number(message):
    # "Line 12: something is wrong"  ->  12   (used to sort the errors by line)
    first_part = message.split(":")[0]     # "Line 12"
    number = first_part.split(" ")[1]      # "12"
    return int(number)
 
 
def first_word(line_tokens):
    # the keyword a line starts with ("" if the line doesn't start with a keyword)
    if line_tokens[0][1] in KEYWORD_KINDS:
        return line_tokens[0][0]
    return ""
 
 
def syntax_analyze(tokens):
    # returns a list of error messages (empty list = no syntax errors)
    
    # OBTW / TLDR sharing a line with a statement
    errors = check_comment_placement(tokens)
    lines = group_by_line(tokens)

    # attach a standalone closing MKAY to the preceding function call
    for n in range(1, len(lines)):
        line_tokens = lines[n][1]
        previous_tokens = lines[n - 1][1]
        if (len(line_tokens) == 1 and is_keyword(line_tokens[0], "MKAY")
                and any(is_keyword(token, "I IZ") for token in previous_tokens)
                and sum(is_keyword(token, "I IZ") is not None for token in previous_tokens)
                > sum(is_keyword(token, "MKAY") is not None for token in previous_tokens)):
            previous_tokens.extend(line_tokens)
            lines[n] = (lines[n][0], [])

    lines = [entry for entry in lines if entry[1]]

    if len(lines) == 0:
        return ["Line 1: the program is empty - it must start with 'HAI' and end with 'KTHXBYE'"]
 
    # first keyword of every line ("" if the line doesn't start with a keyword)
    words = []
    for line, line_tokens in lines:
        words.append(first_word(line_tokens))
    words.append("")    # extra empty entry, so words[n + 1] is safe on the last line
 
    started = False     # becomes True when HAI is seen
    finished = False    # becomes True when KTHXBYE is seen
    stack = []          # the blocks that are still open (see new_block)
 
    for n in range(len(lines)):
        line = lines[n][0]
        line_tokens = lines[n][1]
        word = words[n]
        
        previous_word = ""
        if n > 0:
            previous_word = words[n - 1]
        next_word = words[n + 1]
 
        # the block we are currently inside (None if there is none)
        top = None
        if len(stack) > 0:
            top = stack[-1]
 
        try:
            # outside HAI ... KTHXBYE only function definitions are allowed (per spec) 
            if not started and len(stack) == 0 and word != "HAI" and word != "HOW IZ I":
                errors.append("Line " + str(line) + ": the program must start with 'HAI'")
                started = True    # pretend HAI was there, so we don't repeat this error on every line
            if finished and len(stack) == 0 and word != "HOW IZ I":
                fail(line, "only function definitions may come after 'KTHXBYE'")
 
            # a normal statement while WAZZUP is still open: BUHBYE is missing 
            if top is not None and top["name"] == "WAZZUP":
                if word != "I HAS A" and word != "BUHBYE" and word != "KTHXBYE":
                    errors.append("Line " + str(top["line"]) + ": 'WAZZUP' is never closed - expected 'BUHBYE' before line " + str(line))
                    stack.pop()        # treat WAZZUP as closed and check this line normally
                    top = None
                    if len(stack) > 0:
                        top = stack[-1]
 
            # the line is chosen by its first keyword 
 
            if word == "HAI":
                if started or len(stack) > 0:
                    fail(line, "'HAI' can only appear once, at the start of the program")
                started = True
                # an optional version number is tolerated (HAI 1.2), the spec says it isn't needed
                i = 1
                version = get(line_tokens, 1)
                if version is not None and version[1] == "NUMBAR Literal":
                    i = 2
                check_end(line_tokens, i, line, "'HAI' can only be followed by a version number like 1.2")
 
            elif word == "KTHXBYE":
                # anything still open here was never closed
                while len(stack) > 0:
                    unclosed = stack.pop()
                    errors.append("Line " + str(unclosed["line"]) + ": '" + unclosed["name"] + "' is never closed")
                finished = True
                check_end(line_tokens, 1, line, "'KTHXBYE' must be alone on its line")
 
            # variables: only inside WAZZUP ... BUHBYE 
            elif word == "WAZZUP":
                if previous_word != "HAI":
                    errors.append("Line " + str(line) + ": 'WAZZUP' must come right after 'HAI'")
                stack.append(new_block("WAZZUP", line))
                check_end(line_tokens, 1, line, "'WAZZUP' must be alone on its line")
 
            elif word == "BUHBYE":
                close_block(stack, ("WAZZUP",), word, line, errors)
                check_end(line_tokens, 1, line, "'BUHBYE' must be alone on its line")
 
            elif word == "I HAS A":
                # allow global declarations in WAZZUP and local ones in functions
                if (top is None or
                        (top["name"] != "WAZZUP" and not inside(stack, ("HOW IZ I",)))):
                    fail(line, "variables must be declared in the WAZZUP section or inside a function")
                check_varident(line_tokens, line)
 
            #  if-else 
            elif word == "O RLY?":
                stack.append(new_block("O RLY?", line))
                check_end(line_tokens, 1, line, "'O RLY?' must be alone on its line")
                if next_word != "YA RLY":
                    fail(line, "'O RLY?' must be followed by 'YA RLY' on the next line")
 
            elif word == "YA RLY":
                if top is None or top["name"] != "O RLY?":
                    fail(line, "'YA RLY' has no matching 'O RLY?'")
                if previous_word != "O RLY?":
                    fail(line, "'YA RLY' must come right after 'O RLY?'")
                check_end(line_tokens, 1, line, "'YA RLY' must be alone on its line")
 
            elif word == "MEBBE":
                if top is None or top["name"] != "O RLY?":
                    fail(line, "'MEBBE' has no matching 'O RLY?'")
                if top["done"]:
                    fail(line, "'MEBBE' cannot come after 'NO WAI'")
                i = parse_expr(line_tokens, 1, line, False, "'MEBBE'")
                check_end(line_tokens, i, line)
 
            elif word == "NO WAI":
                if top is None or top["name"] != "O RLY?":
                    fail(line, "'NO WAI' has no matching 'O RLY?'")
                if top["done"]:
                    fail(line, "an 'O RLY?' block can only have one 'NO WAI'")
                top["done"] = True
                check_end(line_tokens, 1, line, "'NO WAI' must be alone on its line")
 
            elif word == "OIC":
                # OIC closes an if-else OR a switch-case
                close_block(stack, ("O RLY?", "WTF?"), word, line, errors)
                check_end(line_tokens, 1, line, "'OIC' must be alone on its line")
 
            # switch-case 
            elif word == "WTF?":
                stack.append(new_block("WTF?", line))
                check_end(line_tokens, 1, line, "'WTF?' must be alone on its line")
                if next_word != "OMG":
                    fail(line, "'WTF?' must be followed by at least one 'OMG' on the next line")
 
            elif word == "OMG":
                if top is None or top["name"] != "WTF?":
                    fail(line, "'OMG' has no matching 'WTF?'")
                if top["done"]:
                    fail(line, "'OMG' cases cannot come after the 'OMGWTF' default case")
                # after OMG there must be ONE literal
                literal = get(line_tokens, 1)
                if literal is not None and literal[1] in LITERAL_KINDS:
                    end_position = 2        # a number / TROOF is 1 token
                elif literal is not None and literal[1] == "String Delimiter":
                    end_position = 4        # a string is 3 tokens: quote, text, quote
                else:
                    fail(line, "'OMG' must be followed by a literal (NUMBR, NUMBAR, YARN or TROOF), but found " + describe(literal))
                check_end(line_tokens, end_position, line, "'OMG' takes exactly one literal")
 
            elif word == "OMGWTF":
                if top is None or top["name"] != "WTF?":
                    fail(line, "'OMGWTF' has no matching 'WTF?'")
                if top["done"]:
                    fail(line, "a switch-case can only have one 'OMGWTF'")
                top["done"] = True
                check_end(line_tokens, 1, line, "'OMGWTF' must be alone on its line")
 
            # loops
            elif word == "IM IN YR":
                label = None
                second = get(line_tokens, 1)
                if second is not None and second[1] == "Loop Identifier":
                    label = second[0]
                # push BEFORE checking the header, so a bad header doesn't also cause a "never closed" error later
                stack.append(new_block("IM IN YR", line, label))
                check_loop_header(line_tokens, line)
 
            elif word == "IM OUTTA YR":
                block = close_block(stack, ("IM IN YR",), word, line, errors)
                label = get(line_tokens, 1)
                if label is None or label[1] != "Loop Identifier":
                    fail(line, "expected the loop label after 'IM OUTTA YR', but found " + describe(label))
                if block["label"] is not None and label[0] != block["label"]:
                    fail(line, "'IM OUTTA YR " + label[0] + "' does not match the loop label '" + block["label"] + "' opened on line " + str(block["line"]))
                check_end(line_tokens, 2, line, "'IM OUTTA YR <label>' must be alone on its line")
 
            # functions
            elif word == "HOW IZ I":
                stack.append(new_block("HOW IZ I", line))
                check_func_header(line_tokens, line)
 
            elif word == "IF U SAY SO":
                close_block(stack, ("HOW IZ I",), word, line, errors)
                check_end(line_tokens, 1, line, "'IF U SAY SO' must be alone on its line")
 
            elif word == "GTFO":
                # break (switch), terminate (loop) or return (function): must be inside one of them
                if not inside(stack, ("IM IN YR", "WTF?", "HOW IZ I")):
                    fail(line, "'GTFO' can only be used inside a loop, a switch-case or a function")
                check_end(line_tokens, 1, line, "'GTFO' must be alone on its line")
 
            elif word == "FOUND YR":
                if not inside(stack, ("HOW IZ I",)):
                    fail(line, "'FOUND YR' can only be used inside a function")
                i = parse_expr(line_tokens, 1, line, False, "'FOUND YR'")
                check_end(line_tokens, i, line)
 
            # input / output
            elif word == "VISIBLE":
                check_visible(line_tokens, line)
 
            elif word == "GIMMEH":
                check_gimmeh(line_tokens, line)
 
            # everything else is a one-line statement
            else:
                check_simple(line_tokens, line)
 
        # fail() was called somewhere above: save the message and go to the next line
        except ValueError as e:
            errors.append(str(e))
 
    # after the last line: every block still on the stack was never closed
    while len(stack) > 0:
        unclosed = stack.pop()
        errors.append("Line " + str(unclosed["line"]) + ": '" + unclosed["name"] + "' is never closed")
 
    if not started:
        errors.append("Line 1: the program must start with 'HAI'")
    if not finished:
        errors.append("Line " + str(lines[-1][0]) + ": the program must end with 'KTHXBYE'")
 
    # errors were saved in the order they were found; show them in line order
    errors.sort(key=error_line_number)
    return errors
