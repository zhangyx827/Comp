from typing import List, Dict, Any
from .core import TokenType, Token, ASTNode, SyntaxError

class EnhancedParser:
    """增强版语法分析器"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = tokens[0] if tokens else None
        self.errors = []
        self.warnings = []
        self.type_specifiers = {
            TokenType.INT, TokenType.FLOAT, TokenType.CHAR, TokenType.STRING,
            TokenType.BOOL, TokenType.VOID, TokenType.STRUCT, TokenType.UNION,
            TokenType.ENUM
        }
    
    def peek(self, offset=1):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None
    
    def eat(self, token_type: str) -> Token:
        if self.current_token and self.current_token.type == token_type:
            token = self.current_token
            self.pos += 1
            if self.pos < len(self.tokens):
                self.current_token = self.tokens[self.pos]
            return token
        else:
            expected = token_type
            got = self.current_token.type if self.current_token else 'EOF'
            line = self.current_token.line if self.current_token else 0
            col = self.current_token.column if self.current_token else 0
            raise SyntaxError(f"期望 {expected}, 得到 {got}", line, col)
    
    def parse(self) -> ASTNode:
        """解析程序"""
        children = []
        while self.current_token.type != TokenType.EOF:
            try:
                children.append(self.declaration())
            except SyntaxError as e:
                self.errors.append({'message': e.message, 'line': e.line, 'column': e.column})
                # 尝试恢复解析
                while self.current_token.type not in [TokenType.EOF, TokenType.SEMICOLON] and self.current_token.type not in self.type_specifiers:
                    self.pos += 1
                    if self.pos < len(self.tokens):
                        self.current_token = self.tokens[self.pos]
                if self.current_token.type == TokenType.SEMICOLON:
                    self.eat(TokenType.SEMICOLON)
                if self.current_token.type == TokenType.EOF:
                    break
        
        return ASTNode('program', children, line=1, column=1)
    
    def declaration(self) -> ASTNode:
        if self.current_token.type in self.type_specifiers:
            if self._is_type_definition_start():
                return self.composite_type_definition()
            declarator_index = self._declarator_start_index()
            if declarator_index is not None:
                if self._token_at(declarator_index).type == TokenType.IDENTIFIER and self._token_at(declarator_index + 1) and self._token_at(declarator_index + 1).type == TokenType.LEFT_PAREN:
                    return self.function_declaration()
            return self.statement()
        return self.statement()

    def _token_at(self, index):
        return self.tokens[index] if index < len(self.tokens) else None

    def _is_type_definition_start(self) -> bool:
        if self.current_token.type not in [TokenType.STRUCT, TokenType.UNION, TokenType.ENUM]:
            return False
        if self.peek() and self.peek().type == TokenType.LEFT_BRACE:
            return True
        return self.peek() and self.peek().type == TokenType.IDENTIFIER and self.peek(2) and self.peek(2).type == TokenType.LEFT_BRACE

    def _declarator_start_index(self):
        index = self.pos
        if self._token_at(index).type in [TokenType.STRUCT, TokenType.UNION, TokenType.ENUM]:
            index += 1
            if self._token_at(index) and self._token_at(index).type == TokenType.IDENTIFIER:
                index += 1
            else:
                return None
        elif self._token_at(index).type in self.type_specifiers:
            index += 1
        else:
            return None
        while self._token_at(index) and self._token_at(index).type == TokenType.MULTIPLY:
            index += 1
        return index

    def parse_type_specifier(self) -> Dict[str, Any]:
        line, col = self.current_token.line, self.current_token.column
        if self.current_token.type in [TokenType.STRUCT, TokenType.UNION, TokenType.ENUM]:
            kind = self.eat(self.current_token.type).value
            name = None
            if self.current_token.type == TokenType.IDENTIFIER:
                name = self.eat(TokenType.IDENTIFIER).value
            return {'kind': kind, 'name': name, 'text': f"{kind} {name}" if name else kind, 'line': line, 'column': col}
        if self.current_token.type in self.type_specifiers:
            text = self.current_token.value
            self.eat(self.current_token.type)
            return {'kind': 'primitive', 'name': text, 'text': text, 'line': line, 'column': col}
        raise SyntaxError(f"期望类型说明符, 得到 {self.current_token.type}", line, col)

    def type_to_text(self, type_spec: Dict[str, Any]) -> str:
        return type_spec['text']

    def composite_type_definition(self) -> ASTNode:
        line, col = self.current_token.line, self.current_token.column
        kind = self.eat(self.current_token.type).value
        name = None
        if self.current_token.type == TokenType.IDENTIFIER:
            name = self.eat(TokenType.IDENTIFIER).value
        self.eat(TokenType.LEFT_BRACE)
        if kind == 'enum':
            members = self.enum_member_list()
        else:
            members = self.field_declaration_list()
        self.eat(TokenType.RIGHT_BRACE)
        self.eat(TokenType.SEMICOLON)
        return ASTNode(f'{kind}_definition', [], {'name': name, 'members': members}, line, col)

    def field_declaration_list(self) -> List[Dict]:
        fields = []
        while self.current_token.type != TokenType.RIGHT_BRACE:
            type_spec = self.parse_type_specifier()
            while True:
                is_pointer = False
                while self.current_token.type == TokenType.MULTIPLY:
                    self.eat(TokenType.MULTIPLY)
                    is_pointer = True
                name = self.eat(TokenType.IDENTIFIER).value
                array_size = None
                if self.current_token.type == TokenType.LEFT_BRACKET:
                    self.eat(TokenType.LEFT_BRACKET)
                    if self.current_token.type == TokenType.INTEGER_LITERAL:
                        array_size = self.parse_integer_literal(self.current_token.value)
                        self.eat(TokenType.INTEGER_LITERAL)
                    self.eat(TokenType.RIGHT_BRACKET)
                field = {'name': name, 'type': self.type_to_text(type_spec)}
                if is_pointer:
                    field['is_pointer'] = True
                if array_size is not None:
                    field['array_size'] = array_size
                fields.append(field)
                if self.current_token.type != TokenType.COMMA:
                    break
                self.eat(TokenType.COMMA)
            self.eat(TokenType.SEMICOLON)
        return fields

    def enum_member_list(self) -> List[Dict]:
        members = []
        next_value = 0
        while self.current_token.type != TokenType.RIGHT_BRACE:
            name = self.eat(TokenType.IDENTIFIER).value
            value = next_value
            if self.current_token.type == TokenType.ASSIGN:
                self.eat(TokenType.ASSIGN)
                sign = 1
                if self.current_token.type == TokenType.MINUS:
                    self.eat(TokenType.MINUS)
                    sign = -1
                value = sign * self.parse_integer_literal(self.eat(TokenType.INTEGER_LITERAL).value)
            members.append({'name': name, 'value': value})
            next_value = value + 1
            if self.current_token.type != TokenType.COMMA:
                break
            self.eat(TokenType.COMMA)
            if self.current_token.type == TokenType.RIGHT_BRACE:
                break
        return members
    
    def function_declaration(self) -> ASTNode:
        type_spec = self.parse_type_specifier()
        return_type = self.type_to_text(type_spec)
        line, col = type_spec['line'], type_spec['column']
        func_name = self.eat(TokenType.IDENTIFIER).value
        self.eat(TokenType.LEFT_PAREN)
        
        params = []
        if self.current_token.type != TokenType.RIGHT_PAREN:
            params = self.parameter_list()
        self.eat(TokenType.RIGHT_PAREN)
        
        body = self.block()
        return ASTNode('function_declaration', [body], 
                      {'name': func_name, 'return_type': return_type, 'params': params},
                      line, col)
    
    def parameter_list(self) -> List[Dict]:
        params = []
        params.append(self.parameter())
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            params.append(self.parameter())
        return params
    
    def parameter(self) -> Dict:
        type_spec = self.parse_type_specifier()
        param_type = self.type_to_text(type_spec)
        line, col = type_spec['line'], type_spec['column']
        
        # 检查是否是指针参数
        is_pointer = False
        if self.current_token.type == TokenType.MULTIPLY:
            self.eat(TokenType.MULTIPLY)
            is_pointer = True
        
        param_name = self.eat(TokenType.IDENTIFIER).value
        
        # 检查是否是数组参数（虽然C中数组会退化为指针，但支持这种语法）
        array_size = None
        if self.current_token.type == TokenType.LEFT_BRACKET:
            self.eat(TokenType.LEFT_BRACKET)
            if self.current_token.type == TokenType.INTEGER_LITERAL:
                array_size = self.parse_integer_literal(self.current_token.value)
                self.eat(TokenType.INTEGER_LITERAL)
            self.eat(TokenType.RIGHT_BRACKET)
        
        result = {'type': param_type, 'name': param_name, 'line': line, 'column': col}
        if is_pointer:
            result['is_pointer'] = True
        if array_size is not None:
            result['array_size'] = array_size
        return result
    
    def block(self) -> ASTNode:
        line, col = self.current_token.line, self.current_token.column
        self.eat(TokenType.LEFT_BRACE)
        statements = []
        while self.current_token.type != TokenType.RIGHT_BRACE:
            statements.append(self.statement())
        self.eat(TokenType.RIGHT_BRACE)
        return ASTNode('block', statements, line=line, column=col)
    
    def statement(self) -> ASTNode:
        line, col = self.current_token.line, self.current_token.column
        
        if self.current_token.type == TokenType.IF:
            return self.if_statement()
        elif self.current_token.type == TokenType.WHILE:
            return self.while_statement()
        elif self.current_token.type == TokenType.FOR:
            return self.for_statement()
        elif self.current_token.type == TokenType.RETURN:
            return self.return_statement()
        elif self.current_token.type == TokenType.BREAK:
            return self.break_statement()
        elif self.current_token.type == TokenType.CONTINUE:
            return self.continue_statement()
        elif self.current_token.type == TokenType.LEFT_BRACE:
            return self.block()
        elif self.current_token.type in self.type_specifiers and self.current_token.type != TokenType.VOID:
            return self.variable_declaration()
        else:
            return self.expression_statement()
    
    def if_statement(self) -> ASTNode:
        line, col = self.current_token.line, self.current_token.column
        self.eat(TokenType.IF)
        self.eat(TokenType.LEFT_PAREN)
        condition = self.expression()
        self.eat(TokenType.RIGHT_PAREN)
        
        if self.current_token.type == TokenType.LEFT_BRACE:
            then_block = self.block()
        else:
            then_block = self.statement()
        
        else_block = None
        if self.current_token.type == TokenType.ELSE:
            self.eat(TokenType.ELSE)
            if self.current_token.type == TokenType.LEFT_BRACE:
                else_block = self.block()
            else:
                else_block = self.statement()
        
        children = [condition, then_block]
        if else_block:
            children.append(else_block)
        return ASTNode('if_statement', children, line=line, column=col)
    
    def while_statement(self) -> ASTNode:
        line, col = self.current_token.line, self.current_token.column
        self.eat(TokenType.WHILE)
        self.eat(TokenType.LEFT_PAREN)
        condition = self.expression()
        self.eat(TokenType.RIGHT_PAREN)
        body = self.block()
        return ASTNode('while_statement', [condition, body], line=line, column=col)
    
    def for_statement(self) -> ASTNode:
        line, col = self.current_token.line, self.current_token.column
        self.eat(TokenType.FOR)
        self.eat(TokenType.LEFT_PAREN)
        
        init = None
        init_was_declaration = False
        if self.current_token.type != TokenType.SEMICOLON:
            if self.current_token.type in self.type_specifiers and self.current_token.type != TokenType.VOID:
                init = self.variable_declaration()
                init_was_declaration = True
            else:
                init = self.expression()
        
        # variable_declaration 已经消费了分号，expression 没有
        if not init_was_declaration:
            self.eat(TokenType.SEMICOLON)
        
        condition = None
        if self.current_token.type != TokenType.SEMICOLON:
            condition = self.expression()
        self.eat(TokenType.SEMICOLON)
        
        increment = None
        if self.current_token.type != TokenType.RIGHT_PAREN:
            increment = self.expression()
        
        self.eat(TokenType.RIGHT_PAREN)
        body = self.block()
        
        children = []
        value = {'has_init': init is not None, 'has_condition': condition is not None, 'has_increment': increment is not None}
        if init:
            children.append(init)
        if condition:
            children.append(condition)
        if increment:
            children.append(increment)
        children.append(body)
        
        return ASTNode('for_statement', children, value, line, col)
    
    def return_statement(self) -> ASTNode:
        line, col = self.current_token.line, self.current_token.column
        self.eat(TokenType.RETURN)
        expr = None
        if self.current_token.type != TokenType.SEMICOLON:
            expr = self.expression()
        self.eat(TokenType.SEMICOLON)
        return ASTNode('return_statement', [expr] if expr else [], line=line, column=col)
    
    def break_statement(self) -> ASTNode:
        line, col = self.current_token.line, self.current_token.column
        self.eat(TokenType.BREAK)
        self.eat(TokenType.SEMICOLON)
        return ASTNode('break_statement', line=line, column=col)
    
    def continue_statement(self) -> ASTNode:
        line, col = self.current_token.line, self.current_token.column
        self.eat(TokenType.CONTINUE)
        self.eat(TokenType.SEMICOLON)
        return ASTNode('continue_statement', line=line, column=col)
    
    def variable_declaration(self) -> ASTNode:
        type_spec = self.parse_type_specifier()
        var_type = self.type_to_text(type_spec)
        line, col = type_spec['line'], type_spec['column']
        
        declarations = []
        
        first = True
        while True:
            if not first:
                self.eat(TokenType.COMMA)
            first = False
            
            is_pointer = False
            if self.current_token.type == TokenType.MULTIPLY:
                self.eat(TokenType.MULTIPLY)
                is_pointer = True
            
            var_name = self.eat(TokenType.IDENTIFIER).value
            
            array_size = None
            if self.current_token.type == TokenType.LEFT_BRACKET:
                self.eat(TokenType.LEFT_BRACKET)
                if self.current_token.type == TokenType.INTEGER_LITERAL:
                    array_size = self.parse_integer_literal(self.current_token.value)
                    self.eat(TokenType.INTEGER_LITERAL)
                self.eat(TokenType.RIGHT_BRACKET)
            
            init = None
            if self.current_token.type == TokenType.ASSIGN:
                self.eat(TokenType.ASSIGN)
                init = self.expression()
            
            children = [init] if init else []
            value = {'name': var_name, 'type': var_type}
            if array_size is not None:
                value['array_size'] = array_size
            if is_pointer:
                value['is_pointer'] = True
            
            declarations.append(ASTNode('variable_declaration', children, value, line, col))
            
            if self.current_token.type != TokenType.COMMA:
                break
        
        self.eat(TokenType.SEMICOLON)
        
        if len(declarations) == 1:
            return declarations[0]
        
        return ASTNode('variable_declarations', declarations, line=line, column=col)
    
    def expression_statement(self) -> ASTNode:
        line, col = self.current_token.line, self.current_token.column
        expr = self.expression()
        self.eat(TokenType.SEMICOLON)
        return ASTNode('expression_statement', [expr], line=line, column=col)
    
    def expression(self) -> ASTNode:
        return self.assignment_expression()
    
    def assignment_expression(self) -> ASTNode:
        left = self.logical_or_expression()
        if self.current_token.type == TokenType.ASSIGN:
            line, col = self.current_token.line, self.current_token.column
            self.eat(TokenType.ASSIGN)
            right = self.assignment_expression()
            return ASTNode('assignment_expression', [left, right], {'operator': '='}, line, col)
        return left
    
    def logical_or_expression(self) -> ASTNode:
        left = self.logical_and_expression()
        while self.current_token.type == TokenType.OR:
            line, col = self.current_token.line, self.current_token.column
            self.eat(TokenType.OR)
            right = self.logical_and_expression()
            left = ASTNode('binary_expression', [left, right], {'operator': '||'}, line, col)
        return left
    
    def logical_and_expression(self) -> ASTNode:
        left = self.equality_expression()
        while self.current_token.type == TokenType.AND:
            line, col = self.current_token.line, self.current_token.column
            self.eat(TokenType.AND)
            right = self.equality_expression()
            left = ASTNode('binary_expression', [left, right], {'operator': '&&'}, line, col)
        return left
    
    def equality_expression(self) -> ASTNode:
        left = self.relational_expression()
        while self.current_token.type in [TokenType.EQUAL, TokenType.NOT_EQUAL]:
            line, col = self.current_token.line, self.current_token.column
            op = self.eat(self.current_token.type).value
            right = self.relational_expression()
            left = ASTNode('binary_expression', [left, right], {'operator': op}, line, col)
        return left
    
    def relational_expression(self) -> ASTNode:
        left = self.shift_expression()
        while self.current_token.type in [TokenType.LESS_THAN, TokenType.GREATER_THAN, 
                                          TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL]:
            line, col = self.current_token.line, self.current_token.column
            op = self.eat(self.current_token.type).value
            right = self.shift_expression()
            left = ASTNode('binary_expression', [left, right], {'operator': op}, line, col)
        return left
    
    def shift_expression(self) -> ASTNode:
        left = self.additive_expression()
        while self.current_token.type in [TokenType.LEFT_SHIFT, TokenType.RIGHT_SHIFT]:
            line, col = self.current_token.line, self.current_token.column
            op = self.eat(self.current_token.type).value
            right = self.additive_expression()
            left = ASTNode('binary_expression', [left, right], {'operator': op}, line, col)
        return left
    
    def additive_expression(self) -> ASTNode:
        left = self.multiplicative_expression()
        while self.current_token.type in [TokenType.PLUS, TokenType.MINUS]:
            line, col = self.current_token.line, self.current_token.column
            op = self.eat(self.current_token.type).value
            right = self.multiplicative_expression()
            left = ASTNode('binary_expression', [left, right], {'operator': op}, line, col)
        return left
    
    def multiplicative_expression(self) -> ASTNode:
        left = self.unary_expression()
        while self.current_token.type in [TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO]:
            line, col = self.current_token.line, self.current_token.column
            op = self.eat(self.current_token.type).value
            right = self.unary_expression()
            left = ASTNode('binary_expression', [left, right], {'operator': op}, line, col)
        return left
    
    def unary_expression(self) -> ASTNode:
        if self.current_token.type in [TokenType.PLUS, TokenType.MINUS, TokenType.NOT, TokenType.BIT_NOT]:
            line, col = self.current_token.line, self.current_token.column
            op = self.eat(self.current_token.type).value
            operand = self.unary_expression()
            return ASTNode('unary_expression', [operand], {'operator': op}, line, col)
        # 取地址操作符 &
        elif self.current_token.type == TokenType.BIT_AND:
            line, col = self.current_token.line, self.current_token.column
            self.eat(TokenType.BIT_AND)
            operand = self.unary_expression()
            return ASTNode('address_of', [operand], line=line, column=col)
        # 解引用操作符 *
        elif self.current_token.type == TokenType.MULTIPLY:
            line, col = self.current_token.line, self.current_token.column
            self.eat(TokenType.MULTIPLY)
            operand = self.unary_expression()
            return ASTNode('unary_expression', [operand], {'operator': '*'}, line, col)
        return self.postfix_expression()
    
    def postfix_expression(self) -> ASTNode:
        left = self.primary_expression()
        
        if self.current_token.type == TokenType.PLUS and self.peek() and self.peek().type == TokenType.PLUS:
            line, col = self.current_token.line, self.current_token.column
            self.eat(TokenType.PLUS)
            self.eat(TokenType.PLUS)
            return ASTNode('postfix_expression', [left], {'operator': '++'}, line, col)
        elif self.current_token.type == TokenType.MINUS and self.peek() and self.peek().type == TokenType.MINUS:
            line, col = self.current_token.line, self.current_token.column
            self.eat(TokenType.MINUS)
            self.eat(TokenType.MINUS)
            return ASTNode('postfix_expression', [left], {'operator': '--'}, line, col)
        
        while True:
            if self.current_token.type == TokenType.DOT:
                line, col = self.current_token.line, self.current_token.column
                self.eat(TokenType.DOT)
                member = self.eat(TokenType.IDENTIFIER).value
                left = ASTNode('member_access', [left], {'member': member}, line, col)
                continue
            if self.current_token.type == TokenType.LEFT_BRACKET:
                line, col = self.current_token.line, self.current_token.column
                self.eat(TokenType.LEFT_BRACKET)
                index = self.expression()
                self.eat(TokenType.RIGHT_BRACKET)
                left = ASTNode('array_access', [left, index], line=line, column=col)
                continue
            break

        if self.current_token.type == TokenType.LEFT_PAREN:
            line, col = self.current_token.line, self.current_token.column
            self.eat(TokenType.LEFT_PAREN)
            args = []
            if self.current_token.type != TokenType.RIGHT_PAREN:
                args = self.argument_list()
            self.eat(TokenType.RIGHT_PAREN)
            return ASTNode('function_call', [left] + args, line=line, column=col)
        
        return left
    
    def argument_list(self) -> List[ASTNode]:
        args = [self.expression()]
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            args.append(self.expression())
        return args
    
    def primary_expression(self) -> ASTNode:
        line, col = self.current_token.line, self.current_token.column
        
        if self.current_token.type == TokenType.IDENTIFIER:
            name = self.eat(TokenType.IDENTIFIER).value
            return ASTNode('identifier', [], {'name': name}, line, col)
        elif self.current_token.type == TokenType.INTEGER_LITERAL:
            value = self.parse_integer_literal(self.eat(TokenType.INTEGER_LITERAL).value)
            return ASTNode('integer_literal', [], {'value': value}, line, col)
        elif self.current_token.type == TokenType.FLOAT_LITERAL:
            value = float(self.eat(TokenType.FLOAT_LITERAL).value)
            return ASTNode('float_literal', [], {'value': value}, line, col)
        elif self.current_token.type == TokenType.CHAR_LITERAL:
            value = self.eat(TokenType.CHAR_LITERAL).value[1:-1]
            return ASTNode('char_literal', [], {'value': value}, line, col)
        elif self.current_token.type == TokenType.STRING_LITERAL:
            value = self.eat(TokenType.STRING_LITERAL).value[1:-1]
            return ASTNode('string_literal', [], {'value': value}, line, col)
        elif self.current_token.type == TokenType.TRUE:
            self.eat(TokenType.TRUE)
            return ASTNode('boolean_literal', [], {'value': True}, line, col)
        elif self.current_token.type == TokenType.FALSE:
            self.eat(TokenType.FALSE)
            return ASTNode('boolean_literal', [], {'value': False}, line, col)
        elif self.current_token.type == TokenType.LEFT_PAREN:
            self.eat(TokenType.LEFT_PAREN)
            expr = self.expression()
            self.eat(TokenType.RIGHT_PAREN)
            return expr
        else:
            raise SyntaxError(f"意外的token: {self.current_token.type}", line, col)

    @staticmethod
    def parse_integer_literal(value: str) -> int:
        text = value.strip()
        if text.startswith(('0x', '0X')):
            return int(text, 16)
        if text.startswith(('0b', '0B')):
            return int(text, 2)
        if text.startswith(('0o', '0O')):
            return int(text, 8)
        return int(text, 10)
