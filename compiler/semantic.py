from typing import Dict, Any, Optional, List
from .core import ASTNode


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
        if self.parent:
            return self.parent.lookup(name)
        return None

    def get_all_symbols(self):
        result = []
        for name, symbol in self.symbols.items():
            result.append({'name': name, **symbol})
        return result


class EnhancedSemanticAnalyzer:
    """增强版语义分析器，负责作用域管理和类型检查"""

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.global_scope = SymbolTable()
        self.types = {}
        self.enum_constants = {}
        self.errors = []
        self.warnings = []
        self.current_function = None
        self.current_return_type = None
        self.loop_depth = 0
        self.symbols_used = []
        self.local_symbols = []

    def analyze(self, ast: ASTNode) -> Dict[str, Any]:
        self.visit(ast)
        return {
            'success': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'global_symbols': self.global_scope.get_all_symbols(),
            'local_symbols': self.local_symbols,
            'symbols_used': self.symbols_used,
            'types': self.types,
            'enum_constants': self.enum_constants,
        }

    def visit(self, node: Optional[ASTNode]):
        if node is None:
            return None
        method = getattr(self, f'visit_{node.type}', self.generic_visit)
        return method(node)

    def generic_visit(self, node: ASTNode):
        last = None
        for child in node.children:
            if child:
                last = self.visit(child)
        return last

    def visit_program(self, node: ASTNode):
        for child in node.children:
            self.visit(child)

    def visit_function_declaration(self, node: ASTNode):
        func_name = node.value['name']
        return_type = node.value['return_type']
        params = node.value['params']

        if self.global_scope.lookup(func_name):
            self.errors.append(f"函数 '{func_name}' 已声明 (行 {node.line})")
            return

        self.global_scope.insert(func_name, {
            'type': 'function',
            'return_type': return_type,
            'params': params,
            'line': node.line,
        })

        prev_scope = self.symbol_table
        self.symbol_table = SymbolTable(prev_scope)
        prev_function = self.current_function
        prev_return_type = self.current_return_type
        self.current_function = func_name
        self.current_return_type = return_type

        for param in params:
            storage_slots = self.type_slots(param['type'])
            if param.get('array_size'):
                storage_slots *= param['array_size']
            local_symbol = {
                'name': param['name'],
                'type': 'variable',
                'data_type': self.normalize_type(param['type'], pointer=param.get('is_pointer', False), array_size=param.get('array_size')),
                'storage_slots': storage_slots,
                'line': param.get('line', node.line),
                'scope': self.current_function or 'global',
            }
            self.symbol_table.insert(param['name'], {
                'type': local_symbol['type'],
                'data_type': local_symbol['data_type'],
                'storage_slots': local_symbol['storage_slots'],
                'line': local_symbol['line'],
            })
            self.local_symbols.append(local_symbol)

        self.visit(node.children[0])

        self.current_function = prev_function
        self.current_return_type = prev_return_type
        self.symbol_table = prev_scope

    def visit_block(self, node: ASTNode):
        prev = self.symbol_table
        self.symbol_table = SymbolTable(prev)
        self.generic_visit(node)
        self.symbol_table = prev

    def visit_variable_declaration(self, node: ASTNode):
        var_name = node.value['name']
        var_type = self.normalize_type(
            node.value['type'],
            pointer=node.value.get('is_pointer', False),
            array_size=node.value.get('array_size')
        )

        if self.symbol_table.lookup(var_name):
            self.errors.append(f"变量 '{var_name}' 已声明 (行 {node.line})")
            return

        storage_slots = self.type_slots(var_type)
        if node.value.get('array_size'):
            storage_slots *= node.value['array_size']
        node.value['storage_slots'] = storage_slots
        node.value['data_type'] = var_type

        self.symbol_table.insert(var_name, {
            'type': 'variable',
            'data_type': var_type,
            'storage_slots': storage_slots,
            'line': node.line,
        })
        self.local_symbols.append({
            'name': var_name,
            'type': 'variable',
            'data_type': var_type,
            'storage_slots': storage_slots,
            'line': node.line,
            'scope': self.current_function or 'block',
        })

        if node.children:
            init_type = self.visit(node.children[0])
            self.check_assignment_compatibility(var_type, init_type, node.line, "初始化")

    def visit_variable_declarations(self, node: ASTNode):
        for child in node.children:
            self.visit(child)

    def visit_identifier(self, node: ASTNode):
        name = node.value['name']
        if name in self.enum_constants:
            enum_type = self.enum_constants[name]['type']
            node.type = 'integer_literal'
            node.value = {
                'value': self.enum_constants[name]['value'],
                'data_type': enum_type,
            }
            return enum_type

        symbol = self.symbol_table.lookup(name) or self.global_scope.lookup(name)
        if not symbol:
            self.errors.append(f"未声明的标识符 '{name}' (行 {node.line})")
            return None

        self.symbols_used.append({'name': name, 'type': symbol['type'], 'line': node.line})
        data_type = symbol.get('data_type') or symbol.get('return_type')
        if data_type:
            node.value['data_type'] = data_type
        return data_type

    def visit_integer_literal(self, node: ASTNode):
        node.value['data_type'] = 'int'
        return 'int'

    def visit_float_literal(self, node: ASTNode):
        node.value['data_type'] = 'float'
        return 'float'

    def visit_char_literal(self, node: ASTNode):
        node.value['data_type'] = 'char'
        return 'char'

    def visit_string_literal(self, node: ASTNode):
        node.value['data_type'] = 'string'
        return 'string'

    def visit_boolean_literal(self, node: ASTNode):
        node.value['data_type'] = 'bool'
        return 'bool'

    def visit_if_statement(self, node: ASTNode):
        cond_type = self.visit(node.children[0])
        self.expect_bool_like(cond_type, node.children[0].line)
        self.visit(node.children[1])
        if len(node.children) > 2:
            self.visit(node.children[2])

    def visit_while_statement(self, node: ASTNode):
        self.loop_depth += 1
        cond_type = self.visit(node.children[0])
        self.expect_bool_like(cond_type, node.children[0].line)
        self.visit(node.children[1])
        self.loop_depth -= 1

    def visit_for_statement(self, node: ASTNode):
        self.loop_depth += 1
        for child in node.children[:-1]:
            if child:
                self.visit(child)
        self.visit(node.children[-1])
        self.loop_depth -= 1

    def visit_break_statement(self, node: ASTNode):
        if self.loop_depth == 0:
            self.warnings.append(f"'break' 语句在循环外使用 (行 {node.line})")

    def visit_continue_statement(self, node: ASTNode):
        if self.loop_depth == 0:
            self.warnings.append(f"'continue' 语句在循环外使用 (行 {node.line})")

    def visit_return_statement(self, node: ASTNode):
        expr_type = self.visit(node.children[0]) if node.children else 'void'
        if self.current_return_type and self.current_return_type != 'void':
            self.check_assignment_compatibility(self.current_return_type, expr_type, node.line, "返回值")
        elif self.current_return_type == 'void' and expr_type != 'void':
            self.errors.append(f"void 函数不应返回值 (行 {node.line})")
        return expr_type

    def visit_binary_expression(self, node: ASTNode):
        left_type = self.visit(node.children[0])
        right_type = self.visit(node.children[1])
        op = node.value.get('operator')

        if op in ['+', '-', '*', '/', '%', '<<', '>>', '&', '|', '^']:
            result = self.arithmetic_result_type(left_type, right_type, node.line)
            node.value['data_type'] = result
            return result
        if op in ['<', '>', '<=', '>=', '==', '!=', '&&', '||']:
            self.require_scalar_compatible(left_type, right_type, node.line, op)
            node.value['data_type'] = 'bool'
            return 'bool'

        node.value['data_type'] = left_type or right_type
        return node.value['data_type']

    def visit_unary_expression(self, node: ASTNode):
        operand_type = self.visit(node.children[0])
        op = node.value.get('operator')
        if op in ['+', '-', '~', '!']:
            node.value['data_type'] = operand_type
            return operand_type
        if op == '*':
            if not operand_type or '*' not in operand_type:
                self.errors.append(f"解引用操作数不是指针 (行 {node.line})")
                return None
            base = operand_type[:-1]
            node.value['data_type'] = base
            return base
        node.value['data_type'] = operand_type
        return operand_type

    def visit_address_of(self, node: ASTNode):
        operand_type = self.visit(node.children[0])
        if not operand_type:
            return None
        result = f"{operand_type}*"
        node.value = node.value or {}
        node.value['data_type'] = result
        return result

    def visit_postfix_expression(self, node: ASTNode):
        operand_type = self.visit(node.children[0])
        node.value['data_type'] = operand_type
        return operand_type

    def visit_assignment_expression(self, node: ASTNode):
        left_node = node.children[0]
        right_node = node.children[1]
        left_type = self.visit(left_node)
        right_type = self.visit(right_node)

        if not self.is_assignable_target(left_node):
            self.errors.append(f"赋值左值无效 (行 {node.line})")
            return None

        self.check_assignment_compatibility(left_type, right_type, node.line, "赋值")
        node.value['data_type'] = left_type
        return left_type

    def visit_function_call(self, node: ASTNode):
        callee = node.children[0]
        func_name = None
        if callee.type == 'identifier':
            func_name = callee.value['name']
        else:
            self.visit(callee)

        symbol = self.global_scope.lookup(func_name) if func_name else None
        if not symbol or symbol.get('type') != 'function':
            self.errors.append(f"调用了未声明的函数 '{func_name}' (行 {node.line})")
            for arg in node.children[1:]:
                self.visit(arg)
            return None

        params = symbol.get('params', [])
        args = node.children[1:]
        if len(args) != len(params):
            self.errors.append(f"函数 '{func_name}' 参数数量不匹配 (行 {node.line})")

        for i, arg in enumerate(args):
            arg_type = self.visit(arg)
            if i < len(params):
                expected = self.normalize_type(
                    params[i]['type'],
                    pointer=params[i].get('is_pointer', False),
                    array_size=params[i].get('array_size')
                )
                self.check_assignment_compatibility(expected, arg_type, arg.line, f"函数 '{func_name}' 参数 {i + 1}")

        return_type = symbol.get('return_type', 'void')
        node.value = node.value or {}
        node.value['data_type'] = return_type
        return return_type

    def visit_member_access(self, node: ASTNode):
        base_type = self.visit(node.children[0])
        if not base_type or base_type not in self.types:
            self.errors.append(f"非结构/联合类型不能访问成员 '{node.value['member']}' (行 {node.line})")
            return None
        type_info = self.types[base_type]
        field = type_info.get('fields', {}).get(node.value['member'])
        if not field:
            self.errors.append(f"类型 '{base_type}' 没有成员 '{node.value['member']}' (行 {node.line})")
            return None
        node.value['base_type'] = base_type
        node.value['data_type'] = field['type']
        node.value['offset'] = field['offset']
        node.value['storage_slots'] = field['size']
        return field['type']

    def visit_array_access(self, node: ASTNode):
        base_type = self.visit(node.children[0])
        index_type = self.visit(node.children[1])
        self.check_assignment_compatibility('int', index_type, node.children[1].line, "数组下标")
        if not base_type:
            return None
        element_type = self.array_element_type(base_type)
        if not element_type:
            self.errors.append(f"类型 '{base_type}' 不能进行数组访问 (行 {node.line})")
            return None
        node.value = node.value or {}
        node.value['data_type'] = element_type
        return element_type

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
            self.enum_constants[const_name] = {
                'value': member['value'],
                'type': type_name,
            }
            self.global_scope.insert(const_name, {
                'type': 'enum_constant',
                'data_type': type_name,
                'value': member['value'],
                'line': node.line,
            })
        if name:
            self.types[type_name] = {'kind': 'enum', 'name': name, 'members': members, 'size': 1}

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
            field_type = self.normalize_type(field['type'], pointer=field.get('is_pointer', False), array_size=field.get('array_size'))
            field_size = self.type_slots(field_type)
            if field.get('array_size'):
                field_size *= field['array_size']
            field_offset = 0 if kind == 'union' else offset
            layout[field['name']] = {
                'type': field_type,
                'offset': field_offset,
                'size': field_size,
                'is_pointer': field.get('is_pointer', False),
                'array_size': field.get('array_size'),
            }
            if kind == 'struct':
                offset += field_size
            else:
                max_size = max(max_size, field_size)

        self.types[type_name] = {
            'kind': kind,
            'name': name,
            'fields': layout,
            'size': max(offset, 1) if kind == 'struct' else max_size,
        }

    def expression_type(self, node: ASTNode):
        return self.visit(node)

    def type_slots(self, type_name: str) -> int:
        if not type_name:
            return 1
        if type_name.endswith('*'):
            return 1
        return self.types.get(type_name, {}).get('size', 1)

    def normalize_type(self, type_name: str, pointer: bool = False, array_size: Optional[int] = None) -> str:
        result = type_name
        if pointer:
            result = f"{result}*"
        if array_size is not None:
            result = f"{result}[]"
        return result

    def array_element_type(self, type_name: str) -> Optional[str]:
        if type_name.endswith('[]'):
            return type_name[:-2]
        if type_name.endswith('*'):
            return type_name[:-1]
        return None

    def is_assignable_target(self, node: ASTNode) -> bool:
        return node.type in {'identifier', 'member_access', 'array_access', 'unary_expression'}

    def expect_bool_like(self, type_name: Optional[str], line: int):
        if type_name is None:
            return
        if type_name not in {'bool', 'int', 'char', 'float'} and not type_name.endswith('*'):
            self.warnings.append(f"条件表达式类型 '{type_name}' 可能不可直接作为布尔值 (行 {line})")

    def require_scalar_compatible(self, left: Optional[str], right: Optional[str], line: int, op: str):
        if left is None or right is None:
            return
        if left != right:
            if self.is_enum_compatible(left, right):
                return
            if self.is_numeric(left) and self.is_numeric(right):
                return
            self.errors.append(f"运算符 '{op}' 两侧类型不匹配: {left} vs {right} (行 {line})")

    def arithmetic_result_type(self, left: Optional[str], right: Optional[str], line: int) -> Optional[str]:
        if left is None or right is None:
            return left or right
        if left == right:
            return left
        if self.is_numeric(left) and self.is_numeric(right):
            if 'float' in (left, right):
                return 'float'
            return 'int'
        if left.endswith('*') and right == 'int' and self.is_pointer_arithmetic_allowed('+'):
            return left
        if right.endswith('*') and left == 'int' and self.is_pointer_arithmetic_allowed('+'):
            return right
        self.errors.append(f"算术表达式类型不兼容: {left} 和 {right} (行 {line})")
        return left

    def is_numeric(self, type_name: Optional[str]) -> bool:
        return type_name in {'int', 'float', 'char', 'bool'}

    def is_pointer_arithmetic_allowed(self, op: str) -> bool:
        return op in {'+', '-'}

    def check_assignment_compatibility(self, target: Optional[str], source: Optional[str], line: int, context: str):
        if target is None or source is None:
            return
        if target == source:
            return
        if self.is_enum_compatible(target, source):
            return
        if target == 'float' and source == 'int':
            return
        if target.endswith('*') and source == 'int':
            return
        self.errors.append(f"{context}类型不匹配: 期望 {target}, 得到 {source} (行 {line})")

    def is_enum_compatible(self, left: Optional[str], right: Optional[str]) -> bool:
        if not left or not right:
            return False
        left_is_enum = left.startswith('enum ')
        right_is_enum = right.startswith('enum ')
        return left_is_enum and right_is_enum and left == right
