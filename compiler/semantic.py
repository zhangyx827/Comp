from typing import List, Dict, Any
from .core import ASTNode, SemanticError

class SymbolTable:
    """符号表"""
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent
        self.level = 0 if parent is None else parent.level + 1
    
    def insert(self, name, symbol):
        self.symbols[name] = symbol
    
    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent:
            return self.parent.lookup(name)
        return None
    
    def get_all_symbols(self):
        result = []
        for name, symbol in self.symbols.items():
            result.append({'name': name, **symbol})
        return result

class EnhancedSemanticAnalyzer:
    """增强版语义分析器"""
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.global_scope = SymbolTable()
        self.errors = []
        self.warnings = []
        self.current_function = None
        self.loop_depth = 0
        self.symbols_used = []
    
    def analyze(self, ast: ASTNode) -> Dict[str, Any]:
        """执行语义分析"""
        self.visit(ast)
        
        return {
            'success': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'global_symbols': self.global_scope.get_all_symbols(),
            'local_symbols': self.symbol_table.get_all_symbols(),
            'symbols_used': self.symbols_used
        }
    
    def visit(self, node: ASTNode):
        if node is None:
            return
        method_name = f'visit_{node.type}'
        method = getattr(self, method_name, self.generic_visit)
        return method(node)
    
    def generic_visit(self, node: ASTNode):
        for child in node.children:
            if child:
                self.visit(child)
    
    def visit_program(self, node: ASTNode):
        for child in node.children:
            self.visit(child)
    
    def visit_function_declaration(self, node: ASTNode):
        func_name = node.value['name']
        return_type = node.value['return_type']
        params = node.value['params']
        
        if self.global_scope.lookup(func_name):
            self.errors.append(f"函数 '{func_name}' 已声明")
            return
        
        self.global_scope.insert(func_name, {
            'type': 'function',
            'return_type': return_type,
            'params': params,
            'line': node.line
        })
        
        self.symbol_table = SymbolTable(self.symbol_table)
        
        for param in params:
            self.symbol_table.insert(param['name'], {
                'type': 'variable',
                'data_type': param['type'],
                'line': param.get('line', node.line)
            })
        
        self.current_function = func_name
        self.visit(node.children[0])
        self.current_function = None
        
        self.symbol_table = self.symbol_table.parent
    
    def visit_block(self, node: ASTNode):
        self.symbol_table = SymbolTable(self.symbol_table)
        self.generic_visit(node)
        self.symbol_table = self.symbol_table.parent
    
    def visit_variable_declaration(self, node: ASTNode):
        var_name = node.value['name']
        var_type = node.value['type']
        
        if self.symbol_table.lookup(var_name):
            self.errors.append(f"变量 '{var_name}' 已声明 (行 {node.line})")
            return
        
        self.symbol_table.insert(var_name, {
            'type': 'variable',
            'data_type': var_type,
            'line': node.line
        })
        
        if node.children:
            self.visit(node.children[0])
    
    def visit_variable_declarations(self, node: ASTNode):
        for child in node.children:
            self.visit(child)
    
    def visit_identifier(self, node: ASTNode):
        name = node.value['name']
        symbol = self.symbol_table.lookup(name)
        
        # 如果局部作用域没有找到，尝试全局作用域（函数）
        if not symbol:
            symbol = self.global_scope.lookup(name)
        
        if not symbol:
            self.errors.append(f"未声明的标识符 '{name}' (行 {node.line})")
            return
        
        self.symbols_used.append({
            'name': name,
            'type': symbol['type'],
            'line': node.line
        })
    
    def visit_if_statement(self, node: ASTNode):
        self.visit(node.children[0])
        self.visit(node.children[1])
        if len(node.children) > 2:
            self.visit(node.children[2])
    
    def visit_while_statement(self, node: ASTNode):
        self.loop_depth += 1
        self.visit(node.children[0])
        self.visit(node.children[1])
        self.loop_depth -= 1
    
    def visit_for_statement(self, node: ASTNode):
        self.loop_depth += 1
        self.generic_visit(node)
        self.loop_depth -= 1
    
    def visit_break_statement(self, node: ASTNode):
        if self.loop_depth == 0:
            self.warnings.append(f"'break' 语句在循环外使用 (行 {node.line})")
    
    def visit_continue_statement(self, node: ASTNode):
        if self.loop_depth == 0:
            self.warnings.append(f"'continue' 语句在循环外使用 (行 {node.line})")
    
    def visit_binary_expression(self, node: ASTNode):
        self.visit(node.children[0])
        self.visit(node.children[1])
    
    def visit_unary_expression(self, node: ASTNode):
        self.visit(node.children[0])
    
    def visit_postfix_expression(self, node: ASTNode):
        self.visit(node.children[0])
    
    def visit_assignment_expression(self, node: ASTNode):
        self.visit(node.children[0])
        self.visit(node.children[1])
    
    def visit_function_call(self, node: ASTNode):
        self.visit(node.children[0])
        for child in node.children[1:]:
            self.visit(child)

