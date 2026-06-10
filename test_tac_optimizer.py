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
        self.assertIn("result = 50", text)
        self.assertIn("result = 45", text)
        self.assertNotIn("call add", text)
        self.assertNotIn("result = t7", text)
        self.assertLess(result["tac_result"]["lines"], result["original_tac_result"]["lines"])
        self.assertTrue(
            any("TAC 常量函数求值" in item for item in result["optimization_result"]["applied"])
        )
        self.assertTrue(
            any("TAC 不可达代码删除" in item for item in result["optimization_result"]["applied"])
        )


if __name__ == "__main__":
    unittest.main()
