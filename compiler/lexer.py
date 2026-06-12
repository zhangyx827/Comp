import re
from typing import List, Dict, Any
from .core import TokenType, Token, LexerError

class EnhancedLexer:
    """增强版词法分析器"""
    
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.pos = 0
        self.line = 1
        self.column = 1
        self.errors = []
        self.warnings = []
        
        self.keywords = {
            'int': TokenType.INT, 'float': TokenType.FLOAT, 'char': TokenType.CHAR,
            'string': TokenType.STRING, 'bool': TokenType.BOOL, 'void': TokenType.VOID,
            'struct': TokenType.STRUCT, 'union': TokenType.UNION, 'enum': TokenType.ENUM,
            'if': TokenType.IF, 'else': TokenType.ELSE, 'while': TokenType.WHILE,
            'for': TokenType.FOR, 'return': TokenType.RETURN, 'break': TokenType.BREAK,
            'continue': TokenType.CONTINUE, 'true': TokenType.TRUE, 'false': TokenType.FALSE
        }
        
        self.token_spec = [
            ('SKIP', r'\s+'),
            ('COMMENT', r'//.*'),
            ('MULTILINE_COMMENT', r'/\*[\s\S]*?\*/'),
            ('FLOAT_LITERAL', r'\d+\.\d+'),
            ('INTEGER_LITERAL', r'\d+'),
            ('STRING_LITERAL', r'"([^"\\]|\\.)*"'),
            ('CHAR_LITERAL', r"'([^'\\]|\\.)'"),
            ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
            ('LEFT_SHIFT', r'<<'),
            ('RIGHT_SHIFT', r'>>'),
            ('PLUS_ASSIGN', r'\+='),
            ('MINUS_ASSIGN', r'-='),
            ('MULTIPLY_ASSIGN', r'\*='),
            ('DIVIDE_ASSIGN', r'/='),
            ('EQUAL', r'=='),
            ('NOT_EQUAL', r'!='),
            ('LESS_EQUAL', r'<='),
            ('GREATER_EQUAL', r'>='),
            ('ASSIGN', r'='),
            ('AND', r'&&'),
            ('OR', r'\|\|'),
            ('NOT', r'!'),
            ('BIT_AND', r'&'),
            ('BIT_OR', r'\|'),
            ('BIT_XOR', r'\^'),
            ('BIT_NOT', r'~'),
            ('PLUS', r'\+'),
            ('MINUS', r'-'),
            ('MULTIPLY', r'\*'),
            ('DIVIDE', r'/'),
            ('MODULO', r'%'),
            ('LESS_THAN', r'<'),
            ('GREATER_THAN', r'>'),
            ('LEFT_PAREN', r'\('),
            ('RIGHT_PAREN', r'\)'),
            ('LEFT_BRACE', r'\{'),
            ('RIGHT_BRACE', r'\}'),
            ('LEFT_BRACKET', r'\['),
            ('RIGHT_BRACKET', r'\]'),
            ('SEMICOLON', r';'),
            ('COMMA', r','),
            ('DOT', r'\.'),
        ]
        
        self.token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.token_spec)
    
    def get_position(self):
        return self.line, self.column
    
    def tokenize(self) -> List[Token]:
        """执行词法分析"""
        tokens = []
        
        for match in re.finditer(self.token_regex, self.source_code):
            kind = match.lastgroup
            value = match.group()
            
            line_start = self.source_code.count('\n', 0, match.start()) + 1
            col_start = match.start() - self.source_code.rfind('\n', 0, match.start())
            
            if kind == 'SKIP':
                continue
            elif kind in ('COMMENT', 'MULTILINE_COMMENT'):
                continue
            elif kind == 'IDENTIFIER':
                token_type = self.keywords.get(value, TokenType.IDENTIFIER)
            else:
                token_type = getattr(TokenType, kind, TokenType.ERROR)
            
            token = Token(token_type, value, line_start, col_start, len(value))
            tokens.append(token)
        
        tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return tokens
    
    def analyze(self) -> Dict[str, Any]:
        """执行词法分析并返回详细结果"""
        tokens = self.tokenize()
        
        # 按类型分组tokens
        tokens_by_type = {}
        for token in tokens:
            if token.type != TokenType.EOF:
                if token.type not in tokens_by_type:
                    tokens_by_type[token.type] = []
                tokens_by_type[token.type].append(token.to_dict())
        
        return {
            'success': True,
            'total_tokens': len(tokens) - 1,
            'tokens': [t.to_dict() for t in tokens if t.type != TokenType.EOF],
            'tokens_by_type': tokens_by_type,
            'errors': self.errors,
            'warnings': self.warnings
        }
