import os

# macro errors
# by las-r

# constants
SOURCES = {}

# base exception
class MacroError(Exception):
    label = "Error"

    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg
        self.frames = []
        self.stamped = False

    def add_frame(self, path, line):
        self.frames.append((path, line))
        self.stamped = True

    def display(self, path):
        try:
            return os.path.relpath(path)
        except ValueError:
            return path

    def format(self):
        out = []
        for depth, (path, line) in enumerate(reversed(self.frames)): 
            src = SOURCES.get(path, [])
            text = src[line - 1].strip() if line and 0 < line <= len(src) else "?"
            out.append(f'{"    " * depth}"{self.display(path)}", {line} => {text}')
        out.append(f'{"    " * len(self.frames)}{self.label} -> {self.msg}')
        return "\n".join(out)

# errors
class MacroSyntaxError(MacroError): label = "syntaxError"
class MacroEnvironmentError(MacroError): label = "environmentError"
class MacroTypeError(MacroError): label = "typeError"
class MacroIndexError(MacroError): label = "indexError"
class MacroImportError(MacroError): label = "importError"
class MacroArgumentError(MacroError): label = "argumentError"
class MacroMathError(MacroError): label = "mathError"

# python extension map
PYMAP = {
    ZeroDivisionError: MacroMathError,
    IndexError: MacroIndexError,
    KeyError: MacroIndexError,
    TypeError: MacroTypeError,
}