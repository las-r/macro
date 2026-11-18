import os
import sys
import macro.lexer
import macro.parser
import macro.nodes
import macro.errors

# macro
# by las-r

# constants
TYPES = {"map": dict, "arr": list, "float": float, "int": int, "str": str}
TYPENAMES = {v: k for k, v in TYPES.items()}
ANY = object()

# builtin decorator
def builtin(*sig):
    def deco(fn):
        def wrapper(*args):
            if len(args) != len(sig):
                raise macro.errors.MacroArgumentError(f"{fn.__name__}() takes {len(sig)} argument(s), got {len(args)}")
            for i, (a, t) in enumerate(zip(args, sig)):
                if t is ANY:
                    continue
                ts = t if isinstance(t, tuple) else (t,)
                if isinstance(a, bool) or not isinstance(a, ts):
                    names = "/".join(TYPENAMES[x] for x in ts)
                    raise macro.errors.MacroTypeError(f"{fn.__name__}() argument {i + 1} must be {names}, got {macro.nodes.typename(a)}")
            return fn(*args)
        wrapper.__name__ = fn.__name__
        return wrapper
    return deco

# inbuilt functions
@builtin(ANY)
def ibprint(x):
    print(x)

@builtin(str)
def ibinput(p):
    return input(p)

@builtin(ANY)
def ibtype(x):
    return macro.nodes.typename(x)

@builtin(ANY, str)
def ibconv(x, t):
    if t in TYPES:
        return TYPES[t](x)
    raise Exception(f"Unknown convertible type: {t}")

@builtin((str, list, dict))
def iblen(a):
    return len(a)

@builtin(list, int, ANY)
def ibadd(a, i, x):
    ac = a.copy()
    ac.insert(i, x)
    return ac

@builtin((list, dict), (int, str))
def ibdel(a, i):
    ac = a.copy()
    ac.pop(i)
    return ac

@builtin(dict)
def ibkeys(m):
    return [*m]

@builtin(dict)
def ibvals(m):
    return [*m.values()]

def main():
    if len(sys.argv) < 2:
        print("usage: python -m macro <file.mic>")
        return
    
    file = sys.argv[1]
    with open(file) as f:
        code = f.read()

    try:
        tokens = macro.lexer.tokenize(code, file)
        nodes = macro.parser.parse(tokens)
        env = {
            "print": ibprint,
            "input": ibinput,
            "type": ibtype,
            "conv": ibconv,
            "len": iblen,
            "add": ibadd,
            "del": ibdel,
            "keys": ibkeys,
            "vals": ibvals,
        }
        for node in nodes:
            macro.nodes.run(node, env, [os.path.abspath(file)])
    except macro.errors.MacroError as e:
        print(e.format(), file=sys.stderr)
        sys.exit(1)
        
if __name__ == "__main__":
    main()