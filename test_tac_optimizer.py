import unittest

from compiler.compiler import Compiler
from compiler.optimizer import TACOptimizer
from compiler.tac import TACInstruction


class TACOptimizerTest(unittest.TestCase):
    def test_constant_folding_and_dead_temp_elimination(self):
        instructions = [
            TACInstruction("function", result="main"),
            TACInstruction("declare", result="x"),
            TACInstruction("+", "2", "3", "t1"),
            TACInstruction("*", "t1", "4", "t2"),
            TACInstruction("assign", "t2", result="x"),
            TACInstruction("+", "x", "0", "t3"),
            TACInstruction("return", "x"),
            TACInstruction("end_function", result="main"),
        ]

        optimizer = TACOptimizer()
        optimized = optimizer.optimize(instructions)
        text = "\n".join(str(instruction) for instruction in optimized)

        self.assertIn("x = 20", text)
        self.assertIn("return 20", text)
        self.assertNotIn("t1 =", text)
        self.assertNotIn("t2 =", text)
        self.assertNotIn("t3 =", text)
        self.assertTrue(any("TAC 常量折叠" in item for item in optimizer.optimizations_applied))
        self.assertTrue(any("TAC 无用临时变量删除" in item for item in optimizer.optimizations_applied))

    def test_compiler_uses_optimized_tac_for_codegen(self):
        source = """
int main() {
    int x = 2 + 3;
    int y = x * 4;
    return y;
}
"""

        result = Compiler().compile(source)

        self.assertTrue(result["success"], result["errors"])
        self.assertEqual(result["tac_result"]["optimized"], True)
        self.assertIn("original_tac_result", result)
        self.assertLessEqual(result["tac_result"]["lines"], result["original_tac_result"]["lines"])
        self.assertTrue(
            any(item.startswith("TAC ") for item in result["optimization_result"]["applied"])
        )

    def test_constant_simple_call_and_dead_branch_elimination(self):
        source = """
int add(int a, int b) {
    int sum = a + b;
    return sum;
}

int main() {
    int x = 10;
    x = 30;
    int y = 20;
    int result = add(x, y);

    if (result > 25) {
        result = result - 5;
    } else {
        result = result + 5;
    }

    while (result < 30) {
        result = result + 1;
    }

    return result;
}
"""

        result = Compiler().compile(source)
        text = result["tac_result"]["text"]

        self.assertTrue(result["success"], result["errors"])
        self.assertIn("result = 45", text)
        self.assertNotIn("result = 50", text)
        self.assertNotIn("call add", text)
        self.assertNotIn("result = t7", text)
        self.assertLess(result["tac_result"]["lines"], result["original_tac_result"]["lines"])
        self.assertTrue(
            any("TAC 常量函数求值" in item for item in result["optimization_result"]["applied"])
        )
        self.assertTrue(
            any("TAC 不可达代码删除" in item for item in result["optimization_result"]["applied"])
        )

    def test_block_local_common_subexpression_elimination(self):
        instructions = [
            TACInstruction("function", result="main"),
            TACInstruction("+", "a", "b", "t1"),
            TACInstruction("+", "a", "b", "t2"),
            TACInstruction("*", "t2", "c", "t3"),
            TACInstruction("return", "t3"),
            TACInstruction("end_function", result="main"),
        ]

        optimizer = TACOptimizer()
        optimized = optimizer.optimize(instructions)
        text = "\n".join(str(instruction) for instruction in optimized)

        self.assertIn("t1 = a + b", text)
        self.assertIn("t3 = t1 * c", text)
        self.assertNotIn("t2 = a + b", text)
        self.assertNotIn("t2 =", text)
        self.assertTrue(
            any("TAC 块内公共子表达式删除" in item for item in optimizer.optimizations_applied)
        )

    def test_dag_basic_block_constant_merge_and_rebinding(self):
        instructions = [
            TACInstruction("function", result="main"),
            TACInstruction("assign", "2", result="x"),
            TACInstruction("+", "x", "3", "t1"),
            TACInstruction("+", "2", "3", "t2"),
            TACInstruction("assign", "t2", result="x"),
            TACInstruction("return", "x"),
            TACInstruction("end_function", result="main"),
        ]

        optimizer = TACOptimizer()
        optimized = optimizer.optimize(instructions)
        text = "\n".join(str(instruction) for instruction in optimized)

        self.assertIn("x = 5", text)
        self.assertIn("return 5", text)
        self.assertNotIn("t1 =", text)
        self.assertNotIn("t2 =", text)
        self.assertTrue(
            any("DAG 常量合并" in item or "TAC 常量折叠" in item for item in optimizer.optimizations_applied)
        )

    def test_basic_block_splitting_handles_branches_and_labels(self):
        instructions = [
            TACInstruction("function", result="main"),
            TACInstruction("declare", result="x"),
            TACInstruction("assign", "1", result="x"),
            TACInstruction("if_false", "x", result="L1"),
            TACInstruction("+", "x", "1", "t1"),
            TACInstruction("goto", result="L2"),
            TACInstruction("label", result="L1"),
            TACInstruction("-", "x", "1", "t2"),
            TACInstruction("label", result="L2"),
            TACInstruction("return", "x"),
            TACInstruction("end_function", result="main"),
        ]

        optimizer = TACOptimizer()
        blocks = optimizer._split_basic_blocks(instructions)

        block_texts = [
            "\n".join(str(instruction) for instruction in block["instructions"])
            for block in blocks
        ]

        self.assertEqual(len(blocks), 5)
        self.assertEqual(block_texts[0], "function main:\ndeclare x\nx = 1\nif_false x goto L1")
        self.assertEqual(block_texts[1], "t1 = x + 1\ngoto L2")
        self.assertEqual(block_texts[2], "L1:\nt2 = x - 1")
        self.assertEqual(block_texts[3], "L2:\nreturn x")
        self.assertEqual(block_texts[4], "end function main")
        self.assertEqual(blocks[0]["successors"], [2, 3])
        self.assertIn("函数入口", blocks[0]["leader_reasons"])

    def test_basic_block_analysis_marks_unreachable_blocks(self):
        instructions = [
            TACInstruction("function", result="main"),
            TACInstruction("goto", result="L1"),
            TACInstruction("assign", "99", result="x"),
            TACInstruction("label", result="L1"),
            TACInstruction("return", "0"),
            TACInstruction("end_function", result="main"),
        ]

        optimizer = TACOptimizer()
        analysis = optimizer.analyze_basic_blocks(instructions)

        self.assertEqual(analysis["unreachable_indexes"], [2])
        unreachable_blocks = [block for block in analysis["blocks"] if not block["reachable"]]
        self.assertEqual(len(unreachable_blocks), 1)
        self.assertEqual(unreachable_blocks[0]["instructions"][0]["text"], "x = 99")


if __name__ == "__main__":
    unittest.main()
