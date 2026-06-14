from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .core import ASTNode
from .tac import TACInstruction


@dataclass
class _DAGNode:
    id: int
    op: Optional[str] = None
    left: Optional["_DAGNode"] = None
    right: Optional["_DAGNode"] = None
    const_value: Optional[str] = None
    fixed_label: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    label_set: Set[str] = field(default_factory=set)

    def add_label(self, label: str):
        if label not in self.label_set:
            self.labels.append(label)
            self.label_set.add(label)

    def remove_label(self, label: str):
        if label in self.label_set:
            self.label_set.remove(label)
            self.labels = [current for current in self.labels if current != label]


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

    @staticmethod
    def _parse_int(value: Any) -> int:
        if isinstance(value, int):
            return value
        text = str(value).strip()
        if text.startswith(('0x', '0X')):
            return int(text, 16)
        if text.startswith(('0b', '0B')):
            return int(text, 2)
        if text.startswith(('0o', '0O')):
            return int(text, 8)
        return int(text, 10)

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

    MAX_OPTIMIZATION_PASSES = 8

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
        for _ in range(self.MAX_OPTIMIZATION_PASSES):
            before = self._instructions_signature(optimized)
            self._function_summaries = self._build_function_summaries(optimized)
            optimized = self._constant_propagation_and_folding(optimized)
            optimized = self._eliminate_common_subexpressions(optimized)
            optimized = self._fold_never_entered_loops(optimized)
            optimized = self._simplify_constant_branches(optimized)
            optimized = self._remove_unreachable_code(optimized)
            optimized = self._remove_redundant_jumps(optimized)
            if self._instructions_signature(optimized) == before:
                break

        for _ in range(self.MAX_OPTIMIZATION_PASSES):
            before = self._instructions_signature(optimized)
            optimized = self._remove_unused_temporaries(optimized)
            if self._instructions_signature(optimized) == before:
                break
        return optimized

    def _instructions_signature(self, instructions: List[TACInstruction]) -> tuple:
        return tuple(
            (instruction.op, instruction.arg1, instruction.arg2, instruction.result)
            for instruction in instructions
        )

    def _eliminate_common_subexpressions(
        self, instructions: List[TACInstruction]
    ) -> List[TACInstruction]:
        optimized: List[TACInstruction] = []
        removed = 0

        for block in self._split_basic_blocks(instructions):
            block_optimized, block_removed = self._eliminate_common_subexpressions_in_block(
                block["instructions"]
            )
            optimized.extend(block_optimized)
            removed += block_removed

        if removed:
            self.optimizations_applied.append(f"TAC 块内公共子表达式删除: 消除 {removed} 条指令")
        return optimized

    def analyze_basic_blocks(self, instructions: List[TACInstruction]) -> Dict[str, Any]:
        blocks = self._split_basic_blocks(instructions)
        unreachable_indexes = sorted(
            index
            for block in blocks
            if not block["reachable"]
            for index in range(block["start"], block["end"] + 1)
            if instructions[index].op not in {"function", "end_function"}
        )
        return {
            "blocks": [self._block_to_dict(block) for block in blocks],
            "entry_indexes": [block["start"] for block in blocks],
            "unreachable_indexes": unreachable_indexes,
            "unreachable_count": len(unreachable_indexes),
        }

    def _split_basic_blocks(self, instructions: List[TACInstruction]) -> List[Dict[str, Any]]:
        if not instructions:
            return []

        leaders = {0}
        leader_reasons: Dict[int, Set[str]] = {0: {"程序入口"}}
        label_positions: Dict[str, int] = {}

        for index, instruction in enumerate(instructions):
            if instruction.op == "function":
                self._add_leader(leaders, leader_reasons, index, "函数入口")
            elif instruction.op == "label":
                label_positions[instruction.result] = index
                self._add_leader(leaders, leader_reasons, index, "标号语句")

        for index, instruction in enumerate(instructions):
            if self._is_block_terminator(instruction) and index + 1 < len(instructions):
                self._add_leader(leaders, leader_reasons, index + 1, "转移/停语句后的下一语句")
            if self._is_branch_instruction(instruction) and instruction.result in label_positions:
                self._add_leader(
                    leaders,
                    leader_reasons,
                    label_positions[instruction.result],
                    f"转移目标 {instruction.result}",
                )

        sorted_leaders = sorted(i for i in leaders if 0 <= i < len(instructions))
        reachable_indexes = self._find_reachable_indexes(instructions, label_positions)
        blocks: List[Dict[str, Any]] = []

        for position, start in enumerate(sorted_leaders):
            next_start = sorted_leaders[position + 1] if position + 1 < len(sorted_leaders) else len(instructions)
            end = self._basic_block_end(instructions, start, next_start)
            block_instructions = [
                self._copy_instruction(instruction) for instruction in instructions[start : end + 1]
            ]
            if not block_instructions:
                continue
            blocks.append(
                {
                    "id": len(blocks) + 1,
                    "start": start,
                    "end": end,
                    "instructions": block_instructions,
                    "leader_reasons": sorted(leader_reasons.get(start, [])),
                    "reachable": (
                        any(index in reachable_indexes for index in range(start, end + 1))
                        or all(
                            instruction.op in {"function", "end_function"}
                            for instruction in block_instructions
                        )
                    ),
                }
            )

        start_to_block = {block["start"]: block for block in blocks}
        label_to_block = {
            instructions[block["start"]].result: block["id"]
            for block in blocks
            if instructions[block["start"]].op == "label"
        }
        for index, block in enumerate(blocks):
            block["successors"] = self._block_successors(block, blocks, index, start_to_block, label_to_block)

        return blocks

    def _add_leader(
        self,
        leaders: Set[int],
        leader_reasons: Dict[int, Set[str]],
        index: int,
        reason: str,
    ):
        leaders.add(index)
        leader_reasons.setdefault(index, set()).add(reason)

    def _basic_block_end(
        self,
        instructions: List[TACInstruction],
        start: int,
        next_start: int,
    ) -> int:
        end_limit = min(next_start, len(instructions))
        for index in range(start, end_limit):
            if self._is_block_terminator(instructions[index]):
                return index
        return end_limit - 1

    def _find_reachable_indexes(
        self,
        instructions: List[TACInstruction],
        label_positions: Dict[str, int],
    ) -> Set[int]:
        entry_points = {0}
        entry_points.update(
            index for index, instruction in enumerate(instructions) if instruction.op == "function"
        )

        reachable_indexes: Set[int] = set()
        stack = list(entry_points)
        while stack:
            index = stack.pop()
            if index < 0 or index >= len(instructions) or index in reachable_indexes:
                continue
            reachable_indexes.add(index)
            instruction = instructions[index]

            if instruction.op == "goto":
                target = label_positions.get(instruction.result)
                if target is not None:
                    stack.append(target)
            elif instruction.op == "if_false":
                target = label_positions.get(instruction.result)
                if target is not None:
                    stack.append(target)
                stack.append(index + 1)
            elif instruction.op in {"return", "end_function"}:
                continue
            else:
                stack.append(index + 1)

        return reachable_indexes

    def _block_successors(
        self,
        block: Dict[str, Any],
        blocks: List[Dict[str, Any]],
        block_index: int,
        start_to_block: Dict[int, Dict[str, Any]],
        label_to_block: Dict[str, int],
    ) -> List[int]:
        last = block["instructions"][-1]
        successors: List[int] = []
        if last.op == "goto":
            target = label_to_block.get(last.result)
            if target:
                successors.append(target)
        elif last.op == "if_false":
            target = label_to_block.get(last.result)
            if target:
                successors.append(target)
            next_block = start_to_block.get(block["end"] + 1)
            if next_block:
                successors.append(next_block["id"])
        elif last.op not in {"return", "end_function"} and block_index + 1 < len(blocks):
            successors.append(blocks[block_index + 1]["id"])
        return sorted(set(successors))

    def _block_to_dict(self, block: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": block["id"],
            "start": block["start"],
            "end": block["end"],
            "size": len(block["instructions"]),
            "leader_reasons": block["leader_reasons"],
            "reachable": block["reachable"],
            "successors": block["successors"],
            "instructions": [
                {
                    **instruction.to_dict(),
                    "index": block["start"] + offset,
                }
                for offset, instruction in enumerate(block["instructions"])
            ],
        }

    def _is_branch_instruction(self, instruction: TACInstruction) -> bool:
        return instruction.op in {"goto", "if_false"}

    def _is_block_terminator(self, instruction: TACInstruction) -> bool:
        return instruction.op in {"goto", "if_false", "return", "end_function"}

    def _eliminate_common_subexpressions_in_block(
        self, block: List[TACInstruction]
    ) -> tuple:
        optimized: List[TACInstruction] = []
        current_segment: List[TACInstruction] = []
        removed = 0

        for instruction in block:
            if self._is_dag_instruction(instruction):
                current_segment.append(self._copy_instruction(instruction))
                continue

            if current_segment:
                segment_optimized, segment_removed = self._optimize_dag_segment(current_segment)
                optimized.extend(segment_optimized)
                removed += segment_removed
                current_segment = []
            optimized.append(self._copy_instruction(instruction))

        if current_segment:
            segment_optimized, segment_removed = self._optimize_dag_segment(current_segment)
            optimized.extend(segment_optimized)
            removed += segment_removed

        return optimized, removed

    def _is_dag_instruction(self, instruction: TACInstruction) -> bool:
        return (
            instruction.op == "assign"
            or instruction.op in self.BINARY_OPS
            or instruction.op in self.UNARY_OPS
        ) and instruction.result is not None

    def _optimize_dag_segment(self, instructions: List[TACInstruction]) -> tuple:
        nodes: List[_DAGNode] = []
        symbol_nodes: Dict[str, _DAGNode] = {}
        const_nodes: Dict[str, _DAGNode] = {}
        expression_nodes: Dict[tuple, _DAGNode] = {}
        original_count = sum(1 for instruction in instructions if instruction.op != "assign")

        def new_node(
            op: Optional[str] = None,
            left: Optional[_DAGNode] = None,
            right: Optional[_DAGNode] = None,
            const_value: Optional[str] = None,
            fixed_label: Optional[str] = None,
        ) -> _DAGNode:
            node = _DAGNode(
                id=len(nodes),
                op=op,
                left=left,
                right=right,
                const_value=const_value,
                fixed_label=fixed_label,
            )
            nodes.append(node)
            return node

        def ensure_operand(value: Any) -> tuple:
            key = str(value)
            if self._is_immediate(value):
                node = const_nodes.get(key)
                if node is None:
                    node = new_node(const_value=key, fixed_label=key)
                    const_nodes[key] = node
                return node, False

            node = symbol_nodes.get(key)
            if node is None:
                node = new_node(fixed_label=key)
                symbol_nodes[key] = node
                return node, True
            return node, False

        def bind_symbol(name: Any, node: _DAGNode):
            if not self._is_symbol(name):
                return
            key = str(name)
            old_node = symbol_nodes.get(key)
            if old_node is not None:
                old_node.remove_label(key)
            node.add_label(key)
            symbol_nodes[key] = node

        def expression_key(op: str, left: _DAGNode, right: Optional[_DAGNode]) -> tuple:
            if right is not None and self._is_commutative(op):
                ordered = tuple(sorted((left.id, right.id)))
                return (op, ordered[0], ordered[1])
            return (op, left.id, right.id if right is not None else None)

        for instruction in instructions:
            if instruction.op == "assign":
                node, _ = ensure_operand(instruction.arg1)
                bind_symbol(instruction.result, node)
                continue

            left, _ = ensure_operand(instruction.arg1)
            right = None
            if instruction.op in self.BINARY_OPS:
                right, _ = ensure_operand(instruction.arg2)

            folded_value = self._try_fold_dag_expression(instruction.op, left, right)
            if folded_value is not None:
                node, _ = ensure_operand(folded_value)
                bind_symbol(instruction.result, node)
                continue

            key = expression_key(instruction.op, left, right)
            node = expression_nodes.get(key)
            if node is None:
                node = new_node(op=instruction.op, left=left, right=right)
                expression_nodes[key] = node
            bind_symbol(instruction.result, node)

        emitted: List[TACInstruction] = []
        node_values: Dict[int, str] = {}
        emitted_nodes: Set[int] = set()

        def representative(node: _DAGNode) -> str:
            if node.id in node_values:
                return node_values[node.id]
            if node.op is not None and node.labels:
                value = node.labels[0]
            elif node.const_value is not None:
                value = node.const_value
            elif node.fixed_label is not None:
                value = node.fixed_label
            elif node.labels:
                value = node.labels[0]
            else:
                value = f"_dag{node.id}"
            node_values[node.id] = value
            return value

        def emit_node(node: _DAGNode):
            if node.id in emitted_nodes:
                return
            if node.left:
                emit_node(node.left)
            if node.right:
                emit_node(node.right)
            if node.op is not None:
                target = representative(node)
                left_value = representative(node.left)
                right_value = representative(node.right) if node.right else None
                if node.op in self.UNARY_OPS:
                    emitted.append(TACInstruction(node.op, left_value, result=target))
                else:
                    emitted.append(TACInstruction(node.op, left_value, right_value, target))
            emitted_nodes.add(node.id)

        for instruction in instructions:
            if self._is_symbol(instruction.result):
                node = symbol_nodes.get(str(instruction.result))
                if node is not None:
                    emit_node(node)

        for name, node in sorted(symbol_nodes.items(), key=lambda item: item[0]):
            if not self._is_temp(name):
                emit_node(node)

        for node in nodes:
            primary = representative(node)
            for label in node.labels:
                if label == primary:
                    continue
                emitted.append(TACInstruction("assign", primary, result=label))

        new_expression_count = sum(1 for instruction in emitted if instruction.op != "assign")
        removed = max(0, original_count - new_expression_count)
        return emitted, removed

    def _try_fold_dag_expression(
        self,
        op: str,
        left: _DAGNode,
        right: Optional[_DAGNode],
    ) -> Optional[str]:
        if op in self.UNARY_OPS and left.const_value is not None:
            value = self._evaluate_unary(op, self._parse_int(left.const_value))
            self.optimizations_applied.append(
                f"TAC DAG 常量合并: {op} {left.const_value} -> {value}"
            )
            return str(value)
        if op in self.BINARY_OPS and left.const_value is not None and right and right.const_value is not None:
            value = self._evaluate_binary(op, self._parse_int(left.const_value), self._parse_int(right.const_value))
            if value is None:
                return None
            self.optimizations_applied.append(
                f"TAC DAG 常量合并: {left.const_value} {op} {right.const_value} -> {value}"
            )
            return str(value)
        return None

    def _is_commutative(self, op: str) -> bool:
        return op in {"+", "*", "==", "!=", "&&", "||", "&", "|", "^"}

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
        reachable_indexes = self._find_reachable_indexes(instructions, label_positions)

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

    @staticmethod
    def _parse_int(value: Any) -> int:
        if isinstance(value, int):
            return value

        text = str(value).strip()
        sign = 1
        if text.startswith("-"):
            sign = -1
            text = text[1:]

        if text.startswith(("0x", "0X")):
            return sign * int(text, 16)
        if text.startswith(("0b", "0B")):
            return sign * int(text, 2)
        if text.startswith(("0o", "0O")):
            return sign * int(text, 8)
        return sign * int(text, 10)

    def _as_int(self, value: Any) -> Optional[int]:
        if not self._is_immediate(value):
            return None
        try:
            return self._parse_int(value)
        except ValueError:
            return None

    def _is_zero(self, value: Any) -> bool:
        return self._as_int(value) == 0

    def _is_one(self, value: Any) -> bool:
        return self._as_int(value) == 1

    def _is_immediate(self, value: Any) -> bool:
        if value is None:
            return False
        text = str(value).lstrip("-")
        return (
            text.isdigit()
            or text.startswith(('0x', '0X'))
            or text.startswith(('0b', '0B'))
            or text.startswith(('0o', '0O'))
        )

    def _is_symbol(self, value: Any) -> bool:
        return isinstance(value, str) and not self._is_immediate(value)

    def _is_temp(self, value: Any) -> bool:
        return isinstance(value, str) and value.startswith("t") and value[1:].isdigit()
