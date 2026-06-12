from collections import Counter
from typing import Any, Dict, List, Optional

from .core import ASTNode
from .tac import TACInstruction


class Optimizer:
    def __init__(self):
        self.optimizations_applied = []

    def optimize(self, ast: ASTNode) -> ASTNode:
        ast = self.constant_folding(ast)
        ast = self.dead_code_elimination(ast)
        return ast

    def constant_folding(self, node: ASTNode) -> ASTNode:
        if node is None:
            return None

        if node.type == "variable_declarations":
            node.children = [self.constant_folding(c) for c in node.children]
            return node

        if node.type == "binary_expression":
            node.children = [self.constant_folding(c) for c in node.children]

            if (
                node.children[0]
                and node.children[0].type == "integer_literal"
                and node.children[1]
                and node.children[1].type == "integer_literal"
            ):
                left_val = node.children[0].value["value"]
                right_val = node.children[1].value["value"]
                op = node.value["operator"]

                try:
                    result = self._evaluate_binary(op, left_val, right_val)
                    if result is None:
                        return node

                    self.optimizations_applied.append(
                        f"AST 常量折叠: {left_val} {op} {right_val} = {result}"
                    )
                    return ASTNode("integer_literal", [], {"value": result}, node.line, node.column)
                except Exception:
                    return node

        node.children = [self.constant_folding(c) for c in node.children]
        return node

    def dead_code_elimination(self, node: ASTNode) -> ASTNode:
        return node

    def _evaluate_binary(self, op: str, left: int, right: int) -> Optional[int]:
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/" and right != 0:
            return left // right
        if op == "%" and right != 0:
            return left % right
        if op == "==":
            return int(left == right)
        if op == "!=":
            return int(left != right)
        if op == "<":
            return int(left < right)
        if op == ">":
            return int(left > right)
        if op == "<=":
            return int(left <= right)
        if op == ">=":
            return int(left >= right)
        if op == "&&":
            return int(bool(left) and bool(right))
        if op == "||":
            return int(bool(left) or bool(right))
        if op == "<<":
            return left << right
        if op == ">>":
            return left >> right
        if op == "&":
            return left & right
        if op == "|":
            return left | right
        if op == "^":
            return left ^ right
        return None


class TACOptimizer:
    """Simple local optimizer for three-address code."""

    BINARY_OPS = {
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
    UNARY_OPS = {"neg", "not", "bit_not"}

    def __init__(self):
        self.optimizations_applied: List[str] = []

    def optimize(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        optimized = [self._copy_instruction(instruction) for instruction in instructions]
        self._function_summaries = self._build_function_summaries(optimized)
        optimized = self._constant_propagation_and_folding(optimized)
        optimized = self._fold_never_entered_loops(optimized)
        optimized = self._constant_propagation_and_folding(optimized)
        optimized = self._simplify_constant_branches(optimized)
        optimized = self._remove_unreachable_code(optimized)
        optimized = self._remove_redundant_jumps(optimized)
        optimized = self._constant_propagation_and_folding(optimized)
        optimized = self._fold_never_entered_loops(optimized)
        optimized = self._constant_propagation_and_folding(optimized)
        optimized = self._simplify_constant_branches(optimized)
        optimized = self._remove_unreachable_code(optimized)
        optimized = self._remove_redundant_jumps(optimized)
        optimized = self._remove_unused_temporaries(optimized)
        return optimized

    def _constant_propagation_and_folding(
        self, instructions: List[TACInstruction]
    ) -> List[TACInstruction]:
        constants: Dict[str, str] = {}
        optimized: List[TACInstruction] = []
        pending_args: List[str] = []

        for instruction in instructions:
            current = self._copy_instruction(instruction)
            self._replace_constant_operands(current, constants)
            folded = self._fold_instruction(current)
            if folded:
                current = folded

            if current.op == "arg":
                pending_args.append(current.arg1)
            elif current.op == "call":
                folded_call = self._fold_constant_call(current, pending_args)
                pending_args = []
                if folded_call:
                    current = folded_call
            elif current.op not in {"declare", "param_decl"}:
                pending_args = []

            if self._is_barrier(current):
                constants.clear()

            self._update_constants(current, constants)
            optimized.append(current)

        return optimized

    def _replace_constant_operands(
        self, instruction: TACInstruction, constants: Dict[str, str]
    ):
        if instruction.op in self.BINARY_OPS or instruction.op in self.UNARY_OPS:
            instruction.arg1 = constants.get(instruction.arg1, instruction.arg1)
            instruction.arg2 = constants.get(instruction.arg2, instruction.arg2)
        elif instruction.op in {"assign", "if_false", "return", "arg"}:
            instruction.arg1 = constants.get(instruction.arg1, instruction.arg1)
        elif instruction.op == "array_load":
            instruction.arg2 = constants.get(instruction.arg2, instruction.arg2)
        elif instruction.op == "array_store":
            instruction.arg1 = constants.get(instruction.arg1, instruction.arg1)
            instruction.arg2 = constants.get(instruction.arg2, instruction.arg2)
        elif instruction.op == "member_store":
            instruction.result = constants.get(instruction.result, instruction.result)
        elif instruction.op == "store":
            instruction.arg1 = constants.get(instruction.arg1, instruction.arg1)

    def _fold_constant_call(
        self, instruction: TACInstruction, pending_args: List[Any]
    ) -> Optional[TACInstruction]:
        if not instruction.result or not hasattr(self, "_function_summaries"):
            return None
        if not all(self._is_immediate(arg) for arg in pending_args):
            return None

        summary = self._function_summaries.get(instruction.arg1)
        if not summary or len(summary["params"]) != len(pending_args):
            return None

        value = self._evaluate_function_summary(summary, pending_args)
        if value is None:
            return None

        self.optimizations_applied.append(
            f"TAC 常量函数求值: {instruction.result} = call {instruction.arg1}({', '.join(map(str, pending_args))}) -> {value}"
        )
        return TACInstruction("assign", str(value), result=instruction.result)

    def _fold_instruction(self, instruction: TACInstruction) -> Optional[TACInstruction]:
        if instruction.op in self.BINARY_OPS:
            algebraic = self._simplify_algebraic(instruction)
            if algebraic:
                return algebraic

            left = self._as_int(instruction.arg1)
            right = self._as_int(instruction.arg2)
            if left is None or right is None:
                return None
            value = self._evaluate_binary(instruction.op, left, right)
            if value is None:
                return None
            self.optimizations_applied.append(
                f"TAC 常量折叠: {instruction.result} = {instruction.arg1} {instruction.op} {instruction.arg2} -> {value}"
            )
            return TACInstruction("assign", str(value), result=instruction.result)

        if instruction.op in self.UNARY_OPS:
            value = self._as_int(instruction.arg1)
            if value is None:
                return None
            result = self._evaluate_unary(instruction.op, value)
            self.optimizations_applied.append(
                f"TAC 常量折叠: {instruction.result} = {instruction.op} {instruction.arg1} -> {result}"
            )
            return TACInstruction("assign", str(result), result=instruction.result)

        return None

    def _simplify_constant_branches(
        self, instructions: List[TACInstruction]
    ) -> List[TACInstruction]:
        optimized: List[TACInstruction] = []
        removed = 0
        converted = 0

        for instruction in instructions:
            if instruction.op == "if_false":
                value = self._as_int(instruction.arg1)
                if value is None:
                    optimized.append(instruction)
                    continue
                if value == 0:
                    optimized.append(TACInstruction("goto", result=instruction.result))
                    converted += 1
                else:
                    removed += 1
                continue
            optimized.append(instruction)

        if removed:
            self.optimizations_applied.append(f"TAC 恒真分支删除: 移除 {removed} 条条件跳转")
        if converted:
            self.optimizations_applied.append(f"TAC 恒假分支简化: 转换 {converted} 条条件跳转")
        return optimized

    def _fold_never_entered_loops(
        self, instructions: List[TACInstruction]
    ) -> List[TACInstruction]:
        optimized = [self._copy_instruction(instruction) for instruction in instructions]
        constants: Dict[str, str] = {}
        folded = 0

        for index, instruction in enumerate(optimized):
            if instruction.op in {"function", "end_function"}:
                constants.clear()
                continue

            if instruction.op == "label":
                if self._try_fold_loop_entry_condition(optimized, index, constants):
                    folded += 1
                continue

            self._update_simple_linear_constants(instruction, constants)

        if folded:
            self.optimizations_applied.append(f"TAC 空循环条件折叠: 折叠 {folded} 个首次不进入的循环")
        return optimized

    def _try_fold_loop_entry_condition(
        self,
        instructions: List[TACInstruction],
        label_index: int,
        constants: Dict[str, str],
    ) -> bool:
        if label_index + 2 >= len(instructions):
            return False

        label = instructions[label_index].result
        condition = self._copy_instruction(instructions[label_index + 1])
        branch = instructions[label_index + 2]
        if condition.op not in self.BINARY_OPS and condition.op not in self.UNARY_OPS:
            return False
        if branch.op != "if_false" or branch.arg1 != condition.result:
            return False
        if not self._has_loop_back_edge(instructions, label_index + 3, label, branch.result):
            return False

        self._replace_constant_operands(condition, constants)
        folded = self._fold_instruction(condition)
        if not folded or folded.op != "assign" or self._as_int(folded.arg1) != 0:
            return False

        instructions[label_index + 1] = folded
        return True

    def _has_loop_back_edge(
        self,
        instructions: List[TACInstruction],
        start_index: int,
        loop_label: str,
        exit_label: str,
    ) -> bool:
        for instruction in instructions[start_index:]:
            if instruction.op == "label" and instruction.result == exit_label:
                return False
            if instruction.op == "goto" and instruction.result == loop_label:
                return True
        return False

    def _update_simple_linear_constants(
        self, instruction: TACInstruction, constants: Dict[str, str]
    ):
        if instruction.op == "assign":
            if instruction.result and self._is_immediate(instruction.arg1):
                constants[instruction.result] = str(instruction.arg1)
            elif instruction.result:
                constants.pop(instruction.result, None)
        elif instruction.op in self.BINARY_OPS or instruction.op in self.UNARY_OPS:
            current = self._copy_instruction(instruction)
            self._replace_constant_operands(current, constants)
            folded = self._fold_instruction(current)
            if folded and folded.op == "assign" and self._is_immediate(folded.arg1):
                constants[folded.result] = str(folded.arg1)
            elif instruction.result:
                constants.pop(instruction.result, None)
        elif self._is_barrier(instruction) or instruction.op == "return":
            if instruction.result and self._is_symbol(instruction.result):
                constants.pop(instruction.result, None)

    def _simplify_algebraic(self, instruction: TACInstruction) -> Optional[TACInstruction]:
        op = instruction.op
        left = instruction.arg1
        right = instruction.arg2
        result = instruction.result

        replacement = None
        if op == "+" and self._is_zero(right):
            replacement = left
        elif op == "+" and self._is_zero(left):
            replacement = right
        elif op == "-" and self._is_zero(right):
            replacement = left
        elif op == "*" and self._is_one(right):
            replacement = left
        elif op == "*" and self._is_one(left):
            replacement = right
        elif op == "*" and (self._is_zero(left) or self._is_zero(right)):
            replacement = "0"
        elif op == "/" and self._is_one(right):
            replacement = left
        elif op == "%" and self._is_one(right):
            replacement = "0"
        elif op == "&&" and (self._is_zero(left) or self._is_zero(right)):
            replacement = "0"
        elif op == "||" and self._is_zero(right):
            replacement = left
        elif op == "||" and self._is_zero(left):
            replacement = right

        if replacement is None:
            return None

        self.optimizations_applied.append(
            f"TAC 代数化简: {result} = {left} {op} {right} -> {replacement}"
        )
        return TACInstruction("assign", replacement, result=result)

    def _update_constants(self, instruction: TACInstruction, constants: Dict[str, str]):
        if instruction.result and self._is_symbol(instruction.result):
            constants.pop(instruction.result, None)

        if instruction.op == "assign" and self._is_immediate(instruction.arg1):
            constants[instruction.result] = str(instruction.arg1)
        elif instruction.op not in {"label", "goto", "if_false", "return", "arg"}:
            if instruction.result and self._is_symbol(instruction.result):
                constants.pop(instruction.result, None)

    def _remove_unreachable_code(
        self, instructions: List[TACInstruction]
    ) -> List[TACInstruction]:
        if not instructions:
            return instructions

        label_positions = {
            instruction.result: index
            for index, instruction in enumerate(instructions)
            if instruction.op == "label"
        }
        entry_points = {0}
        entry_points.update(
            index for index, instruction in enumerate(instructions) if instruction.op == "function"
        )

        reachable_indexes = set()
        stack = list(entry_points)
        while stack:
            index = stack.pop()
            if index < 0 or index >= len(instructions) or index in reachable_indexes:
                continue
            reachable_indexes.add(index)
            instruction = instructions[index]

            next_indexes = []
            if instruction.op == "goto":
                target = label_positions.get(instruction.result)
                if target is not None:
                    next_indexes.append(target)
            elif instruction.op == "if_false":
                target = label_positions.get(instruction.result)
                if target is not None:
                    next_indexes.append(target)
                next_indexes.append(index + 1)
            elif instruction.op in {"return", "end_function"}:
                pass
            else:
                next_indexes.append(index + 1)

            stack.extend(next_indexes)

        optimized = []
        removed = 0
        for index, instruction in enumerate(instructions):
            if index in reachable_indexes or instruction.op in {"function", "end_function"}:
                optimized.append(instruction)
            else:
                removed += 1

        if removed:
            self.optimizations_applied.append(f"TAC 不可达代码删除: 移除 {removed} 条指令")
        return optimized

    def _remove_redundant_jumps(
        self, instructions: List[TACInstruction]
    ) -> List[TACInstruction]:
        optimized: List[TACInstruction] = []
        removed = 0

        for index, instruction in enumerate(instructions):
            if instruction.op == "goto":
                next_index = index + 1
                while next_index < len(instructions) and instructions[next_index].op == "label":
                    if instructions[next_index].result == instruction.result:
                        removed += 1
                        break
                    next_index += 1
                else:
                    optimized.append(instruction)
                continue
            optimized.append(instruction)

        if removed:
            self.optimizations_applied.append(f"TAC 冗余跳转删除: 移除 {removed} 条指令")
        return optimized

    def _remove_unused_temporaries(
        self, instructions: List[TACInstruction]
    ) -> List[TACInstruction]:
        use_counts = self._count_uses(instructions)
        optimized: List[TACInstruction] = []
        removed = 0

        for instruction in instructions:
            if (
                instruction.result
                and self._is_temp(instruction.result)
                and use_counts[instruction.result] == 0
                and self._is_removable_definition(instruction)
            ):
                removed += 1
                continue
            optimized.append(instruction)

        if removed:
            self.optimizations_applied.append(f"TAC 无用临时变量删除: 移除 {removed} 条指令")
        return optimized

    def _count_uses(self, instructions: List[TACInstruction]) -> Counter:
        counts: Counter = Counter()
        for instruction in instructions:
            for value in self._used_values(instruction):
                if self._is_symbol(value):
                    counts[value] += 1
        return counts

    def _used_values(self, instruction: TACInstruction) -> List[Any]:
        if instruction.op in self.BINARY_OPS:
            return [instruction.arg1, instruction.arg2]
        if instruction.op in self.UNARY_OPS or instruction.op in {"assign", "if_false", "return", "arg"}:
            return [instruction.arg1]
        if instruction.op == "array_load":
            return [instruction.arg2]
        if instruction.op == "array_store":
            return [instruction.arg1, instruction.arg2]
        if instruction.op == "member_store":
            return [instruction.result]
        if instruction.op == "store":
            return [instruction.arg1, instruction.result]
        if instruction.op == "call":
            return []
        return []

    def _is_removable_definition(self, instruction: TACInstruction) -> bool:
        return (
            instruction.op in self.BINARY_OPS
            or instruction.op in self.UNARY_OPS
            or instruction.op == "assign"
        )

    def _is_barrier(self, instruction: TACInstruction) -> bool:
        return instruction.op in {"label", "goto", "if_false", "call", "store", "array_store", "member_store"}

    def _build_function_summaries(self, instructions: List[TACInstruction]) -> Dict[str, Dict[str, Any]]:
        summaries: Dict[str, Dict[str, Any]] = {}
        current_name = None
        current_body: List[TACInstruction] = []

        for instruction in instructions:
            if instruction.op == "function":
                current_name = instruction.result
                current_body = []
            elif instruction.op == "end_function":
                if current_name:
                    summary = self._build_function_summary(current_body)
                    if summary:
                        summaries[current_name] = summary
                current_name = None
                current_body = []
            elif current_name is not None:
                current_body.append(instruction)

        return summaries

    def _build_function_summary(
        self, body: List[TACInstruction]
    ) -> Optional[Dict[str, Any]]:
        unsupported_ops = {
            "label",
            "goto",
            "if_false",
            "arg",
            "call",
            "array_load",
            "array_store",
            "member_addr",
            "member_load",
            "member_store",
            "store",
            "addr",
            "deref",
            "array_addr",
        }
        params = [instruction.result for instruction in body if instruction.op == "param_decl"]
        return_count = sum(1 for instruction in body if instruction.op == "return")
        if return_count != 1:
            return None
        if any(instruction.op in unsupported_ops for instruction in body):
            return None

        return {"params": params, "body": [self._copy_instruction(instruction) for instruction in body]}

    def _evaluate_function_summary(
        self, summary: Dict[str, Any], args: List[Any]
    ) -> Optional[int]:
        env: Dict[str, str] = {
            param: str(arg) for param, arg in zip(summary["params"], args)
        }

        for instruction in summary["body"]:
            current = self._copy_instruction(instruction)
            self._replace_constant_operands(current, env)
            folded = self._fold_instruction(current)
            if folded:
                current = folded

            if current.op in {"param_decl", "declare"}:
                continue
            if current.op == "assign":
                if not current.result or not self._is_immediate(current.arg1):
                    return None
                env[current.result] = str(current.arg1)
                continue
            if current.op == "return":
                value = env.get(current.arg1, current.arg1)
                return self._as_int(value)
            return None

        return None

    def _evaluate_binary(self, op: str, left: int, right: int) -> Optional[int]:
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/" and right != 0:
            return left // right
        if op == "%" and right != 0:
            return left % right
        if op == "==":
            return int(left == right)
        if op == "!=":
            return int(left != right)
        if op == "<":
            return int(left < right)
        if op == ">":
            return int(left > right)
        if op == "<=":
            return int(left <= right)
        if op == ">=":
            return int(left >= right)
        if op == "&&":
            return int(bool(left) and bool(right))
        if op == "||":
            return int(bool(left) or bool(right))
        if op == "<<":
            return left << right
        if op == ">>":
            return left >> right
        if op == "&":
            return left & right
        if op == "|":
            return left | right
        if op == "^":
            return left ^ right
        return None

    def _evaluate_unary(self, op: str, value: int) -> int:
        if op == "neg":
            return -value
        if op == "not":
            return int(not value)
        if op == "bit_not":
            return ~value
        return value

    def _copy_instruction(self, instruction: TACInstruction) -> TACInstruction:
        return TACInstruction(instruction.op, instruction.arg1, instruction.arg2, instruction.result)

    def _as_int(self, value: Any) -> Optional[int]:
        if not self._is_immediate(value):
            return None
        return int(str(value))

    def _is_zero(self, value: Any) -> bool:
        return self._as_int(value) == 0

    def _is_one(self, value: Any) -> bool:
        return self._as_int(value) == 1

    def _is_immediate(self, value: Any) -> bool:
        if value is None:
            return False
        return str(value).lstrip("-").isdigit()

    def _is_symbol(self, value: Any) -> bool:
        return isinstance(value, str) and not self._is_immediate(value)

    def _is_temp(self, value: Any) -> bool:
        return isinstance(value, str) and value.startswith("t") and value[1:].isdigit()
