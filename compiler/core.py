import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

class TokenType:
    """Token类型定义"""
    INT = 'INT'
    FLOAT = 'FLOAT'
    CHAR = 'CHAR'
    STRING = 'STRING'
    BOOL = 'BOOL'
    VOID = 'VOID'
    STRUCT = 'STRUCT'
    UNION = 'UNION'
    ENUM = 'ENUM'
    IF = 'IF'
    ELSE = 'ELSE'
    WHILE = 'WHILE'
    FOR = 'FOR'
    RETURN = 'RETURN'
    BREAK = 'BREAK'
    CONTINUE = 'CONTINUE'
    TRUE = 'TRUE'
    FALSE = 'FALSE'
    IDENTIFIER = 'IDENTIFIER'
    INTEGER_LITERAL = 'INTEGER_LITERAL'
    FLOAT_LITERAL = 'FLOAT_LITERAL'
    CHAR_LITERAL = 'CHAR_LITERAL'
    STRING_LITERAL = 'STRING_LITERAL'
    PLUS = 'PLUS'
    MINUS = 'MINUS'
    MULTIPLY = 'MULTIPLY'
    DIVIDE = 'DIVIDE'
    MODULO = 'MODULO'
    ASSIGN = 'ASSIGN'
    PLUS_ASSIGN = 'PLUS_ASSIGN'
    MINUS_ASSIGN = 'MINUS_ASSIGN'
    MULTIPLY_ASSIGN = 'MULTIPLY_ASSIGN'
    DIVIDE_ASSIGN = 'DIVIDE_ASSIGN'
    EQUAL = 'EQUAL'
    NOT_EQUAL = 'NOT_EQUAL'
    LESS_THAN = 'LESS_THAN'
    GREATER_THAN = 'GREATER_THAN'
    LESS_EQUAL = 'LESS_EQUAL'
    GREATER_EQUAL = 'GREATER_EQUAL'
    AND = 'AND'
    OR = 'OR'
    NOT = 'NOT'
    BIT_AND = 'BIT_AND'
    BIT_OR = 'BIT_OR'
    BIT_XOR = 'BIT_XOR'
    BIT_NOT = 'BIT_NOT'
    LEFT_SHIFT = 'LEFT_SHIFT'
    RIGHT_SHIFT = 'RIGHT_SHIFT'
    LEFT_PAREN = 'LEFT_PAREN'
    RIGHT_PAREN = 'RIGHT_PAREN'
    LEFT_BRACE = 'LEFT_BRACE'
    RIGHT_BRACE = 'RIGHT_BRACE'
    LEFT_BRACKET = 'LEFT_BRACKET'
    RIGHT_BRACKET = 'RIGHT_BRACKET'
    SEMICOLON = 'SEMICOLON'
    COMMA = 'COMMA'
    DOT = 'DOT'
    EOF = 'EOF'
    ERROR = 'ERROR'

@dataclass
class Token:
    """Token数据结构"""
    type: str
    value: str
    line: int
    column: int
    length: int = 0
    
    def to_dict(self):
        return {
            'type': self.type,
            'value': self.value,
            'line': self.line,
            'column': self.column,
            'length': self.length
        }

class LexerError(Exception):
    """词法分析错误"""
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"词法错误 (行 {line}, 列 {column}): {message}")

class SyntaxError(Exception):
    """语法分析错误"""
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"语法错误 (行 {line}, 列 {column}): {message}")

class SemanticError(Exception):
    """语义分析错误"""
    def __init__(self, message, line=None, column=None):
        self.message = message
        self.line = line
        self.column = column
        loc = f" (行 {line}, 列 {column})" if line else ""
        super().__init__(f"语义错误{loc}: {message}")

@dataclass
class ASTNode:
    """AST节点"""
    type: str
    children: List['ASTNode'] = field(default_factory=list)
    value: Any = None
    line: int = 0
    column: int = 0
    
    def to_dict(self):
        result = {
            'type': self.type,
            'line': self.line,
            'column': self.column
        }
        if self.value is not None:
            result['value'] = self.value
        if self.children:
            result['children'] = [child.to_dict() if isinstance(child, ASTNode) else child for child in self.children]
        return result
