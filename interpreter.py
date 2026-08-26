#!/usr/bin/env python3
"""
NEX Programming Language Interpreter v1.1
==========================================
A lightweight scripting language with Python integration.
Supports .N and .nex file extensions.

Author: NEX
License: MIT
Website: https://github.com/nex-lang/nex-lang

Usage:
    nex hello.N          Run a NEX script
    nex --test           Run test suite
    nex install          Install VS Code extension
    nex --help           Show help
    nex                  Start REPL mode
"""
import sys
import os
import importlib
import shutil
import platform
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Any, List, Dict, Optional, Callable
from enum import Enum, auto
from io import StringIO

class TokenType(Enum):
    NUMBER = auto(); STRING = auto(); IDENTIFIER = auto()
    TRUE = auto(); FALSE = auto(); NULL = auto()
    PLUS = auto(); MINUS = auto(); STAR = auto(); SLASH = auto(); PERCENT = auto()
    EQ = auto(); NEQ = auto(); LT = auto(); GT = auto(); LTE = auto(); GTE = auto()
    AND = auto(); OR = auto(); NOT = auto(); ASSIGN = auto()
    LPAREN = auto(); RPAREN = auto(); LBRACKET = auto(); RBRACKET = auto()
    LBRACE = auto(); RBRACE = auto(); COMMA = auto(); DOT = auto(); COLON = auto()
    ARROW = auto(); IMPORT = auto(); OUTPUT = auto(); INPUT = auto()
    FN = auto(); END = auto(); IF = auto(); ELIF = auto(); ELSE = auto()
    LOOP = auto(); IN = auto(); AS = auto()
    FILE_OPEN = auto(); FILE_WRITE = auto(); FILE_CLOSE = auto()
    RETURN = auto(); NEWLINE = auto(); COMMENT = auto(); EOF = auto()

@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    col: int
    lexeme: str

class LexerError(Exception):
    pass

class Lexer:
    def __init__(self, source, filename="<stdin>"):
        self.source = source
        self.filename = filename
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.col = 1
        self.start_col = 1

    def error(self, msg):
        raise LexerError(f"[SyntaxError] Line {self.line}, Col {self.col}: {msg}")

    def is_at_end(self):
        return self.current >= len(self.source)

    def peek(self, offset=0):
        pos = self.current + offset
        if pos >= len(self.source):
            return "\0"
        return self.source[pos]

    def advance(self):
        ch = self.source[self.current]
        self.current += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def match(self, expected):
        if self.is_at_end() or self.source[self.current] != expected:
            return False
        self.advance()
        return True

    def add_token(self, ttype, value=None):
        lexeme = self.source[self.start:self.current]
        self.tokens.append(Token(ttype, value, self.line, self.start_col, lexeme))

    def read_string(self, quote):
        result = []
        while not self.is_at_end() and self.peek() != quote:
            if self.peek() == "\\":
                self.advance()
                esc = self.advance()
                if esc == "n": result.append("\n")
                elif esc == "t": result.append("\t")
                elif esc == "r": result.append("\r")
                elif esc == '"': result.append('"')
                elif esc == "'": result.append("'")
                elif esc == "\\": result.append("\\")
                else: result.append(esc)
            else:
                result.append(self.advance())
        if self.is_at_end():
            self.error("Unterminated string literal")
        self.advance()
        self.add_token(TokenType.STRING, "".join(result))

    def read_number(self):
        while self.peek().isdigit():
            self.advance()
        if self.peek() == "." and self.peek(1).isdigit():
            self.advance()
            while self.peek().isdigit():
                self.advance()
        num_str = self.source[self.start:self.current]
        if "." in num_str:
            self.add_token(TokenType.NUMBER, float(num_str))
        else:
            self.add_token(TokenType.NUMBER, int(num_str))

    def read_identifier(self):
        while not self.is_at_end() and (self.peek().isalnum() or self.peek() == "_"):
            self.advance()
        text = self.source[self.start:self.current]
        keywords = {
            "fn": TokenType.FN, "end": TokenType.END, "in": TokenType.IN,
            "as": TokenType.AS, "true": TokenType.TRUE, "false": TokenType.FALSE,
            "null": TokenType.NULL, "and": TokenType.AND, "or": TokenType.OR,
            "not": TokenType.NOT,
        }
        if text in keywords:
            if text in ("true", "false"):
                self.add_token(keywords[text], text == "true")
            elif text == "null":
                self.add_token(keywords[text], None)
            else:
                self.add_token(keywords[text])
        else:
            self.add_token(TokenType.IDENTIFIER, text)

    def scan_token(self):
        self.start = self.current
        self.start_col = self.col
        if self.is_at_end():
            self.add_token(TokenType.EOF)
            return
        c = self.advance()
        if c == "-" and self.match("-"):
            while not self.is_at_end() and self.peek() != "\n":
                self.advance()
            return
        if c in ('"', "'"):
            self.read_string(c)
            return
        if c.isdigit():
            self.read_number()
            return
        if c.isalpha() or c == "_":
            self.read_identifier()
            return
        if c == "=":
            if self.match("="):
                self.add_token(TokenType.EQ)
            elif self.match(">"):
                self.add_token(TokenType.IMPORT)
            else:
                self.add_token(TokenType.ASSIGN)
            return
        if c == "[":
            if self.peek() == ">" and self.peek(1) == "=":
                self.advance()
                self.advance()
                self.add_token(TokenType.OUTPUT)
            elif self.peek() == "<" and self.peek(1) == "=":
                self.advance()
                self.advance()
                self.add_token(TokenType.INPUT)
            else:
                self.add_token(TokenType.LBRACKET)
            return
        if c == "]":
            self.add_token(TokenType.RBRACKET)
            return
        if c == "<":
            remaining = self.source[self.current:]
            if remaining.startswith("เปิด"):
                for _ in range(4):
                    self.advance()
                self.add_token(TokenType.FILE_OPEN)
                return
            elif self.match("="):
                self.add_token(TokenType.LTE)
            else:
                self.add_token(TokenType.LT)
            return
        if c == ">":
            if self.match(">"):
                self.add_token(TokenType.FILE_WRITE)
            elif self.match("="):
                self.add_token(TokenType.GTE)
            else:
                self.add_token(TokenType.GT)
            return
        if c == "-":
            if self.match(">"):
                self.add_token(TokenType.RETURN)
            else:
                self.add_token(TokenType.MINUS)
            return
        if c == ":":
            if self.match("?"):
                self.add_token(TokenType.ELIF)
            else:
                if self.tokens and self.tokens[-1].type == TokenType.END:
                    self.tokens[-1] = Token(TokenType.FILE_CLOSE, None,
                                           self.tokens[-1].line, self.tokens[-1].col, "end:")
                else:
                    self.add_token(TokenType.ELSE)
            return
        if c == "?":
            self.add_token(TokenType.IF)
            return
        if c == "@":
            self.add_token(TokenType.LOOP)
            return
        if c == "!":
            if self.match("="):
                self.add_token(TokenType.NEQ)
            else:
                self.add_token(TokenType.NOT)
            return
        singles = {
            "+": TokenType.PLUS, "*": TokenType.STAR, "/": TokenType.SLASH,
            "%": TokenType.PERCENT, "(": TokenType.LPAREN, ")": TokenType.RPAREN,
            "{": TokenType.LBRACE, "}": TokenType.RBRACE, ",": TokenType.COMMA,
            ".": TokenType.DOT,
        }
        if c in singles:
            self.add_token(singles[c])
            return
        if c == "\n":
            self.add_token(TokenType.NEWLINE)
            return
        if c in " \t\r":
            return
        self.error(f'Unexpected character "{c}"')

    def scan(self):
        while not self.is_at_end():
            self.scan_token()
        self.start = self.current
        self.start_col = self.col
        self.add_token(TokenType.EOF)
        return self.tokens

# =============================================================================
# AST NODES
# =============================================================================

@dataclass
class NumberLiteral:
    value: float; line: int; col: int

@dataclass
class StringLiteral:
    value: str; line: int; col: int

@dataclass
class BooleanLiteral:
    value: bool; line: int; col: int

@dataclass
class NullLiteral:
    line: int; col: int

@dataclass
class Identifier:
    name: str; line: int; col: int

@dataclass
class ListExpr:
    elements: List[Any]; line: int; col: int

@dataclass
class BinaryOp:
    left: Any; op: str; right: Any; line: int; col: int

@dataclass
class UnaryOp:
    op: str; operand: Any; line: int; col: int

@dataclass
class Assign:
    name: str; value: Any; line: int; col: int

@dataclass
class CallExpr:
    callee: Any; args: List[Any]; line: int; col: int

@dataclass
class IndexExpr:
    obj: Any; index: Any; line: int; col: int

@dataclass
class AttributeExpr:
    obj: Any; attr: str; line: int; col: int

@dataclass
class OutputStmt:
    expr: Any; line: int; col: int

@dataclass
class InputStmt:
    prompt: Any; line: int; col: int

@dataclass
class ImportStmt:
    module: str; names: Optional[List[str]]; alias: Optional[str]; line: int; col: int

@dataclass
class FunctionDef:
    name: str; params: List[str]; body: List[Any]; line: int; col: int

@dataclass
class ReturnStmt:
    value: Any; line: int; col: int

@dataclass
class IfStmt:
    condition: Any; then_body: List[Any]; elif_branches: List[tuple]; else_body: List[Any]; line: int; col: int

@dataclass
class RepeatStmt:
    count: Any; body: List[Any]; line: int; col: int

@dataclass
class ForEachStmt:
    var: str; iterable: Any; body: List[Any]; line: int; col: int

@dataclass
class FileBlockStmt:
    filename: Any; content: Any; line: int; col: int

@dataclass
class Program:
    statements: List[Any]

# =============================================================================
# PARSER
# =============================================================================

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens, filename="<stdin>"):
        self.tokens = tokens
        self.filename = filename
        self.current = 0

    def error(self, msg):
        tok = self.peek()
        raise ParseError(f"[SyntaxError] Line {tok.line}, Col {tok.col}: {msg}")

    def peek(self):
        if self.current >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def is_at_end(self):
        return self.peek().type == TokenType.EOF

    def advance(self):
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def check(self, ttype):
        if self.is_at_end():
            return False
        return self.peek().type == ttype

    def match(self, *types):
        for t in types:
            if self.check(t):
                self.advance()
                return True
        return False

    def consume(self, ttype, msg):
        if self.check(ttype):
            return self.advance()
        self.error(msg)

    def skip_newlines(self):
        while self.match(TokenType.NEWLINE):
            pass

    def parse(self):
        statements = []
        self.skip_newlines()
        while not self.is_at_end():
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        return Program(statements)

    def statement(self):
        self.skip_newlines()
        if self.check(TokenType.IMPORT): return self.import_stmt()
        if self.check(TokenType.OUTPUT): return self.output_stmt()
        if self.check(TokenType.FN): return self.function_def()
        if self.check(TokenType.IF): return self.if_stmt()
        if self.check(TokenType.LOOP): return self.loop_stmt()
        if self.check(TokenType.FILE_OPEN): return self.file_block()
        if self.check(TokenType.RETURN): return self.return_stmt()
        return self.expr_statement()

    def import_stmt(self):
        tok = self.advance()
        line, col = tok.line, tok.col
        if self.check(TokenType.STRING):
            module = self.advance().value
        elif self.check(TokenType.IDENTIFIER):
            module = self.advance().value
        else:
            self.error('Expected module name after "=>"')
        names = None
        alias = None
        if self.match(TokenType.LPAREN):
            names = []
            if not self.check(TokenType.RPAREN):
                names.append(self.consume(TokenType.IDENTIFIER, "Expected identifier").value)
                while self.match(TokenType.COMMA):
                    names.append(self.consume(TokenType.IDENTIFIER, "Expected identifier").value)
            self.consume(TokenType.RPAREN, 'Expected ")" after import list')
        if self.match(TokenType.AS):
            alias = self.consume(TokenType.IDENTIFIER, "Expected alias").value
        return ImportStmt(module, names, alias, line, col)

    def output_stmt(self):
        tok = self.advance()
        line, col = tok.line, tok.col
        expr = self.expression()
        self.consume(TokenType.RBRACKET, 'Expected "]" to close output')
        return OutputStmt(expr, line, col)

    def function_def(self):
        tok = self.advance()
        line, col = tok.line, tok.col
        name = self.consume(TokenType.IDENTIFIER, "Expected function name").value
        self.consume(TokenType.LPAREN, 'Expected "(" after function name')
        params = []
        if not self.check(TokenType.RPAREN):
            params.append(self.consume(TokenType.IDENTIFIER, "Expected parameter").value)
            while self.match(TokenType.COMMA):
                params.append(self.consume(TokenType.IDENTIFIER, "Expected parameter").value)
        self.consume(TokenType.RPAREN, 'Expected ")" after parameters')
        body = self.block_body()
        self.consume(TokenType.END, "Expected 'end' after function body")
        return FunctionDef(name, params, body, line, col)

    def block_body(self):
        statements = []
        self.skip_newlines()
        while not self.check(TokenType.END) and not self.check(TokenType.EOF) and \
              not self.check(TokenType.ELSE) and not self.check(TokenType.ELIF) and \
              not self.check(TokenType.FILE_CLOSE):
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        return statements

    def if_stmt(self):
        tok = self.advance()
        line, col = tok.line, tok.col
        condition = self.expression()
        then_body = self.block_body()
        elif_branches = []
        while self.check(TokenType.ELIF):
            self.advance()
            elif_cond = self.expression()
            elif_body = self.block_body()
            elif_branches.append((elif_cond, elif_body))
        else_body = []
        if self.check(TokenType.ELSE):
            self.advance()
            else_body = self.block_body()
        if not (elif_branches or else_body):
            self.consume(TokenType.END, "Expected 'end' after if statement")
        elif self.check(TokenType.END):
            self.advance()
        return IfStmt(condition, then_body, elif_branches, else_body, line, col)

    def loop_stmt(self):
        tok = self.advance()
        line, col = tok.line, tok.col
        if self.check(TokenType.IDENTIFIER):
            first = self.advance()
            if self.check(TokenType.IN):
                self.advance()
                iterable = self.expression()
                body = self.block_body()
                self.consume(TokenType.END, "Expected 'end' after for loop body")
                return ForEachStmt(first.value, iterable, body, line, col)
            else:
                self.current -= 1
        count = self.expression()
        body = self.block_body()
        self.consume(TokenType.END, "Expected 'end' after loop body")
        return RepeatStmt(count, body, line, col)

    def file_block(self):
        tok = self.advance()
        line, col = tok.line, tok.col
        filename = self.expression()
        self.consume(TokenType.FILE_WRITE, 'Expected ">>" after filename')
        content = self.expression()
        self.skip_newlines()
        self.consume(TokenType.FILE_CLOSE, 'Expected "end:" to close file block')
        return FileBlockStmt(filename, content, line, col)

    def return_stmt(self):
        tok = self.advance()
        line, col = tok.line, tok.col
        value = self.expression()
        return ReturnStmt(value, line, col)

    def expr_statement(self):
        expr = self.expression()
        if isinstance(expr, Identifier) and self.match(TokenType.ASSIGN):
            if self.check(TokenType.INPUT):
                tok = self.advance()
                prompt = self.expression()
                self.consume(TokenType.RBRACKET, 'Expected "]" after input')
                return Assign(expr.name, InputStmt(prompt, tok.line, tok.col), expr.line, expr.col)
            else:
                value = self.expression()
                return Assign(expr.name, value, expr.line, expr.col)
        return expr

    def expression(self):
        return self.or_expr()

    def or_expr(self):
        left = self.and_expr()
        while self.match(TokenType.OR):
            op = self.previous().lexeme
            right = self.and_expr()
            left = BinaryOp(left, op, right, self.previous().line, self.previous().col)
        return left

    def and_expr(self):
        left = self.equality()
        while self.match(TokenType.AND):
            op = self.previous().lexeme
            right = self.equality()
            left = BinaryOp(left, op, right, self.previous().line, self.previous().col)
        return left

    def equality(self):
        left = self.comparison()
        while self.match(TokenType.EQ, TokenType.NEQ):
            op = self.previous().lexeme
            right = self.comparison()
            left = BinaryOp(left, op, right, self.previous().line, self.previous().col)
        return left

    def comparison(self):
        left = self.term()
        while self.match(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self.previous().lexeme
            right = self.term()
            left = BinaryOp(left, op, right, self.previous().line, self.previous().col)
        return left

    def term(self):
        left = self.factor()
        while self.match(TokenType.MINUS, TokenType.PLUS):
            op = self.previous().lexeme
            right = self.factor()
            left = BinaryOp(left, op, right, self.previous().line, self.previous().col)
        return left

    def factor(self):
        left = self.unary()
        while self.match(TokenType.SLASH, TokenType.STAR, TokenType.PERCENT):
            op = self.previous().lexeme
            right = self.unary()
            left = BinaryOp(left, op, right, self.previous().line, self.previous().col)
        return left

    def unary(self):
        if self.match(TokenType.NOT, TokenType.MINUS):
            op = self.previous().lexeme
            operand = self.unary()
            return UnaryOp(op, operand, self.previous().line, self.previous().col)
        return self.call()

    def call(self):
        expr = self.primary()
        while True:
            if self.match(TokenType.LPAREN):
                args = []
                if not self.check(TokenType.RPAREN):
                    args.append(self.expression())
                    while self.match(TokenType.COMMA):
                        args.append(self.expression())
                self.consume(TokenType.RPAREN, 'Expected ")" after arguments')
                expr = CallExpr(expr, args, expr.line, expr.col)
            elif self.match(TokenType.LBRACKET):
                index = self.expression()
                self.consume(TokenType.RBRACKET, 'Expected "]" after index')
                expr = IndexExpr(expr, index, expr.line, expr.col)
            elif self.match(TokenType.DOT):
                attr = self.consume(TokenType.IDENTIFIER, "Expected attribute name").value
                expr = AttributeExpr(expr, attr, expr.line, expr.col)
            else:
                break
        return expr

    def primary(self):
        if self.match(TokenType.TRUE): return BooleanLiteral(True, self.previous().line, self.previous().col)
        if self.match(TokenType.FALSE): return BooleanLiteral(False, self.previous().line, self.previous().col)
        if self.match(TokenType.NULL): return NullLiteral(self.previous().line, self.previous().col)
        if self.match(TokenType.NUMBER): return NumberLiteral(self.previous().value, self.previous().line, self.previous().col)
        if self.match(TokenType.STRING): return StringLiteral(self.previous().value, self.previous().line, self.previous().col)
        if self.match(TokenType.IDENTIFIER): return Identifier(self.previous().value, self.previous().line, self.previous().col)
        if self.match(TokenType.LBRACKET):
            elements = []
            if not self.check(TokenType.RBRACKET):
                elements.append(self.expression())
                while self.match(TokenType.COMMA):
                    elements.append(self.expression())
            self.consume(TokenType.RBRACKET, 'Expected "]" after list')
            return ListExpr(elements, self.previous().line, self.previous().col)
        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, 'Expected ")" after expression')
            return expr
        self.error(f'Unexpected token "{self.peek().lexeme}"')

# =============================================================================
# RUNTIME VALUES
# =============================================================================

class NEXValue:
    pass

class NEXNumber(NEXValue):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        if isinstance(self.value, int) or self.value == int(self.value):
            return str(int(self.value))
        return str(self.value)

class NEXString(NEXValue):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return self.value

class NEXBoolean(NEXValue):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return "true" if self.value else "false"

class NEXNull(NEXValue):
    def __repr__(self):
        return "null"

class NEXList(NEXValue):
    def __init__(self, elements):
        self.elements = elements
    def __repr__(self):
        return "[" + ", ".join(str(e) for e in self.elements) + "]"

class NEXFunction(NEXValue):
    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure
    def __repr__(self):
        return f"<fn {self.name}>"

class NEXPythonModule(NEXValue):
    def __init__(self, module, exports=None):
        self.module = module
        self.exports = exports
    def get(self, name):
        if self.exports is not None and name not in self.exports:
            return None
        return getattr(self.module, name, None)
    def __repr__(self):
        return f"<module {self.module.__name__}>"

class NEXPythonCallable(NEXValue):
    def __init__(self, callable_obj):
        self.callable = callable_obj
    def __repr__(self):
        return "<python callable>"

class NEXPythonObject(NEXValue):
    def __init__(self, obj):
        self.obj = obj
    def __repr__(self):
        return str(self.obj)

class NEXModule(NEXValue):
    def __init__(self, env, exports=None):
        self.env = env
        self.exports = exports or []
    def get(self, name):
        if self.exports and name not in self.exports:
            return None
        return self.env.get(name)
    def __repr__(self):
        return "<module>"

# =============================================================================
# ENVIRONMENT
# =============================================================================

class Environment:
    def __init__(self, enclosing=None):
        self.values = {}
        self.enclosing = enclosing

    def define(self, name, value):
        self.values[name] = value

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.enclosing:
            return self.enclosing.get(name)
        return None

    def set(self, name, value):
        if name in self.values:
            self.values[name] = value
            return True
        if self.enclosing:
            return self.enclosing.set(name, value)
        return False

# =============================================================================
# EVALUATOR
# =============================================================================

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class Evaluator:
    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.globals = Environment()
        self.environment = self.globals
        self._setup_builtins()

    def _setup_builtins(self):
        builtins = ["len", "type", "str", "num", "int", "float", "range",
                    "append", "split", "join", "upper", "lower", "contains",
                    "keys", "values"]
        for name in builtins:
            self.globals.define(name, NEXFunction(name, ["obj"], None, None))

    def evaluate(self, node):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self._no_visit)
        return method(node)

    def _no_visit(self, node):
        raise RuntimeError(f"No visit method for {type(node).__name__}")

    def visit_Program(self, node):
        result = NEXNull()
        for stmt in node.statements:
            result = self.evaluate(stmt)
        return result

    def visit_NumberLiteral(self, node):
        return NEXNumber(node.value)

    def visit_StringLiteral(self, node):
        return NEXString(node.value)

    def visit_BooleanLiteral(self, node):
        return NEXBoolean(node.value)

    def visit_NullLiteral(self, node):
        return NEXNull()

    def visit_Identifier(self, node):
        value = self.environment.get(node.name)
        if value is None:
            raise RuntimeError(f'[RuntimeError] Line {node.line}: Undefined variable "{node.name}"')
        return value

    def visit_ListExpr(self, node):
        elements = [self.evaluate(e) for e in node.elements]
        return NEXList(elements)

    def visit_BinaryOp(self, node):
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        if node.op == "+":
            if isinstance(left, NEXString) or isinstance(right, NEXString):
                return NEXString(self._to_string(left) + self._to_string(right))
            if isinstance(left, NEXNumber) and isinstance(right, NEXNumber):
                return NEXNumber(left.value + right.value)
            if isinstance(left, NEXList) and isinstance(right, NEXList):
                return NEXList(left.elements + right.elements)
            raise RuntimeError(f"[RuntimeError] Line {node.line}: Cannot add {type(left).__name__} and {type(right).__name__}")
        if node.op == "and": return NEXBoolean(self._is_truthy(left) and self._is_truthy(right))
        elif node.op == "or": return NEXBoolean(self._is_truthy(left) or self._is_truthy(right))
        elif node.op == "==": return NEXBoolean(self._equals(left, right))
        elif node.op == "!=": return NEXBoolean(not self._equals(left, right))
        if not isinstance(left, NEXNumber) or not isinstance(right, NEXNumber):
            raise RuntimeError(f'[RuntimeError] Line {node.line}: Operation "{node.op}" requires numeric operands')
        if node.op == "-": return NEXNumber(left.value - right.value)
        elif node.op == "*": return NEXNumber(left.value * right.value)
        elif node.op == "/":
            if right.value == 0:
                raise RuntimeError(f"[RuntimeError] Line {node.line}: Cannot divide by zero")
            return NEXNumber(left.value / right.value)
        elif node.op == "%":
            if right.value == 0:
                raise RuntimeError(f"[RuntimeError] Line {node.line}: Cannot modulo by zero")
            return NEXNumber(left.value % right.value)
        elif node.op == "<": return NEXBoolean(left.value < right.value)
        elif node.op == ">": return NEXBoolean(left.value > right.value)
        elif node.op == "<=": return NEXBoolean(left.value <= right.value)
        elif node.op == ">=": return NEXBoolean(left.value >= right.value)
        raise RuntimeError(f'[RuntimeError] Line {node.line}: Unknown operator "{node.op}"')

    def visit_UnaryOp(self, node):
        operand = self.evaluate(node.operand)
        if node.op == "-":
            if not isinstance(operand, NEXNumber):
                raise RuntimeError(f"[RuntimeError] Line {node.line}: Cannot negate non-number")
            return NEXNumber(-operand.value)
        elif node.op == "not":
            return NEXBoolean(not self._is_truthy(operand))
        raise RuntimeError(f'[RuntimeError] Line {node.line}: Unknown unary operator "{node.op}"')

    def visit_Assign(self, node):
        value = self.evaluate(node.value)
        if isinstance(value, InputStmt):
            prompt_val = self.evaluate(value.prompt)
            prompt_str = self._to_string(prompt_val)
            try:
                user_input = input(prompt_str)
            except EOFError:
                user_input = ""
            try:
                if "." in user_input:
                    result = NEXNumber(float(user_input))
                else:
                    result = NEXNumber(int(user_input))
            except ValueError:
                result = NEXString(user_input)
            self.environment.define(node.name, result)
            return result
        if not self.environment.set(node.name, value):
            self.environment.define(node.name, value)
        return value

    def visit_CallExpr(self, node):
        callee = self.evaluate(node.callee)
        args = [self.evaluate(arg) for arg in node.args]
        if isinstance(callee, NEXFunction):
            if callee.body is None:
                return self._call_builtin(callee.name, args, node.line)
            return self._call_function(callee, args, node.line)
        raise RuntimeError(f'[RuntimeError] Line {node.line}: "{callee}" is not a function')

    def _call_function(self, func, args, line):
        if len(args) != len(func.params):
            raise RuntimeError(f'[RuntimeError] Line {line}: Function "{func.name}" expects {len(func.params)} arguments, got {len(args)}')
        env = Environment(func.closure)
        for param, arg in zip(func.params, args):
            env.define(param, arg)
        previous = self.environment
        self.environment = env
        try:
            result = NEXNull()
            for stmt in func.body:
                result = self.evaluate(stmt)
            return result
        except ReturnException as ret:
            return ret.value
        finally:
            self.environment = previous

    def _call_builtin(self, name, args, line):
        if name == "len":
            if len(args) != 1: raise RuntimeError(f'[RuntimeError] Line {line}: "len" expects 1 argument')
            if isinstance(args[0], NEXString): return NEXNumber(len(args[0].value))
            if isinstance(args[0], NEXList): return NEXNumber(len(args[0].elements))
            raise RuntimeError(f'[RuntimeError] Line {line}: "len" expects string or list')
        elif name == "type":
            if len(args) != 1: raise RuntimeError(f'[RuntimeError] Line {line}: "type" expects 1 argument')
            return NEXString(type(args[0]).__name__.replace("NEX", "").lower())
        elif name == "str":
            if len(args) != 1: raise RuntimeError(f'[RuntimeError] Line {line}: "str" expects 1 argument')
            return NEXString(self._to_string(args[0]))
        elif name == "num":
            if len(args) != 1: raise RuntimeError(f'[RuntimeError] Line {line}: "num" expects 1 argument')
            s = self._to_string(args[0])
            try:
                if "." in s: return NEXNumber(float(s))
                return NEXNumber(int(s))
            except ValueError:
                raise RuntimeError(f'[RuntimeError] Line {line}: Cannot convert "{s}" to number')
        elif name == "int":
            if len(args) != 1: raise RuntimeError(f'[RuntimeError] Line {line}: "int" expects 1 argument')
            s = self._to_string(args[0])
            try: return NEXNumber(int(float(s)))
            except ValueError: raise RuntimeError(f'[RuntimeError] Line {line}: Cannot convert "{s}" to int')
        elif name == "float":
            if len(args) != 1: raise RuntimeError(f'[RuntimeError] Line {line}: "float" expects 1 argument')
            s = self._to_string(args[0])
            try: return NEXNumber(float(s))
            except ValueError: raise RuntimeError(f'[RuntimeError] Line {line}: Cannot convert "{s}" to float')
        elif name == "range":
            if len(args) == 1: return NEXList([NEXNumber(i) for i in range(int(args[0].value))])
            elif len(args) == 2: return NEXList([NEXNumber(i) for i in range(int(args[0].value), int(args[1].value))])
            else: raise RuntimeError(f'[RuntimeError] Line {line}: "range" expects 1 or 2 arguments')
        elif name == "append":
            if len(args) != 2: raise RuntimeError(f'[RuntimeError] Line {line}: "append" expects 2 arguments')
            if not isinstance(args[0], NEXList): raise RuntimeError(f'[RuntimeError] Line {line}: "append" expects a list')
            args[0].elements.append(args[1])
            return args[0]
        elif name == "split":
            if len(args) not in (1, 2): raise RuntimeError(f'[RuntimeError] Line {line}: "split" expects 1 or 2 arguments')
            s = self._to_string(args[0])
            delim = self._to_string(args[1]) if len(args) == 2 else " "
            return NEXList([NEXString(p) for p in s.split(delim)])
        elif name == "join":
            if len(args) != 2: raise RuntimeError(f'[RuntimeError] Line {line}: "join" expects 2 arguments')
            if not isinstance(args[0], NEXList): raise RuntimeError(f'[RuntimeError] Line {line}: "join" expects a list')
            delim = self._to_string(args[1])
            return NEXString(delim.join(self._to_string(e) for e in args[0].elements))
        elif name == "upper":
            if len(args) != 1: raise RuntimeError(f'[RuntimeError] Line {line}: "upper" expects 1 argument')
            return NEXString(self._to_string(args[0]).upper())
        elif name == "lower":
            if len(args) != 1: raise RuntimeError(f'[RuntimeError] Line {line}: "lower" expects 1 argument')
            return NEXString(self._to_string(args[0]).lower())
        elif name == "contains":
            if len(args) != 2: raise RuntimeError(f'[RuntimeError] Line {line}: "contains" expects 2 arguments')
            if isinstance(args[0], NEXString): return NEXBoolean(self._to_string(args[1]) in args[0].value)
            if isinstance(args[0], NEXList): return NEXBoolean(any(self._equals(args[1], e) for e in args[0].elements))
            raise RuntimeError(f'[RuntimeError] Line {line}: "contains" expects string or list')
        elif name == "keys":
            if len(args) != 1: raise RuntimeError(f'[RuntimeError] Line {line}: "keys" expects 1 argument')
            if isinstance(args[0], dict): return NEXList([NEXString(k) for k in args[0].keys()])
            raise RuntimeError(f'[RuntimeError] Line {line}: "keys" expects a dict')
        elif name == "values":
            if len(args) != 1: raise RuntimeError(f'[RuntimeError] Line {line}: "values" expects 1 argument')
            if isinstance(args[0], dict): return NEXList(list(args[0].values()))
            raise RuntimeError(f'[RuntimeError] Line {line}: "values" expects a dict')
        return NEXNull()

    def visit_IndexExpr(self, node):
        obj = self.evaluate(node.obj)
        index = self.evaluate(node.index)
        if isinstance(obj, NEXList):
            if not isinstance(index, NEXNumber): raise RuntimeError(f"[RuntimeError] Line {node.line}: List index must be a number")
            idx = int(index.value)
            if idx < 0 or idx >= len(obj.elements): raise RuntimeError(f"[RuntimeError] Line {node.line}: Index {idx} out of bounds")
            return obj.elements[idx]
        if isinstance(obj, NEXString):
            if not isinstance(index, NEXNumber): raise RuntimeError(f"[RuntimeError] Line {node.line}: String index must be a number")
            idx = int(index.value)
            if idx < 0 or idx >= len(obj.value): raise RuntimeError(f"[RuntimeError] Line {node.line}: Index {idx} out of bounds")
            return NEXString(obj.value[idx])
        raise RuntimeError(f"[RuntimeError] Line {node.line}: Cannot index {type(obj).__name__}")

    def visit_AttributeExpr(self, node):
        obj = self.evaluate(node.obj)
        if isinstance(obj, NEXPythonModule):
            val = obj.get(node.attr)
            if val is None: raise RuntimeError(f'[RuntimeError] Line {node.line}: Module has no attribute "{node.attr}"')
            return self._wrap_python_value(val)
        if isinstance(obj, NEXString):
            if node.attr == "length": return NEXNumber(len(obj.value))
        if isinstance(obj, NEXList):
            if node.attr == "length": return NEXNumber(len(obj.elements))
        raise RuntimeError(f'[RuntimeError] Line {node.line}: "{type(obj).__name__}" has no attribute "{node.attr}"')

    def _wrap_python_value(self, val):
        if val is None: return NEXNull()
        if isinstance(val, bool): return NEXBoolean(val)
        if isinstance(val, (int, float)): return NEXNumber(val)
        if isinstance(val, str): return NEXString(val)
        if isinstance(val, list): return NEXList([self._wrap_python_value(v) for v in val])
        if callable(val): return NEXPythonCallable(val)
        return NEXPythonObject(val)

    def visit_OutputStmt(self, node):
        value = self.evaluate(node.expr)
        print(self._to_string(value))
        return value

    def visit_InputStmt(self, node):
        prompt_val = self.evaluate(node.prompt)
        prompt_str = self._to_string(prompt_val)
        try:
            user_input = input(prompt_str)
        except EOFError:
            user_input = ""
        try:
            if "." in user_input: return NEXNumber(float(user_input))
            return NEXNumber(int(user_input))
        except ValueError:
            return NEXString(user_input)

    def visit_ImportStmt(self, node):
        module_name = node.module
        if module_name.endswith(".nex") or module_name.endswith(".N"):
            filepath = module_name
        else:
            for ext in [".N", ".nex"]:
                if os.path.exists(module_name + ext):
                    filepath = module_name + ext
                    break
            else:
                filepath = module_name + ".N"
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            lexer = Lexer(source, filepath)
            tokens = lexer.scan()
            parser = Parser(tokens, filepath)
            ast = parser.parse()
            module_env = Environment(self.globals)
            previous = self.environment
            self.environment = module_env
            try:
                self.evaluate(ast)
            finally:
                self.environment = previous
            if node.alias:
                mod = NEXModule(module_env, node.names)
                self.globals.define(node.alias, mod)
            elif node.names:
                for name in node.names:
                    val = module_env.get(name)
                    if val is not None:
                        self.globals.define(name, val)
            else:
                for name, val in module_env.values.items():
                    self.globals.define(name, val)
            return NEXNull()
        try:
            py_module = importlib.import_module(module_name)
            nex_module = NEXPythonModule(py_module, node.names)
            if node.alias:
                self.globals.define(node.alias, nex_module)
            elif node.names:
                for name in node.names:
                    val = nex_module.get(name)
                    if val is not None:
                        self.globals.define(name, self._wrap_python_value(val))
            else:
                self.globals.define(module_name, nex_module)
            return NEXNull()
        except ImportError:
            raise RuntimeError(f'[ImportError] Line {node.line}: Cannot find module or file "{module_name}"')

    def visit_FunctionDef(self, node):
        func = NEXFunction(node.name, node.params, node.body, self.environment)
        self.environment.define(node.name, func)
        return func

    def visit_ReturnStmt(self, node):
        value = self.evaluate(node.value)
        raise ReturnException(value)

    def visit_IfStmt(self, node):
        if self._is_truthy(self.evaluate(node.condition)):
            return self._execute_block(node.then_body)
        for cond, body in node.elif_branches:
            if self._is_truthy(self.evaluate(cond)):
                return self._execute_block(body)
        if node.else_body:
            return self._execute_block(node.else_body)
        return NEXNull()

    def _execute_block(self, statements):
        result = NEXNull()
        for stmt in statements:
            result = self.evaluate(stmt)
        return result

    def visit_RepeatStmt(self, node):
        count_val = self.evaluate(node.count)
        if not isinstance(count_val, NEXNumber):
            raise RuntimeError(f"[RuntimeError] Line {node.line}: Repeat count must be a number")
        result = NEXNull()
        for _ in range(int(count_val.value)):
            for stmt in node.body:
                result = self.evaluate(stmt)
        return result

    def visit_ForEachStmt(self, node):
        iterable = self.evaluate(node.iterable)
        result = NEXNull()
        if isinstance(iterable, NEXList):
            items = iterable.elements
        elif isinstance(iterable, NEXString):
            items = [NEXString(c) for c in iterable.value]
        elif isinstance(iterable, NEXNumber):
            items = [NEXNumber(i) for i in range(int(iterable.value))]
        else:
            raise RuntimeError(f"[RuntimeError] Line {node.line}: Cannot iterate over {type(iterable).__name__}")
        for item in items:
            self.environment.define(node.var, item)
            for stmt in node.body:
                result = self.evaluate(stmt)
        return result

    def visit_FileBlockStmt(self, node):
        filename_val = self.evaluate(node.filename)
        content_val = self.evaluate(node.content)
        filename = self._to_string(filename_val)
        content = self._to_string(content_val)
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
        except IOError as e:
            raise RuntimeError(f'[RuntimeError] Line {node.line}: Cannot write to file "{filename}": {e}')
        return NEXNull()

    def _is_truthy(self, value):
        if isinstance(value, NEXBoolean): return value.value
        if isinstance(value, NEXNull): return False
        if isinstance(value, NEXNumber): return value.value != 0
        if isinstance(value, NEXString): return len(value.value) > 0
        if isinstance(value, NEXList): return len(value.elements) > 0
        return True

    def _to_string(self, value):
        if isinstance(value, NEXString): return value.value
        if isinstance(value, NEXNumber):
            if isinstance(value.value, int) or value.value == int(value.value):
                return str(int(value.value))
            return str(value.value)
        if isinstance(value, NEXBoolean): return "true" if value.value else "false"
        if isinstance(value, NEXNull): return "null"
        if isinstance(value, NEXList): return "[" + ", ".join(self._to_string(e) for e in value.elements) + "]"
        if isinstance(value, NEXFunction): return f"<fn {value.name}>"
        if isinstance(value, NEXPythonModule): return str(value)
        if isinstance(value, NEXPythonCallable): return "<python callable>"
        if isinstance(value, NEXPythonObject): return str(value.obj)
        if isinstance(value, NEXModule): return "<module>"
        return str(value)

    def _equals(self, a, b):
        if type(a) != type(b): return False
        if isinstance(a, NEXNumber): return a.value == b.value
        if isinstance(a, NEXString): return a.value == b.value
        if isinstance(a, NEXBoolean): return a.value == b.value
        if isinstance(a, NEXNull): return True
        if isinstance(a, NEXList):
            if len(a.elements) != len(b.elements): return False
            return all(self._equals(x, y) for x, y in zip(a.elements, b.elements))
        return a == b

# =============================================================================
# INTERPRETER
# =============================================================================

class Interpreter:
    def __init__(self):
        self.evaluator = Evaluator(self)

    def run(self, source, filename="<stdin>"):
        lexer = Lexer(source, filename)
        tokens = lexer.scan()
        parser = Parser(tokens, filename)
        ast = parser.parse()
        return self.evaluator.evaluate(ast)

    def run_repl(self):
        print("NEX Programming Language v1.0")
        print('Type "exit" or press Ctrl+D to quit.\n')
        while True:
            try:
                line = input("nex> ")
                if line.strip().lower() in ("exit", "quit"):
                    break
                if not line.strip():
                    continue
                self.run(line, "<repl>")
            except (LexerError, ParseError, RuntimeError) as e:
                print(str(e))
            except EOFError:
                print(); break
            except KeyboardInterrupt:
                print("\nInterrupted"); break
            except Exception as e:
                print(f"[InternalError] {type(e).__name__}: {e}")

# =============================================================================
# TEST SUITE
# =============================================================================

def run_tests():
    print("=" * 60)
    print("NEX INTERPRETER TEST SUITE")
    print("=" * 60)
    tests_passed = 0
    tests_failed = 0

    def test(name, code, expected_output=None, should_error=False):
        nonlocal tests_passed, tests_failed
        print(f"\n[Test] {name}")
        display_code = code.replace("\n", " ")[:60]
        print(f"  Code: {display_code}{'...' if len(code) > 60 else ''}")
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            interpreter = Interpreter()
            interpreter.run(code, "<test>")
            output = sys.stdout.getvalue().strip()
            sys.stdout = old_stdout
            if should_error:
                print(f"  FAILED - Expected error but got output: {output}")
                tests_failed += 1; return
            if expected_output is not None and output != expected_output:
                print(f'  FAILED - Expected: "{expected_output}", Got: "{output}"')
                tests_failed += 1; return
            print(f'  PASSED - Output: "{output}"')
            tests_passed += 1
        except Exception as e:
            sys.stdout = old_stdout
            if should_error:
                print(f"  PASSED - Got expected error: {e}")
                tests_passed += 1
            else:
                print(f"  FAILED - Unexpected error: {e}")
                tests_failed += 1

    test("Basic Output", '[>= "Hello, NEX!"]', "Hello, NEX!")
    test("Variables & Arithmetic", "x = 10\ny = 20\n[>= x + y]", "30")
    test("String Concatenation", 'score = 100\n[>= "Score: " + score]', "Score: 100")
    test("If Statement", "x = 5\n? x > 3\n[>= \"yes\"]\nend", "yes")
    test("If-Else", "x = 2\n? x > 3\n[>= \"yes\"]\n:\n[>= \"no\"]\nend", "no")
    test("If-Elif-Else", "x = 2\n? x > 3\n[>= \"A\"]\n:? x == 2\n[>= \"B\"]\n:\n[>= \"C\"]\nend", "B")
    test("Repeat Loop", "@ 3\n[>= \"loop\"]\nend", "loop\nloop\nloop")
    test("For Each Loop", "items = [1, 2, 3]\n@ i in items\n[>= i]\nend", "1\n2\n3")
    test("Function Definition & Call", 'fn greet(name)\n[>= "Hello, " + name]\nend\ngreet("NEX")', "Hello, NEX")
    test("Function Return", "fn add(a, b)\n-> a + b\nend\n[>= add(5, 3)]", "8")
    test("Division by Zero", "x = 10 / 0", should_error=True)
    test("Undefined Variable", "[>= undefined_var]", should_error=True)
    test("Boolean Logic", "x = true\ny = false\n[>= x and not y]", "true")
    test("Comparisons", "x = 5\n[>= x == 5]\n[>= x != 5]\n[>= x < 10]\n[>= x >= 5]", "true\nfalse\ntrue\ntrue")
    test("Lists", "nums = [1, 2, 3]\n[>= nums[0]]\n[>= nums[1] + nums[2]]", "1\n5")
    test("Built-in len", 'name = "NEX"\n[>= len(name)]', "3")
    test("Built-in type", "x = 42\n[>= type(x)]", "number")
    test("Truthiness - 0 is falsy", "? 0\n[>= \"truthy\"]\n:\n[>= \"falsy\"]\nend", "falsy")
    test("Truthiness - empty string is falsy", '? ""\n[>= "truthy"]\n:\n[>= "falsy"]\nend', "falsy")
    test("String Upper", 'name = "nex"\n[>= upper(name)]', "NEX")
    test("String Lower", 'name = "NEX"\n[>= lower(name)]', "nex")
    test("Range", "nums = range(5)\n[>= len(nums)]", "5")
    test("Append", "items = [1, 2]\nappend(items, 3)\n[>= len(items)]", "3")
    test("Split & Join", 'words = split("hello world")\n[>= join(words, "-")]', "hello-world")
    test("Contains - String", '[>= contains("hello", "ell")]', "true")
    test("Contains - List", "nums = [1, 2, 3]\n[>= contains(nums, 2)]", "true")
    test("Nested Functions", "fn outer()\nfn inner()\n-> 42\nend\n-> inner()\nend\n[>= outer()]", "42")
    test("Modulo", "[>= 10 % 3]", "1")
    test("Null", "x = null\n[>= x]", "null")
    test("String Index", 'name = "NEX"\n[>= name[0]]', "N")
    test("List Concatenation", "a = [1, 2]\nb = [3, 4]\nc = a + b\n[>= len(c)]", "4")
    test("Auto Coercion in Concat", 'x = 42\n[>= "Value: " + x]', "Value: 42")
    test("Float Arithmetic", "x = 3.5\ny = 1.5\n[>= x + y]", "5")
    test("Negative Numbers", "x = -5\n[>= x + 10]", "5")
    test("Not Operator", "x = false\n[>= not x]", "true")
    test("Or Operator", "x = false\ny = true\n[>= x or y]", "true")
    test("Complex Expression", "x = 5\ny = 10\n[>= (x + y) * 2 - 5]", "25")
    test("String Length Property", 'name = "hello"\n[>= name.length]', "5")
    test("List Length Property", "nums = [1, 2, 3, 4]\n[>= nums.length]", "4")

    print("\n" + "=" * 60)
    print(f"RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)
    return tests_failed == 0

# =============================================================================
# MAIN CLI
# =============================================================================

def install_nex():
    """Install NEX language support: pip package + VS Code extension"""
    print("=" * 50)
    print("   NEX Language Installer")
    print("=" * 50)
    script_dir = Path(__file__).parent.resolve()
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", str(script_dir)])
        print("[OK] Python package installed/updated")
    except subprocess.CalledProcessError as e:
        print(f"[WARN] pip install failed: {e}")
    vscode_ext_src = script_dir / "vscode-extension"
    if not vscode_ext_src.exists():
        print(f"[SKIP] VS Code extension not found at {vscode_ext_src}")
        return
    system = platform.system()
    if system == "Windows":
        vscode_ext_dir = Path.home() / ".vscode" / "extensions" / "nex-lang"
    else:
        vscode_ext_dir = Path.home() / ".vscode" / "extensions" / "nex-lang"
    try:
        if vscode_ext_dir.exists():
            shutil.rmtree(vscode_ext_dir)
        shutil.copytree(vscode_ext_src, vscode_ext_dir)
        print(f"[OK] VS Code Extension installed to: {vscode_ext_dir}")
        print("   Please restart VS Code to activate .N syntax highlighting")
    except Exception as e:
        print(f"[WARN] VS Code extension install failed: {e}")
    if system == "Windows":
        try:
            import winreg
            nex_exe = shutil.which("nex") or sys.executable
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.N") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "NEXSourceFile")
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\NEXSourceFile") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "NEX Source File")
                with winreg.CreateKey(key, r"shell\open\command") as cmd_key:
                    winreg.SetValue(cmd_key, "", winreg.REG_SZ, f'"{nex_exe}" "%1"')
            print("[OK] Registered .N file association on Windows")
        except Exception as e:
            print(f"[INFO] Could not register file association: {e}")
    print("=" * 50)
    print("Installation complete! Try:")
    print("  nex hello.N")
    print("  nex --test")
    print("=" * 50)

def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ("install", "--install"):
            install_nex()
            return
        if arg in ("--test", "-t"):
            success = run_tests()
            sys.exit(0 if success else 1)
        elif arg in ("--help", "-h"):
            print("""
NEX Programming Language Interpreter v1.0
Usage:
  python interpreter.py <file.nex>    Run a NEX script file
  python interpreter.py               Start REPL mode
  python interpreter.py --test        Run test suite
  python interpreter.py --help        Show this help message

NEX Language Quick Reference:
  nex install        Install NEX + VS Code extension + .N file association
  [>= expr]          Print/output expression
  var = [<= "prompt"]  Read user input
  => module          Import module (NEX or Python)
  => module (a, b)   Import specific names
  => module as alias Import with alias
  fn name(p1, p2)    Define function
  -> expr            Return from function
  ? condition        If statement
  :? condition       Else if
  :                  Else
  @ N                Repeat N times
  @ item in list     For each loop
  <เปิด "file">> "content" end:  Write file
  -- comment         Single line comment
""")
            return
        else:
            filename = arg
            if not os.path.exists(filename):
                found = False
                for ext in [".N", ".nex"]:
                    if os.path.exists(filename + ext):
                        filename = filename + ext
                        found = True
                        break
                if not found:
                    print(f"[Error] File not found: {arg}")
                    sys.exit(1)
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    source = f.read()
                interpreter = Interpreter()
                interpreter.run(source, filename)
            except (LexerError, ParseError, RuntimeError) as e:
                print(str(e))
                sys.exit(1)
            except Exception as e:
                print(f"[InternalError] {type(e).__name__}: {e}")
                sys.exit(1)
    else:
        interpreter = Interpreter()
        interpreter.run_repl()

if __name__ == "__main__":
    main()
