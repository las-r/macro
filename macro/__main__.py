import os
import sys
import macro.lexer
import macro.parser
import macro.nodes

# macro
# by las-r

# constants
TYPES = {"map": dict, "arr": list, "float": float, "int": int, "str": str}

# inbuilt functions
def ibtype(x):
    if isinstance(x, macro.nodes.Function) or callable(x): return "func"
    return {v: k for k, v in TYPES.items()}[type(x)]
    
def ibconv(x, t):
    if t in TYPES:
        return TYPES[t](x)
    raise Exception(f"Unknown convertible type: {t}")

def ibadd(a, i, x):
    ac = a.copy()
    ac.insert(i, x)
    return ac

def ibdel(a, i):
    ac = a.copy()
    ac.pop(i)
    return ac

def ibkeys(m):
    return [*m]

def ibvals(m):
    return [*m.values()]

def main():
    if len(sys.argv) < 2:
        print("usage: python -m macro <file.mic>")
        return
    
    file = sys.argv[1]
    with open(file) as f:
        code = f.read()
        
    tokens = macro.lexer.tokenize(code)
    nodes = macro.parser.parse(tokens)
    
    env = {
        "print": print,
        "input": input,
        "type": ibtype,
        "conv": ibconv,
        "len": len,
        "add": ibadd,
        "del": ibdel,
        "keys": ibkeys,
        "vals": ibvals,
    }
    for node in nodes:
        node.eval(env, [os.path.abspath(file)])
        
if __name__ == "__main__":
    main()