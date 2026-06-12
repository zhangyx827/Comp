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
        self.types = {}
        self.enum_constants = {}
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
            'symbols_used': self.symbols_used,
            'types': self.types,
            'enum_constants': self.enum_constants
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
            storage_slots = self.type_slots(param['type'])
            if param.get('array_size'):
                storage_slots *= param['array_size']
            self.symbol_table.insert(param['name'], {
                'type': 'variable',
                'data_type': param['type'],
                'storage_slots': storage_slots,
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
        
        storage_slots = self.type_slots(var_type)
        if node.value.get('array_size'):
            storage_slots *= node.value['array_size']
        node.value['storage_slots'] = storage_slots

        self.symbol_table.insert(var_name, {
            'type': 'variable',
            'data_type': var_type,
            'storage_slots': storage_slots,
            'line': node.line
        })
        
        if node.children:
            self.visit(node.children[0])
    
    def visit_variable_declarations(self, node: ASTNode):
        for child in node.children:
            self.visit(child)
    
    def visit_identifier(self, node: ASTNode):
        name = node.value['name']
        if name in self.enum_constants:
            node.type = 'integer_literal'
            node.value = {'value': self.enum_constants[name]}
            return

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
        if symbol.get('data_type'):
            node.value['data_type'] = symbol['data_type']
    
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

    def visit_struct_definition(self, node: ASTNode):
        self.register_composite_type('struct', node)

    def visit_union_definition(self, node: ASTNode):
        self.register_composite_type('union', node)

    def visit_enum_definition(self, node: ASTNode):
        name = node.value.get('name')
        type_name = f"enum {name}" if name else "enum"
        if name and type_name in self.types:
            self.errors.append(f"类型 '{type_name}' 已声明 (行 {node.line})")
            return
        members = node.value.get('members', [])
        for member in members:
            const_name = member['name']
            if const_name in self.enum_constants:
                self.errors.append(f"枚举常量 '{const_name}' 已声明 (行 {node.line})")
                continue
            self.enum_constants[const_name] = member['value']
            self.global_scope.insert(const_name, {
                'type': 'enum_constant',
                'data_type': type_name,
                'value': member['value'],
                'line': node.line
            })
        if name:
            self.types[type_name] = {
                'kind': 'enum',
                'name': name,
                'members': members,
                'size': 1
            }

    def register_composite_type(self, kind: str, node: ASTNode):
        name = node.value.get('name')
        if not name:
            self.errors.append(f"匿名 {kind} 类型定义暂不支持 (行 {node.line})")
            return
        type_name = f"{kind} {name}"
        if type_name in self.types:
            self.errors.append(f"类型 '{type_name}' 已声明 (行 {node.line})")
            return

        layout = {}
        offset = 0
        max_size = 1
        for field in node.value.get('members', []):
            field_size = self.type_slots(field['type'])
            if field.get('array_size'):
                field_size *= field['array_size']
            field_offset = 0 if kind == 'union' else offset
            layout[field['name']] = {
                'type': field['type'],
                'offset': field_offset,
                'size': field_size,
                'is_pointer': field.get('is_pointer', False),
                'array_size': field.get('array_size')
            }
            if kind == 'struct':
                offset += field_size
            else:
                max_size = max(max_size, field_size)

        self.types[type_name] = {
            'kind': kind,
            'name': name,
            'fields': layout,
            'size': max(offset, 1) if kind == 'struct' else max_size
        }

    def visit_member_access(self, node: ASTNode):
        self.visit(node.children[0])
        base_type = self.expression_type(node.children[0])
        if not base_type or base_type not in self.types:
            self.errors.append(f"非结构/联合类型不能访问成员 '{node.value['member']}' (行 {node.line})")
            return
        type_info = self.types[base_type]
        member = node.value['member']
        field = type_info.get('fields', {}).get(member)
        if not field:
            self.errors.append(f"类型 '{base_type}' 没有成员 '{member}' (行 {node.line})")
            return
        node.value['base_type'] = base_type
        node.value['data_type'] = field['type']
        node.value['offset'] = field['offset']
        node.value['storage_slots'] = field['size']

    def visit_array_access(self, node: ASTNode):
        self.visit(node.children[0])
        self.visit(node.children[1])
        base_type = self.expression_type(node.children[0])
        if base_type:
            node.value = node.value or {}
            node.value['data_type'] = base_type

    def expression_type(self, node: ASTNode):
        if node.type == 'identifier':
            return node.value.get('data_type')
        if node.type == 'member_access':
            return node.value.get('data_type')
        return None

    def type_slots(self, type_name: str) -> int:
        return self.types.get(type_name, {}).get('size', 1)
