from .core import ASTNode

class EnhancedCodeGenerator:
    """增强版代码生成器"""
    
    def __init__(self):
        self.code = []
        self.indent = 0
        self.label_counter = 0
        self.var_offset = 8  # 局部变量用负偏移，所以初始值是8（表示-8）
        self.param_offset = 16  # 参数用正偏移
        self.var_offsets = {}
        self.param_offsets = {}
        self.in_function = False
    
    def generate(self, ast: ASTNode) -> str:
        """生成汇编代码"""
        self.visit(ast)
        return '\n'.join(self.code)
    
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
    
    def emit(self, line):
        self.code.append('    ' * self.indent + line)
    
    def new_label(self):
        self.label_counter += 1
        return f'L{self.label_counter}'
    
    def visit_program(self, node: ASTNode):
        self.emit('.text')
        self.emit('.global main')
        self.emit('.intel_syntax noprefix')
        self.emit('')
        for child in node.children:
            self.visit(child)
    
    def visit_function_declaration(self, node: ASTNode):
        func_name = node.value['name']
        
        # 重置偏移量计数器
        self.var_offset = 8  # 局部变量用负偏移，所以初始值是8（表示-8）
        self.param_offset = 16  # 参数从+16开始
        self.var_offsets = {}
        self.param_offsets = {}
        
        # 为参数分配偏移量（正偏移）
        params = node.value.get('params', [])
        for i, param in enumerate(params):
            self.param_offsets[param['name']] = 16 + i * 8
        
        self.in_function = True
        self.emit(f'{func_name}:')
        self.indent += 1
        self.emit('push rbp')
        self.emit('mov rbp, rsp')
        
        self.visit(node.children[0])
        
        self.emit('')
        self.emit('mov rsp, rbp')
        self.emit('pop rbp')
        self.emit('ret')
        self.indent -= 1
        self.emit('')
        self.in_function = False
    
    def visit_block(self, node: ASTNode):
        for child in node.children:
            self.visit(child)
    
    def visit_variable_declaration(self, node: ASTNode):
        var_name = node.value['name']
        array_size = node.value.get('array_size')
        
        if var_name not in self.param_offsets:
            if array_size:
                self.var_offsets[var_name] = -self.var_offset
                self.var_offset += array_size * 8
            else:
                self.var_offsets[var_name] = -self.var_offset
                self.var_offset += 8
        
        if node.children:
            self.visit(node.children[0])
            if not array_size:
                offset = self.var_offsets.get(var_name, self.param_offsets.get(var_name, 0))
                sign = '+' if offset > 0 else ''
                self.emit(f'mov qword ptr [rbp{sign}{offset}], rax')
    
    def visit_variable_declarations(self, node: ASTNode):
        for child in node.children:
            self.visit(child)
    
    def visit_if_statement(self, node: ASTNode):
        self.visit(node.children[0])
        
        else_label = self.new_label()
        end_label = self.new_label()
        
        self.emit('cmp rax, 0')
        self.emit(f'je {else_label}')
        
        self.visit(node.children[1])
        self.emit(f'jmp {end_label}')
        self.emit(f'{else_label}:')
        
        if len(node.children) > 2:
            self.visit(node.children[2])
        
        self.emit(f'{end_label}:')
    
    def visit_while_statement(self, node: ASTNode):
        start_label = self.new_label()
        end_label = self.new_label()
        
        self.emit(f'{start_label}:')
        self.visit(node.children[0])
        self.emit('cmp rax, 0')
        self.emit(f'je {end_label}')
        self.visit(node.children[1])
        self.emit(f'jmp {start_label}')
        self.emit(f'{end_label}:')
    
    def visit_for_statement(self, node: ASTNode):
        index = 0
        init = node.children[index] if node.value and node.value.get('has_init') else None
        index += 1 if init is not None else 0
        condition = node.children[index] if node.value and node.value.get('has_condition') else None
        index += 1 if condition is not None else 0
        increment = node.children[index] if node.value and node.value.get('has_increment') else None
        index += 1 if increment is not None else 0
        body = node.children[index] if index < len(node.children) else node.children[-1]
        
        if init:
            self.visit(init)
        
        start_label = self.new_label()
        end_label = self.new_label()
        
        self.emit(f'{start_label}:')
        
        if condition:
            self.visit(condition)
            self.emit('cmp rax, 0')
            self.emit(f'je {end_label}')
        
        self.visit(body)
        
        if increment:
            self.visit(increment)
        
        self.emit(f'jmp {start_label}')
        self.emit(f'{end_label}:')
    
    def visit_return_statement(self, node: ASTNode):
        if node.children:
            self.visit(node.children[0])
        self.emit('ret')
    
    def visit_expression_statement(self, node: ASTNode):
        self.visit(node.children[0])
    
    def visit_binary_expression(self, node: ASTNode):
        self.visit(node.children[1])
        self.emit('push rax')
        self.visit(node.children[0])
        self.emit('pop rbx')
        
        op = node.value['operator']
        ops = {
            '+': 'add rax, rbx',
            '-': 'sub rax, rbx',
            '*': 'imul rbx',
            '/': 'idiv rbx',
            '%': ('idiv rbx', 'mov rax, rdx'),
            '==': ('cmp rax, rbx', 'sete al', 'movzx rax, al'),
            '!=': ('cmp rax, rbx', 'setne al', 'movzx rax, al'),
            '<': ('cmp rax, rbx', 'setl al', 'movzx rax, al'),
            '>': ('cmp rax, rbx', 'setg al', 'movzx rax, al'),
            '<=': ('cmp rax, rbx', 'setle al', 'movzx rax, al'),
            '>=': ('cmp rax, rbx', 'setge al', 'movzx rax, al'),
        }
        
        if op in ops:
            if isinstance(ops[op], tuple):
                for o in ops[op]:
                    self.emit(o)
            else:
                self.emit(ops[op])
    
    def visit_unary_expression(self, node: ASTNode):
        self.visit(node.children[0])
        op = node.value['operator']
        if op == '-':
            self.emit('neg rax')
        elif op == '!':
            self.emit('cmp rax, 0')
            self.emit('sete al')
            self.emit('movzx rax, al')
        elif op == '&':
            # 取地址 - lea rax, [rbp+offset]
            pass
        elif op == '*':
            # 解引用 - rax中存储的是地址，需要加载该地址处的值
            self.emit('mov rax, qword ptr [rax]')
    
    def visit_address_of(self, node: ASTNode):
        # 取地址操作 &
        child = node.children[0]
        if child.type == 'identifier':
            # 简单变量: &x -> lea rax, [rbp+offset]
            name = child.value['name']
            offset = self.var_offsets.get(name, self.param_offsets.get(name, 0))
            sign = '+' if offset > 0 else ''
            self.emit(f'lea rax, [rbp{sign}{offset}]')
        elif child.type == 'array_access':
            # 数组元素: &arr[index] -> 计算元素地址
            arr_name = child.children[0].value['name']
            arr_offset = self.var_offsets.get(arr_name, self.param_offsets.get(arr_name, 0))
            arr_sign = '+' if arr_offset > 0 else ''
            
            # 访问index表达式
            self.visit(child.children[1])
            self.emit('push rax')  # 保存index
            
            # 获取数组基地址
            self.emit(f'lea rax, [rbp{arr_sign}{arr_offset}]')
            
            # pop index到rbx
            self.emit('pop rbx')
            
            # 计算实际地址: rax + rbx * 8
            self.emit('imul rbx, 8')
            self.emit('add rax, rbx')
    
    def visit_postfix_expression(self, node: ASTNode):
        self.visit(node.children[0])
        op = node.value.get('operator')
        if op == '++':
            self.emit('add rax, 1')
        elif op == '--':
            self.emit('sub rax, 1')
    
    def visit_function_call(self, node: ASTNode):
        args = node.children[1:]
        # 按顺序压入参数（从左到右）
        for arg in args:
            self.visit(arg)
            self.emit('push rax')
        
        func_name = node.children[0].value['name']
        self.emit(f'call {func_name}')
        
        if args:
            self.emit(f'add rsp, {len(args) * 8}')
    
    def visit_assignment_expression(self, node: ASTNode):
        # 保存右值到栈上
        self.visit(node.children[1])
        self.emit('push rax')
        
        # 获取左值地址
        left = node.children[0]
        if left.type == 'identifier':
            # 简单变量赋值: 直接用lea获取地址
            var_name = left.value.get('name')
            offset = self.var_offsets.get(var_name, self.param_offsets.get(var_name, 0))
            sign = '+' if offset > 0 else ''
            self.emit(f'lea rax, [rbp{sign}{offset}]')
        elif left.type == 'array_access':
            # 数组元素赋值: 计算元素地址
            arr_name = left.children[0].value['name']
            arr_offset = self.var_offsets.get(arr_name, self.param_offsets.get(arr_name, 0))
            arr_sign = '+' if arr_offset > 0 else ''
            
            # 访问index表达式
            self.visit(left.children[1])
            self.emit('push rax')  # 保存index
            
            # 获取数组基地址
            self.emit(f'lea rax, [rbp{arr_sign}{arr_offset}]')
            
            # pop index到rbx
            self.emit('pop rbx')
            
            # 计算实际地址: rax + rbx * 8
            self.emit('imul rbx, 8')
            self.emit('add rax, rbx')
        elif left.type == 'unary_expression' and left.value.get('operator') == '*':
            # 指针解引用赋值: *ptr = value
            # 访问指针变量，获取指针的值（即地址）
            self.visit(left.children[0])
            # 此时rax中存储的是指针的值（地址），这就是目标地址
        
        # pop 右值到 rbx
        self.emit('pop rbx')
        # 将右值存储到左值地址
        self.emit('mov qword ptr [rax], rbx')
    
    def visit_identifier(self, node: ASTNode):
        name = node.value['name']
        offset = self.var_offsets.get(name, self.param_offsets.get(name, 0))
        sign = '+' if offset > 0 else ''
        self.emit(f'mov rax, qword ptr [rbp{sign}{offset}]')
    
    def visit_array_access(self, node: ASTNode):
        # 数组下标访问: arr[index]
        # 先计算数组基地址
        arr_name = node.children[0].value['name']
        arr_offset = self.var_offsets.get(arr_name, self.param_offsets.get(arr_name, 0))
        arr_sign = '+' if arr_offset > 0 else ''
        
        # 访问index表达式，结果在rax中
        self.visit(node.children[1])
        self.emit('push rax')  # 保存index
        
        # 获取数组基地址到rax
        self.emit(f'lea rax, [rbp{arr_sign}{arr_offset}]')
        
        # pop index到rbx
        self.emit('pop rbx')
        
        # 计算实际地址: rax + rbx * 8 (每个元素8字节)
        self.emit('imul rbx, 8')
        self.emit('add rax, rbx')
        
        # 加载值
        self.emit('mov rax, qword ptr [rax]')
    
    def visit_integer_literal(self, node: ASTNode):
        self.emit(f'mov rax, {node.value["value"]}')
    
    def visit_float_literal(self, node: ASTNode):
        self.emit(f'mov rax, {int(node.value["value"])}')
    
    def visit_boolean_literal(self, node: ASTNode):
        self.emit(f'mov rax, {"1" if node.value["value"] else "0"}')
