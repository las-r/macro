import operator as oper
import os
from copy import deepcopy
from macro.errors import *

# macro nodes
# by las-r

# constants
UNOPS = {
    "-": oper.neg, "~": oper.inv,
    "!": lambda a: int(a == 0)
}
BINOPS = {
    "+": oper.add, "-": oper.sub, "*": oper.mul, "/": oper.truediv,
    "%": oper.mod, "&": oper.and_, "|": oper.or_, "^": oper.xor,
    "==": lambda a, b: int(a == b),
    "!=": lambda a, b: int(a != b),
    ">=": lambda a, b: int(a >= b),
    "<=": lambda a, b: int(a <= b),
    ">": lambda a, b: int(a > b),
    "<": lambda a, b: int(a < b),
}
TYPENAMES = {dict: "map", list: "arr", float: "float", int: "int", str: "str"}

# typename helper
def typename(x):
    if isinstance(x, Function) or callable(x): return "func"
    return TYPENAMES.get(type(x), type(x).__name__)

# node runner helper
def run(node, env, paths=None):
    try:
        return node.eval(env, paths)
    except (Break, Return):
        raise
    except MacroError as e:
        if not e.stamped:
            e.add_frame(node.file, node.line)
        raise
    except Exception as e:
        err = PYMAP.get(type(e), MacroError)(str(e))
        err.add_frame(node.file, node.line)
        raise err from e

# exceptions
class Break(Exception):
    pass

class Return(Exception):
    def __init__(self, value):
        self.value = value

# function object
class Function:
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env

# literal node
class LiteralNode:
    def __init__(self, value):
        self.value = value
    
    def eval(self, env, paths=None):
        return self.value

# variable nodes
class VariableNode:
    def __init__(self, name):
        self.name = name
    
    def eval(self, env, paths=None):
        if self.name in env:
            return env[self.name]
        raise MacroEnvironmentError(f"Undefined variable: {self.name}")

class AssignNode:
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

    def eval(self, env, paths=None):
        val = self.expr.eval(env)
        if isinstance(val, list):
            val = val.copy()
        env[self.name] = val
    
# operation nodes
class UnaryOpNode:
    def __init__(self, op, a):
        self.op = op
        self.a = a
    
    def eval(self, env, paths=None):
        a = self.a.eval(env)
        if self.op in UNOPS:
            try:
                return UNOPS[self.op](a)
            except TypeError:
                raise MacroTypeError(f"Cannot apply '{self.op}' to {typename(a)}") from None
        raise MacroError(f"Unknown unary operator: {self.op}")
    
class BinaryOpNode:
    def __init__(self, a, op, b):
        self.a = a
        self.op = op
        self.b = b
    
    def eval(self, env, paths=None):
        a = self.a.eval(env)
        if self.op == "&&": return int(a != 0 and self.b.eval(env) != 0)
        if self.op == "||": return int(a != 0 or self.b.eval(env) != 0)
        b = self.b.eval(env)
        if self.op in BINOPS:
            try:
                return BINOPS[self.op](a, b)
            except TypeError:
                raise MacroTypeError(f"Cannot apply '{self.op}' to {typename(a)} and {typename(b)}") from None
        raise MacroError(f"Unknown binary operator: {self.op}")
    
# array and map nodes
class ArrayNode:
    def __init__(self, items):
        self.items = items
        
    def eval(self, env, paths=None):
        return [i.eval(env) for i in self.items]
    
class MapNode:
    def __init__(self, pairs):
        self.pairs = pairs
    
    def eval(self, env, paths=None):
        return {k.eval(env): v.eval(env) for k, v in self.pairs}
    
class IndexNode:
    def __init__(self, arr, idx):
        self.arr = arr
        self.idx = idx
        
    def eval(self, env, paths=None):
        arr = self.arr.eval(env)
        idx = self.idx.eval(env)
        return arr[idx]
    
class IndexAssignNode:
    def __init__(self, arr, idx, val):
        self.arr = arr
        self.idx = idx
        self.val = val
    
    def eval(self, env, paths=None):
        arr = self.arr.eval(env)
        idx = self.idx.eval(env)
        val = self.val.eval(env)
        arr[idx] = val
    
# control flow nodes
class IfNode:
    def __init__(self, cond, body, ebody):
        self.cond = cond
        self.body = body
        self.ebody = ebody
        
    def eval(self, env, paths=None):
        if self.cond.eval(env) != 0:
            for node in self.body:
                run(node, env, paths)
        else:
            for node in self.ebody:
                run(node, env, paths)
                
class WhileNode:
    def __init__(self, cond, body):
            self.cond = cond
            self.body = body
            
    def eval(self, env, paths=None):
        try:
            while self.cond.eval(env) != 0:
                for node in self.body:
                    run(node, env, paths)
        except Break:
            pass
        
class ForNode:
    def __init__(self, var, arr, body):
        self.var = var
        self.arr = arr
        self.body = body
        
    def eval(self, env, paths=None):
        arr = self.arr.eval(env)
        if not isinstance(arr, list):
            raise MacroTypeError(f"Cannot iterate over type: {typename(arr)}")
        try:
            for v in arr:
                env[self.var] = v
                for node in self.body:
                    run(node, env, paths)
        except Break:
            pass
        
class BreakNode:
    def __init__(self):
        pass
    
    def eval(self, env, paths=None):
        raise Break
    
# function nodes
class FunctionNode:
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body
    
    def eval(self, env, paths=None):
        func = Function(self.params, self.body, env)
        if self.name is None:
            return func
        env[self.name] = func
        
class CallNode:
    def __init__(self, func, args):
        self.func = func
        self.args = args

    def eval(self, env, paths=None):
        func = self.func.eval(env)
        copy = lambda v: deepcopy(v) if type(v) in (list, dict) else v
        eargs = [a.eval(env) for a in self.args]
        if callable(func):
            return func(*[copy(a) for a in eargs])
        if isinstance(func, Function):
            if len(self.args) != len(func.params):
                raise MacroArgumentError(f"Expected {len(func.params)} argument(s), got {len(self.args)}")
            lenv = {k: copy(v) for k, v in func.env.items()} | {p: copy(v) for p, v in zip(func.params, eargs)}
            try:
                for node in func.body:
                    run(node, lenv)
            except Return as e:
                return e.value
            except MacroError as e:
                e.stamped = False
                raise
            return
        raise MacroTypeError(f"{typename(func)} is not callable")
    
class ReturnNode:
    def __init__(self, expr):
        self.expr = expr
        
    def eval(self, env, paths=None):
        raise Return(self.expr.eval(env) if self.expr else None)
    
# import nodes
class ImportNode:
    def __init__(self, path):
        self.path = path

    def eval(self, env, paths):
        from . import lexer
        from . import parser
        name = self.path.eval(env)
        fpath = os.path.abspath(os.path.join(os.path.dirname(self.file), name))
        if fpath in paths:
            raise MacroImportError(f"Circular import: {fpath}")
        paths.append(fpath)
        try:
            try:
                with open(fpath) as f:
                    code = f.read()
            except OSError:
                raise MacroImportError(f"Cannot open file: {name}") from None
            tokens = lexer.tokenize(code, fpath)
            nodes = parser.parse(tokens)
            for node in nodes:
                run(node, env, paths)
        except MacroError as e:
            e.stamped = False
            raise
        finally:
            paths.pop()