OPERATORS = ["+", "-", "*", "/", "^"]
FUNCTIONS = ["sin", "cos", "tan"]

def remove_braces(s):
    if (len(s) >= 1) and (s[0] == "(") and (s[-1] == ")"):
        l = 0
        for (i, c) in enumerate(s):
            if c == "(":
                l += 1
            elif c == ")":
                l -= 1
            elif l == 0:
                return s
        if l == 0:
            return remove_braces(s[1:-1])
    return s


def check_function(s) -> (str, str):
    for fn in FUNCTIONS:
        if (len(s) >= len(fn)) and (s[:len(fn)] == fn):
            return fn, s[len(fn):]
    return "", s


def split(s):
    if remove_braces(s) != s:
        return s[1:len(s)-1], "(", None
    fn, t = check_function(s)
    if fn != "":
        return fn, t, None
    for op in OPERATORS:
        i = next_op_pos(s, op)
        if i >= 0:
            return s[:i], s[i], s[i+1:]
    return s, None, None


def next_op_pos(s, op) -> int:
    if op in ["+", "*", "^"]:
        l = 0
        for (i, c) in enumerate(s):
            if c == "(":
                l += 1
            elif c == ")":
                l -= 1
            elif (c == op) and (l == 0):
                return i
        return -1
    elif op in ["-", "/"]:
        l = 0
        for (i, c) in enumerate(reversed(s)):
            if c == "(":
                l += 1
            elif c == ")":
                l -= 1
            elif (c == op) and (l == 0):
                return len(s)-1-i
    return -1
