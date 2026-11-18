import re
from macro.nodes import *

# macro parser
# by las-r

# constant lists
ESCAPES = {"n": "\n", "t": "\t", "r": "\r"}

# tagged decorator
def tagged(fn):
    def wrapper(tokens):
        line = tokens.line()
        node = fn(tokens)
        node.file, node.line = tokens.path, line
        return node
    return wrapper

# atom parser
def parseatom(tokens, index=True):
    # array literals
    if tokens.peek() == "[":
        tokens.eat()
        items = []
        if tokens.peek() != "]":
            items.append(parseexpr(tokens))
            while tokens.peek() == ",":
                tokens.eat()
                items.append(parseexpr(tokens))
        tokens.expect_value("]")
        node = ArrayNode(items)
    
    # map literals
    elif tokens.peek() == "{":
        tokens.eat()
        pairs = []
        if tokens.peek() != "}":
            key = parseexpr(tokens)
            tokens.expect_value("=")
            val = parseexpr(tokens)
            pairs.append((key, val))
            while tokens.peek() == ",":
                tokens.eat()
                key = parseexpr(tokens)
                tokens.expect_value("=")
                val = parseexpr(tokens)
                pairs.append((key, val))
        tokens.expect_value("}")
        node = MapNode(pairs)
    
    # closures
    elif tokens.peek() == "@":
        tokens.eat()
        params = []
        if tokens.peek() == "(":
            tokens.eat()
            if tokens.peek() != ")":
                params.append(tokens.eat())
                while tokens.peek() == ",":
                    tokens.eat()
                    params.append(tokens.eat())
            tokens.expect_value(")")
        body = []
        while tokens.can_eat() and tokens.peek() != "end":
            body.append(parsestmt(tokens))
        tokens.expect_value("end")
        node = FunctionNode(None, params, body)

    # unary ops
    elif tokens.peek() in [*UNOPS]: # pyright: ignore[reportUndefinedVariable]
        op = tokens.eat()
        a = parseatom(tokens, index)
        return UnaryOpNode(op, a)

    # parentheses
    elif tokens.peek() == "(":
        tokens.eat()
        node = parseexpr(tokens)
        tokens.expect_value(")")

    # literal or variable
    else:
        tok = tokens.eat()
        c = tok[0]
        if c == '"':
            node = LiteralNode(re.sub(r"\\(.)", lambda m: ESCAPES.get(m.group(1), m.group(1)), tok[1:-1]))
        elif c.isdigit():
            node = LiteralNode(float(tok) if "." in tok else int(tok))
        elif c.isalpha() or c == "_":
            node = VariableNode(tok)
        else:
            raise tokens.error(f"Unexpected token: {tok}")

    # postfix operations: indexing (:) and calls (())
    while tokens.can_eat() and ((index and tokens.peek() == ":") or tokens.peek() == "("):
        if index and tokens.peek() == ":":
            tokens.eat()
            iexpr = parseatom(tokens, False)
            node = IndexNode(node, iexpr)
        elif tokens.peek() == "(":
            tokens.eat()
            args = []
            if tokens.peek() != ")":
                args.append(parseexpr(tokens))
                while tokens.peek() == ",":
                    tokens.eat()
                    args.append(parseexpr(tokens))
            tokens.expect_value(")")
            node = CallNode(node, args)

    return node

# expression parser
def parseexpr(tokens):
    a = parseatom(tokens)
    while tokens.can_eat() and tokens.peek() in [*BINOPS, "&&", "||"]: # pyright: ignore[reportUndefinedVariable]
        op = tokens.eat()
        b = parseatom(tokens)
        a = BinaryOpNode(a, op, b)
    return a

# statement parser
@tagged
def parsestmt(tokens):
    # if statement
    if tokens.peek() in ("if", "else if"):
        tokens.eat()
        cond = parseexpr(tokens)
        body = []
        while tokens.can_eat() and tokens.peek() not in ("else if", "else", "end"):
            body.append(parsestmt(tokens))
        if tokens.peek() == "else if":
            return IfNode(cond, body, [parsestmt(tokens)])
        ebody = []
        if tokens.peek() == "else":
            tokens.eat()
            while tokens.can_eat() and tokens.peek() != "end":
                ebody.append(parsestmt(tokens))
        tokens.expect_value("end")
        return IfNode(cond, body, ebody)
    
    # while statement
    if tokens.peek() == "while":
        tokens.eat()
        cond = parseexpr(tokens)
        body = []
        while tokens.can_eat() and tokens.peek() != "end":
            body.append(parsestmt(tokens))
        tokens.expect_value("end")
        return WhileNode(cond, body)
    
    # for statement
    if tokens.peek() == "for":
        tokens.eat()
        var = tokens.eat()
        tokens.expect_value(",")
        arr = parseexpr(tokens)
        body = []
        while tokens.can_eat() and tokens.peek() != "end":
            body.append(parsestmt(tokens))
        tokens.expect_value("end")
        return ForNode(var, arr, body)
    
    # break statement
    if tokens.peek() == "break":
        tokens.eat()
        return BreakNode()
    
    # function definition statement
    if tokens.peek() == "func":
        tokens.eat()
        name = tokens.eat()
        params = []
        if tokens.peek() == "(":
            tokens.eat()
            if tokens.peek() != ")":
                params.append(tokens.eat())
                while tokens.peek() == ",":
                    tokens.eat()
                    params.append(tokens.eat())
            tokens.expect_value(")")
        body = []
        while tokens.can_eat() and tokens.peek() != "end":
            body.append(parsestmt(tokens))
        tokens.expect_value("end")
        return FunctionNode(name, params, body)
    
    # return statement
    if tokens.peek() == "return":
        tokens.eat()
        if tokens.can_eat() and tokens.peek() not in ["end", "if", "else", "while", "for", "func"]:
            expr = parseexpr(tokens)
        else:
            expr = None
        return ReturnNode(expr)
    
    # import statement
    if tokens.peek() == "import":
        tokens.eat()
        path = parseexpr(tokens)
        return ImportNode(path)
    
    # assignment
    lhs = parseexpr(tokens)
    if tokens.peek() == "=":
        tokens.eat()
        rhs = parseexpr(tokens)
        if isinstance(lhs, VariableNode):
            return AssignNode(lhs.name, rhs)
        if isinstance(lhs, IndexNode):
            return IndexAssignNode(lhs.arr, lhs.idx, rhs)
        raise tokens.error("Invalid assignment target")
    
    # fallback expression
    return lhs

# error parser
def parseerror(tokens):
    line = tokens.line()
    node = parsestmt(tokens)
    node.file, node.line = tokens.path, line
    return node

# parser
def parse(tokens):
    nodes = []
    while tokens.can_eat():
        nodes.append(parseerror(tokens))
    return nodes