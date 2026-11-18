import os
import re
from macro.errors import *

# macro lexer
# by las-r

# regex pattern
REGEX = re.compile(r"""
    (?P<COMMENT>  //[^\n]*) |
    (?P<NUMBER>   \d+(?:\.\d+)?) |
    (?P<STRING>   "(?:\\.|[^"\\])*") |
    (?P<KEYWORD>  \b(end|if|else[ \t]+if|else|while|for|func|break|return|import)\b) |
    (?P<OPER>     ==|!=|<=|>=|&&|\|\||[+\-*/%<>~&\|^()!:=,\[\]{}@]) |
    (?P<IDENT>    [a-zA-Z_]\w*) |
    (?P<SKIP>     [ \t\r\n]+) |
    (?P<MISMATCH> .)
""", re.VERBOSE)

# tokens classes
class Token(str): line = 0
class Tokens:
    def __init__(self, tokens, path):
        self.tokens = tokens
        self.path = path
        self.i = 0

    def line(self):
        if not self.tokens: return 1
        return self.tokens[min(self.i, len(self.tokens) - 1)].line

    def error(self, msg):
        e = MacroSyntaxError(msg)
        e.add_frame(self.path, self.line())
        return e
        
    def can_eat(self, inc=1):
        return self.i + inc <= len(self.tokens)
        
    def eat(self, inc=1):
        self.i += inc
        return self.tokens[self.i - inc]
    
    def peek(self, off=0):
        if self.i + off >= len(self.tokens):
            return ""
        return self.tokens[self.i + off]
    
    def expect_value(self, value):
        if self.peek() != value:
            raise self.error(f"Expected {value}, got {self.peek()}")
        self.eat()
    
# tokenizer
def tokenize(code, path):
    path = os.path.abspath(path)
    SOURCES[path] = code.splitlines()
    tokens, line = [], 1
    for match in REGEX.finditer(code):
        typ, val = match.lastgroup, match.group()
        if typ == "MISMATCH":
            e = MacroSyntaxError(f"Unexpected token: {val}")
            e.add_frame(path, line)
            raise e
        if typ not in ("SKIP", "COMMENT"):
            if typ == "KEYWORD" and val.startswith("else") and val != "else":
                val = "else if"
            t = Token(val)
            t.line = line
            tokens.append(t)
        line += val.count("\n")
    return Tokens(tokens, path)