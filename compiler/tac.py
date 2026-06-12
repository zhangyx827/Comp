from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from .core import ASTNode


@dataclass
class TACInstruction:
    """Three-address-code instruction."""

    op: str
    arg1: Any = None
    arg2: Any = None
    result: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op": self.op,
            "arg1": self.arg1,
            "arg2": self.arg2,
            "result": self.result,
            "text": str(self),
        }

    def __str__(self) -> str:
        if self.op == "function":
            return f"function {self.result}:"
        if self.op == "end_function":
            return f"end function {self.result}"
        if self.op == "param_decl":
            return f"param {self.result}"
        if self.op == "declare":
            size = f"[{self.arg1}]" if self.arg1 else ""
            return f"declare {self.result}{size}"
        if self.op == "label":
            return f"{self.result}:"
        if self.op == "goto":
            return f"goto {self.result}"
        if self.op == "if_false":
            return f"if_false {self.arg1} goto {self.result}"
        if self.op == "return":
            return f"return {self.arg1}" if self.arg1 is not None else "return"
        if self.op == "assign":
            return f"{self.result} = {self.arg1}"
        if self.op in {"neg", "not", "bit_not", "deref", "addr"}:
            symbol = {"neg": "-", "not": "!", "bit_not": "~", "deref": "*", "addr": "&"}[self.op]
            return f"{self.result} = {symbol}{self.arg1}"
        if self.op == "array_load":
            return f"{self.result} = {self.arg1}[{self.arg2}]"
        if self.op == "array_store":
            return f"{self.result}[{self.arg1}] = {self.arg2}"
        if self.op == "member_addr":
            return f"{self.result} = &{self.arg1}.{self.arg2}"
        if self.op == "member_load":
            return f"{self.result} = {self.arg1}.{self.arg2}"
        if self.op == "member_store":
            return f"{self.arg1}.{self.arg2} = {self.result}"
        if self.op == "store":
            return f"*{self.result} = {self.arg1}"
        if self.op == "arg":
            return f"arg {self.arg1}"
        if self.op == "call":
            prefix = f"{self.result} = " if self.result else ""
            return f"{prefix}call {self.arg1}, {self.arg2}"
        return f"{self.result} = {self.arg1} {self.op} {self.arg2}"


class TACGenerator:
    """Lower AST to TAC before target-specific assembly generation."""

    def __init__(self):
        self.instructions: List[TACInstruction] = []
        self.temp_counter = 0
        self.label_counter = 0
        self.loop_stack: List[Dict[str, str]] = []

    def generate(self, ast: ASTNode) -> List[TACInstruction]:
        self.visit(ast)
        return self.instructions

    def emit(self, op: str, arg1: Any = None, arg2: Any = None, result: Any = None) -> TACInstruction:
        instruction = TACInstruction(op, arg1, arg2, result)
        self.instructions.append(instruction)
        return instruction

    def new_temp(self) -> str:
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def new_label(self) -> str:
        self.label_counter += 1
        return f"L{self.label_counter}"

    def visit(self, node: Optional[ASTNode]):
        if node is None:
            return None
        method = getattr(self, f"visit_{node.type}", self.generic_visit)
        return method(node)

    def generic_visit(self, node: ASTNode):
        for child in node.children:
            self.visit(child)

    def visit_program(self, node: ASTNode):
        for child in node.children:
            self.visit(child)

    def visit_function_declaration(self, node: ASTNode):
        name = node.value["name"]
        self.emit("function", result=name)
        for param in node.value.get("params", []):
            self.emit("param_decl", result=param["name"])
        self.visit(node.children[0])
        self.emit("end_function", result=name)

    def visit_block(self, node: ASTNode):
        for child in node.children:
            self.visit(child)

    def visit_variable_declarations(self, node: ASTNode):
        for child in node.children:
            self.visit(child)

    def visit_variable_declaration(self, node: ASTNode):
        name = node.value["name"]
        self.emit("declare", node.value.get("storage_slots", node.value.get("array_size")), result=name)
        if node.children:
            value = self.visit(node.children[0])
            self.emit("assign", value, result=name)

    def visit_expression_statement(self, node: ASTNode):
        if node.children:
            self.visit(node.children[0])

    def visit_if_statement(self, node: ASTNode):
        else_label = self.new_label()
        end_label = self.new_label()
        condition = self.visit(node.children[0])
        self.emit("if_false", condition, result=else_label)
        self.visit(node.children[1])
        self.emit("goto", result=end_label)
        self.emit("label", result=else_label)
        if len(node.children) > 2:
            self.visit(node.children[2])
        self.emit("label", result=end_label)

    def visit_while_statement(self, node: ASTNode):
        start_label = self.new_label()
        end_label = self.new_label()
        self.loop_stack.append({"continue": start_label, "break": end_label})
        self.emit("label", result=start_label)
        condition = self.visit(node.children[0])
        self.emit("if_false", condition, result=end_label)
        self.visit(node.children[1])
        self.emit("goto", result=start_label)
        self.emit("label", result=end_label)
        self.loop_stack.pop()

    def visit_for_statement(self, node: ASTNode):
        children = node.children
        index = 0
        init = children[index] if node.value.get("has_init") else None
        index += 1 if init is not None else 0
        condition = children[index] if node.value.get("has_condition") else None
        index += 1 if condition is not None else 0
        increment = children[index] if node.value.get("has_increment") else None
        index += 1 if increment is not None else 0
        body = children[index] if index < len(children) else None

        if init:
            self.visit(init)

        start_label = self.new_label()
        continue_label = self.new_label()
        end_label = self.new_label()
        self.loop_stack.append({"continue": continue_label, "break": end_label})

        self.emit("label", result=start_label)
        if condition:
            cond_value = self.visit(condition)
            self.emit("if_false", cond_value, result=end_label)

        self.visit(body)
        self.emit("label", result=continue_label)
        if increment:
            self.visit(increment)
        self.emit("goto", result=start_label)
        self.emit("label", result=end_label)
        self.loop_stack.pop()

    def visit_return_statement(self, node: ASTNode):
        value = self.visit(node.children[0]) if node.children else None
        self.emit("return", value)

    def visit_break_statement(self, node: ASTNode):
        if self.loop_stack:
            self.emit("goto", result=self.loop_stack[-1]["break"])

    def visit_continue_statement(self, node: ASTNode):
        if self.loop_stack:
            self.emit("goto", result=self.loop_stack[-1]["continue"])

    def visit_assignment_expression(self, node: ASTNode):
        value = self.visit(node.children[1])
        left = node.children[0]
        if left.type == "identifier":
            target = left.value["name"]
            self.emit("assign", value, result=target)
            return target
        if left.type == "array_access":
            array_name = left.children[0].value["name"]
            index = self.visit(left.children[1])
            self.emit("array_store", index, value, result=array_name)
            return value
        if left.type == "member_access":
            base, offset = self.member_reference(left)
            self.emit("member_store", base, offset, result=value)
            return value
        if left.type == "unary_expression" and left.value.get("operator") == "*":
            address = self.visit(left.children[0])
            self.emit("store", value, result=address)
            return value
        return value

    def visit_binary_expression(self, node: ASTNode):
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        result = self.new_temp()
        self.emit(node.value["operator"], left, right, result)
        return result

    def visit_unary_expression(self, node: ASTNode):
        value = self.visit(node.children[0])
        op = node.value["operator"]
        if op == "+":
            return value
        result = self.new_temp()
        op_name = {"-": "neg", "!": "not", "~": "bit_not", "*": "deref"}.get(op, op)
        self.emit(op_name, value, result=result)
        return result

    def visit_address_of(self, node: ASTNode):
        child = node.children[0]
        result = self.new_temp()
        if child.type == "identifier":
            self.emit("addr", child.value["name"], result=result)
        elif child.type == "member_access":
            base, offset = self.member_reference(child)
            self.emit("member_addr", base, offset, result)
        elif child.type == "array_access":
            array_name = child.children[0].value["name"]
            index = self.visit(child.children[1])
            self.emit("array_addr", array_name, index, result)
        return result

    def visit_postfix_expression(self, node: ASTNode):
        operand = node.children[0]
        if operand.type != "identifier":
            return self.visit(operand)
        name = operand.value["name"]
        one = "1"
        op = "+" if node.value.get("operator") == "++" else "-"
        updated = self.new_temp()
        self.emit(op, name, one, updated)
        self.emit("assign", updated, result=name)
        return name

    def visit_function_call(self, node: ASTNode):
        func_name = node.children[0].value["name"]
        args = [self.visit(arg) for arg in node.children[1:]]
        for arg in args:
            self.emit("arg", arg)
        result = self.new_temp()
        self.emit("call", func_name, len(args), result)
        return result

    def visit_array_access(self, node: ASTNode):
        array_name = node.children[0].value["name"]
        index = self.visit(node.children[1])
        result = self.new_temp()
        self.emit("array_load", array_name, index, result)
        return result

    def visit_member_access(self, node: ASTNode):
        base, offset = self.member_reference(node)
        result = self.new_temp()
        self.emit("member_load", base, offset, result)
        return result

    def member_reference(self, node: ASTNode):
        base_node = node.children[0]
        offset = int(node.value.get("offset", 0))
        if base_node.type == "identifier":
            return base_node.value["name"], offset
        if base_node.type == "member_access":
            base, base_offset = self.member_reference(base_node)
            return base, base_offset + offset
        raise ValueError("成员访问基表达式暂仅支持变量或嵌套成员")

    def visit_identifier(self, node: ASTNode):
        return node.value["name"]

    def visit_integer_literal(self, node: ASTNode):
        return str(node.value["value"])

    def visit_float_literal(self, node: ASTNode):
        return str(int(node.value["value"]))

    def visit_boolean_literal(self, node: ASTNode):
        return "1" if node.value["value"] else "0"

    def visit_char_literal(self, node: ASTNode):
        value = node.value["value"]
        return str(ord(value[0])) if value else "0"

    def visit_string_literal(self, node: ASTNode):
        return "0"


class TACAssemblyGenerator:
    """Translate TAC to Intel-syntax x86-64 style assembly."""

    BINARY_OPS: Set[str] = {
        "+",
        "-",
        "*",
        "/",
        "%",
        "==",
        "!=",
        "<",
        ">",
        "<=",
        ">=",
        "&&",
        "||",
        "<<",
        ">>",
        "&",
        "|",
        "^",
    }

    def __init__(self):
        self.code: List[str] = []
        self.indent = 0
        self.current_function: Optional[str] = None
        self.function_epilogue: Optional[str] = None
        self.offsets: Dict[str, int] = {}
        self.array_symbols: Set[str] = set()
        self.param_symbols: Set[str] = set()
        self.frame_size = 0
        self.pending_args: List[Any] = []

    def generate(self, instructions: List[TACInstruction]) -> str:
        self.code = []
        self.emit(".text")
        self.emit(".global main")
        self.emit(".intel_syntax noprefix")
        self.emit("")

        functions = self._split_functions(instructions)
        for name, body in functions:
            self._prepare_frame(body)
            self._emit_function(name, body)
        return "\n".join(self.code)

    def _split_functions(self, instructions: List[TACInstruction]) -> List[tuple]:
        functions = []
        current_name = None
        current_body = []
        for instruction in instructions:
            if instruction.op == "function":
                current_name = instruction.result
                current_body = []
            elif instruction.op == "end_function":
                functions.append((current_name, current_body))
                current_name = None
                current_body = []
            elif current_name is not None:
                current_body.append(instruction)
        return functions

    def _prepare_frame(self, body: List[TACInstruction]):
        self.offsets = {}
        self.array_symbols = set()
        self.param_symbols = set()
        offset = 8
        for instruction in body:
            if instruction.op == "param_decl":
                self.offsets[instruction.result] = offset
                self.param_symbols.add(instruction.result)
                offset += 8
            elif instruction.op == "declare":
                size = int(instruction.arg1 or 1)
                self.offsets[instruction.result] = offset
                if size > 1:
                    self.array_symbols.add(instruction.result)
                offset += size * 8
            elif instruction.result and self._is_symbol(instruction.result):
                if instruction.result not in self.offsets:
                    self.offsets[instruction.result] = offset
                    offset += 8
        self.frame_size = self._align(offset - 8, 16)

    def _emit_function(self, name: str, body: List[TACInstruction]):
        self.current_function = name
        self.function_epilogue = f".L_{name}_return"
        self.emit(f"{name}:")
        self.indent += 1
        self.emit("push rbp")
        self.emit("mov rbp, rsp")
        if self.frame_size:
            self.emit(f"sub rsp, {self.frame_size}")

        for index, instruction in enumerate(i for i in body if i.op == "param_decl"):
            self.emit(f"mov rax, qword ptr [rbp+{16 + index * 8}]")
            self._store(instruction.result, "rax")

        for instruction in body:
            if instruction.op != "param_decl":
                self._emit_instruction(instruction)

        self.emit(f"{self.function_epilogue}:")
        self.emit("mov rsp, rbp")
        self.emit("pop rbp")
        self.emit("ret")
        self.indent -= 1
        self.emit("")
        self.current_function = None
        self.function_epilogue = None
        self.pending_args = []

    def _emit_instruction(self, instruction: TACInstruction):
        op = instruction.op
        if op == "declare":
            return
        if op == "label":
            self.indent -= 1
            self.emit(f"{instruction.result}:")
            self.indent += 1
            return
        if op == "goto":
            self.emit(f"jmp {instruction.result}")
            return
        if op == "if_false":
            self._load(instruction.arg1, "rax")
            self.emit("cmp rax, 0")
            self.emit(f"je {instruction.result}")
            return
        if op == "return":
            if instruction.arg1 is not None:
                self._load(instruction.arg1, "rax")
            self.emit(f"jmp {self.function_epilogue}")
            return
        if op == "assign":
            self._load(instruction.arg1, "rax")
            self._store(instruction.result, "rax")
            return
        if op in self.BINARY_OPS:
            self._emit_binary(instruction)
            return
        if op in {"neg", "not", "bit_not", "deref", "addr"}:
            self._emit_unary(instruction)
            return
        if op == "array_addr":
            self._array_address(instruction.arg1, instruction.arg2)
            self._store(instruction.result, "rax")
            return
        if op == "array_load":
            self._array_address(instruction.arg1, instruction.arg2)
            self.emit("mov rax, qword ptr [rax]")
            self._store(instruction.result, "rax")
            return
        if op == "array_store":
            self._array_address(instruction.result, instruction.arg1)
            self.emit("push rax")
            self._load(instruction.arg2, "rbx")
            self.emit("pop rax")
            self.emit("mov qword ptr [rax], rbx")
            return
        if op == "member_addr":
            self._member_address(instruction.arg1, instruction.arg2)
            self._store(instruction.result, "rax")
            return
        if op == "member_load":
            self._member_address(instruction.arg1, instruction.arg2)
            self.emit("mov rax, qword ptr [rax]")
            self._store(instruction.result, "rax")
            return
        if op == "member_store":
            self._member_address(instruction.arg1, instruction.arg2)
            self.emit("push rax")
            self._load(instruction.result, "rbx")
            self.emit("pop rax")
            self.emit("mov qword ptr [rax], rbx")
            return
        if op == "store":
            self._load(instruction.result, "rax")
            self.emit("push rax")
            self._load(instruction.arg1, "rbx")
            self.emit("pop rax")
            self.emit("mov qword ptr [rax], rbx")
            return
        if op == "arg":
            self.pending_args.append(instruction.arg1)
            return
        if op == "call":
            for arg in reversed(self.pending_args):
                if arg in self.array_symbols:
                    self._address_of(arg, "rax")
                else:
                    self._load(arg, "rax")
                self.emit("push rax")
            self.emit(f"call {instruction.arg1}")
            if instruction.arg2:
                self.emit(f"add rsp, {int(instruction.arg2) * 8}")
            self.pending_args = []
            if instruction.result:
                self._store(instruction.result, "rax")

    def _emit_binary(self, instruction: TACInstruction):
        self._load(instruction.arg1, "rax")
        self._load(instruction.arg2, "rbx")
        op = instruction.op
        if op == "+":
            self.emit("add rax, rbx")
        elif op == "-":
            self.emit("sub rax, rbx")
        elif op == "*":
            self.emit("imul rax, rbx")
        elif op in {"/", "%"}:
            self.emit("cqo")
            self.emit("idiv rbx")
            if op == "%":
                self.emit("mov rax, rdx")
        elif op in {"==", "!=", "<", ">", "<=", ">="}:
            suffix = {"==": "sete", "!=": "setne", "<": "setl", ">": "setg", "<=": "setle", ">=": "setge"}[op]
            self.emit("cmp rax, rbx")
            self.emit(f"{suffix} al")
            self.emit("movzx rax, al")
        elif op == "&&":
            self.emit("cmp rax, 0")
            self.emit("setne al")
            self.emit("cmp rbx, 0")
            self.emit("setne bl")
            self.emit("and al, bl")
            self.emit("movzx rax, al")
        elif op == "||":
            self.emit("cmp rax, 0")
            self.emit("setne al")
            self.emit("cmp rbx, 0")
            self.emit("setne bl")
            self.emit("or al, bl")
            self.emit("movzx rax, al")
        elif op == "<<":
            self.emit("mov rcx, rbx")
            self.emit("shl rax, cl")
        elif op == ">>":
            self.emit("mov rcx, rbx")
            self.emit("sar rax, cl")
        elif op == "&":
            self.emit("and rax, rbx")
        elif op == "|":
            self.emit("or rax, rbx")
        elif op == "^":
            self.emit("xor rax, rbx")
        self._store(instruction.result, "rax")

    def _emit_unary(self, instruction: TACInstruction):
        if instruction.op == "addr":
            self._address_of(instruction.arg1, "rax")
        else:
            self._load(instruction.arg1, "rax")
            if instruction.op == "neg":
                self.emit("neg rax")
            elif instruction.op == "not":
                self.emit("cmp rax, 0")
                self.emit("sete al")
                self.emit("movzx rax, al")
            elif instruction.op == "bit_not":
                self.emit("not rax")
            elif instruction.op == "deref":
                self.emit("mov rax, qword ptr [rax]")
        self._store(instruction.result, "rax")

    def _array_address(self, name: str, index: Any):
        if name in self.param_symbols:
            self._load(name, "rax")
        else:
            self._address_of(name, "rax")
        self.emit("push rax")
        self._load(index, "rbx")
        self.emit("imul rbx, 8")
        self.emit("pop rax")
        self.emit("add rax, rbx")

    def _member_address(self, name: str, slot_offset: Any):
        if name in self.param_symbols:
            self._load(name, "rax")
        else:
            self._address_of(name, "rax")
        offset = int(slot_offset or 0) * 8
        if offset:
            self.emit(f"add rax, {offset}")

    def _address_of(self, symbol: str, register: str):
        offset = self.offsets[symbol]
        self.emit(f"lea {register}, [rbp-{offset}]")

    def _load(self, value: Any, register: str):
        if self._is_immediate(value):
            self.emit(f"mov {register}, {value}")
        else:
            offset = self.offsets[value]
            self.emit(f"mov {register}, qword ptr [rbp-{offset}]")

    def _store(self, symbol: str, register: str):
        offset = self.offsets[symbol]
        self.emit(f"mov qword ptr [rbp-{offset}], {register}")

    def _is_immediate(self, value: Any) -> bool:
        if value is None:
            return False
        text = str(value)
        return text.lstrip("-").isdigit()

    def _is_symbol(self, value: Any) -> bool:
        return isinstance(value, str) and not self._is_immediate(value)

    def _align(self, value: int, alignment: int) -> int:
        if value == 0:
            return 0
        return ((value + alignment - 1) // alignment) * alignment

    def emit(self, line: str):
        self.code.append("    " * self.indent + line)


class TACRiscVAssemblyGenerator:
    """Translate TAC to RV64G-style RISC-V assembly."""

    BINARY_OPS: Set[str] = TACAssemblyGenerator.BINARY_OPS
    ARG_REGISTERS = ["a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7"]

    def __init__(self):
        self.code: List[str] = []
        self.indent = 0
        self.current_function: Optional[str] = None
        self.function_epilogue: Optional[str] = None
        self.offsets: Dict[str, int] = {}
        self.array_symbols: Set[str] = set()
        self.param_symbols: Set[str] = set()
        self.frame_size = 0
        self.pending_args: List[Any] = []

    def generate(self, instructions: List[TACInstruction]) -> str:
        self.code = []
        self.emit(".text")
        self.emit(".globl main")
        self.emit("")

        functions = self._split_functions(instructions)
        for name, body in functions:
            self._prepare_frame(body)
            self._emit_function(name, body)
        return "\n".join(self.code)

    def _split_functions(self, instructions: List[TACInstruction]) -> List[tuple]:
        functions = []
        current_name = None
        current_body = []
        for instruction in instructions:
            if instruction.op == "function":
                current_name = instruction.result
                current_body = []
            elif instruction.op == "end_function":
                functions.append((current_name, current_body))
                current_name = None
                current_body = []
            elif current_name is not None:
                current_body.append(instruction)
        return functions

    def _prepare_frame(self, body: List[TACInstruction]):
        self.offsets = {}
        self.array_symbols = set()
        self.param_symbols = set()
        offset = 16
        for instruction in body:
            if instruction.op == "param_decl":
                self.offsets[instruction.result] = offset
                self.param_symbols.add(instruction.result)
                offset += 8
            elif instruction.op == "declare":
                size = int(instruction.arg1 or 1)
                self.offsets[instruction.result] = offset
                if size > 1:
                    self.array_symbols.add(instruction.result)
                offset += size * 8
            elif instruction.result and self._is_symbol(instruction.result):
                if instruction.result not in self.offsets:
                    self.offsets[instruction.result] = offset
                    offset += 8
        self.frame_size = self._align(offset, 16)

    def _emit_function(self, name: str, body: List[TACInstruction]):
        self.current_function = name
        self.function_epilogue = f".L_{name}_return"
        self.emit(f"{name}:")
        self.indent += 1
        self.emit(f"addi sp, sp, -{self.frame_size}")
        self.emit(f"sd ra, {self.frame_size - 8}(sp)")
        self.emit(f"sd s0, {self.frame_size - 16}(sp)")
        self.emit(f"addi s0, sp, {self.frame_size}")

        for index, instruction in enumerate(i for i in body if i.op == "param_decl"):
            if index < len(self.ARG_REGISTERS):
                self._store(instruction.result, self.ARG_REGISTERS[index])
            else:
                stack_offset = 8 * (index - len(self.ARG_REGISTERS))
                self.emit(f"ld t0, {stack_offset}(s0)")
                self._store(instruction.result, "t0")

        for instruction in body:
            if instruction.op != "param_decl":
                self._emit_instruction(instruction)

        self.emit(f"{self.function_epilogue}:")
        self.emit(f"ld ra, {self.frame_size - 8}(sp)")
        self.emit(f"ld s0, {self.frame_size - 16}(sp)")
        self.emit(f"addi sp, sp, {self.frame_size}")
        self.emit("ret")
        self.indent -= 1
        self.emit("")
        self.current_function = None
        self.function_epilogue = None
        self.pending_args = []

    def _emit_instruction(self, instruction: TACInstruction):
        op = instruction.op
        if op == "declare":
            return
        if op == "label":
            self.indent -= 1
            self.emit(f"{instruction.result}:")
            self.indent += 1
            return
        if op == "goto":
            self.emit(f"j {instruction.result}")
            return
        if op == "if_false":
            self._load(instruction.arg1, "t0")
            self.emit(f"beqz t0, {instruction.result}")
            return
        if op == "return":
            if instruction.arg1 is not None:
                self._load(instruction.arg1, "a0")
            self.emit(f"j {self.function_epilogue}")
            return
        if op == "assign":
            self._load(instruction.arg1, "t0")
            self._store(instruction.result, "t0")
            return
        if op in self.BINARY_OPS:
            self._emit_binary(instruction)
            return
        if op in {"neg", "not", "bit_not", "deref", "addr"}:
            self._emit_unary(instruction)
            return
        if op == "array_addr":
            self._array_address(instruction.arg1, instruction.arg2)
            self._store(instruction.result, "t0")
            return
        if op == "array_load":
            self._array_address(instruction.arg1, instruction.arg2)
            self.emit("ld t0, 0(t0)")
            self._store(instruction.result, "t0")
            return
        if op == "array_store":
            self._array_address(instruction.result, instruction.arg1)
            self._load(instruction.arg2, "t1")
            self.emit("sd t1, 0(t0)")
            return
        if op == "member_addr":
            self._member_address(instruction.arg1, instruction.arg2)
            self._store(instruction.result, "t0")
            return
        if op == "member_load":
            self._member_address(instruction.arg1, instruction.arg2)
            self.emit("ld t0, 0(t0)")
            self._store(instruction.result, "t0")
            return
        if op == "member_store":
            self._member_address(instruction.arg1, instruction.arg2)
            self._load(instruction.result, "t1")
            self.emit("sd t1, 0(t0)")
            return
        if op == "store":
            self._load(instruction.result, "t0")
            self._load(instruction.arg1, "t1")
            self.emit("sd t1, 0(t0)")
            return
        if op == "arg":
            self.pending_args.append(instruction.arg1)
            return
        if op == "call":
            stack_args = max(0, len(self.pending_args) - len(self.ARG_REGISTERS))
            stack_size = self._align(stack_args * 8, 16)
            if stack_size:
                self.emit(f"addi sp, sp, -{stack_size}")
            for index, arg in enumerate(self.pending_args):
                if arg in self.array_symbols:
                    self._address_of(arg, "t0")
                else:
                    self._load(arg, "t0")
                if index < len(self.ARG_REGISTERS):
                    self.emit(f"mv {self.ARG_REGISTERS[index]}, t0")
                else:
                    self.emit(f"sd t0, {(index - len(self.ARG_REGISTERS)) * 8}(sp)")
            self.emit(f"call {instruction.arg1}")
            if stack_size:
                self.emit(f"addi sp, sp, {stack_size}")
            self.pending_args = []
            if instruction.result:
                self._store(instruction.result, "a0")

    def _emit_binary(self, instruction: TACInstruction):
        self._load(instruction.arg1, "t0")
        self._load(instruction.arg2, "t1")
        op = instruction.op
        if op == "+":
            self.emit("add t0, t0, t1")
        elif op == "-":
            self.emit("sub t0, t0, t1")
        elif op == "*":
            self.emit("mul t0, t0, t1")
        elif op == "/":
            self.emit("div t0, t0, t1")
        elif op == "%":
            self.emit("rem t0, t0, t1")
        elif op == "==":
            self.emit("sub t0, t0, t1")
            self.emit("seqz t0, t0")
        elif op == "!=":
            self.emit("sub t0, t0, t1")
            self.emit("snez t0, t0")
        elif op == "<":
            self.emit("slt t0, t0, t1")
        elif op == ">":
            self.emit("slt t0, t1, t0")
        elif op == "<=":
            self.emit("slt t0, t1, t0")
            self.emit("xori t0, t0, 1")
        elif op == ">=":
            self.emit("slt t0, t0, t1")
            self.emit("xori t0, t0, 1")
        elif op == "&&":
            self.emit("snez t0, t0")
            self.emit("snez t1, t1")
            self.emit("and t0, t0, t1")
        elif op == "||":
            self.emit("or t0, t0, t1")
            self.emit("snez t0, t0")
        elif op == "<<":
            self.emit("sll t0, t0, t1")
        elif op == ">>":
            self.emit("sra t0, t0, t1")
        elif op == "&":
            self.emit("and t0, t0, t1")
        elif op == "|":
            self.emit("or t0, t0, t1")
        elif op == "^":
            self.emit("xor t0, t0, t1")
        self._store(instruction.result, "t0")

    def _emit_unary(self, instruction: TACInstruction):
        if instruction.op == "addr":
            self._address_of(instruction.arg1, "t0")
        else:
            self._load(instruction.arg1, "t0")
            if instruction.op == "neg":
                self.emit("neg t0, t0")
            elif instruction.op == "not":
                self.emit("seqz t0, t0")
            elif instruction.op == "bit_not":
                self.emit("not t0, t0")
            elif instruction.op == "deref":
                self.emit("ld t0, 0(t0)")
        self._store(instruction.result, "t0")

    def _array_address(self, name: str, index: Any):
        if name in self.param_symbols:
            self._load(name, "t0")
        else:
            self._address_of(name, "t0")
        self._load(index, "t1")
        self.emit("slli t1, t1, 3")
        self.emit("add t0, t0, t1")

    def _member_address(self, name: str, slot_offset: Any):
        if name in self.param_symbols:
            self._load(name, "t0")
        else:
            self._address_of(name, "t0")
        offset = int(slot_offset or 0) * 8
        if offset:
            self.emit(f"addi t0, t0, {offset}")

    def _address_of(self, symbol: str, register: str):
        offset = self.offsets[symbol]
        self.emit(f"addi {register}, s0, -{offset}")

    def _load(self, value: Any, register: str):
        if self._is_immediate(value):
            self.emit(f"li {register}, {value}")
        else:
            offset = self.offsets[value]
            self.emit(f"ld {register}, -{offset}(s0)")

    def _store(self, symbol: str, register: str):
        offset = self.offsets[symbol]
        self.emit(f"sd {register}, -{offset}(s0)")

    def _is_immediate(self, value: Any) -> bool:
        if value is None:
            return False
        text = str(value)
        return text.lstrip("-").isdigit()

    def _is_symbol(self, value: Any) -> bool:
        return isinstance(value, str) and not self._is_immediate(value)

    def _align(self, value: int, alignment: int) -> int:
        if value == 0:
            return 0
        return ((value + alignment - 1) // alignment) * alignment

    def emit(self, line: str):
        self.code.append("    " * self.indent + line)
