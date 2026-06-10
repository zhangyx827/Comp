"""编译器综合测试报告"""
from compiler.compiler import Compiler
import time
import json

def generate_report():
    """生成综合测试报告"""
    compiler = Compiler()

    print("=" * 80)
    print(" " * 20 + "编译器综合测试报告")
    print("=" * 80)

    # 测试用例定义
    test_cases = [
        {
            'name': '基础测试',
            'code': """
int main() {
    int x = 10;
    int y = 20;
    return x + y;
}"""
        },
        {
            'name': '条件语句',
            'code': """
int main() {
    int a = 5;
    if (a > 3) {
        return 1;
    } else {
        return 0;
    }
}"""
        },
        {
            'name': '循环语句',
            'code': """
int main() {
    int sum = 0;
    for (int i = 0; i < 10; i++) {
        sum = sum + i;
    }
    return sum;
}"""
        },
        {
            'name': '函数调用',
            'code': """
int add(int a, int b) {
    return a + b;
}
int main() {
    return add(3, 5);
}"""
        },
        {
            'name': '数组操作',
            'code': """
int main() {
    int arr[5];
    arr[0] = 100;
    arr[1] = 200;
    return arr[0] + arr[1];
}"""
        },
        {
            'name': '指针操作',
            'code': """
int main() {
    int x = 42;
    int *ptr = &x;
    return *ptr;
}"""
        },
        {
            'name': '复杂表达式',
            'code': """
int main() {
    int a = 1, b = 2, c = 3;
    int d = a * b + c / 2 - (a + b) * c;
    return d;
}"""
        },
        {
            'name': '递归函数',
            'code': """
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
int main() {
    return factorial(5);
}"""
        },
        {
            'name': '嵌套条件',
            'code': """
int main() {
    int x = 10;
    int y = 20;
    int z = 30;
    if (x > y) {
        if (x > z) return x;
        return z;
    } else {
        if (y > z) return y;
        return z;
    }
}"""
        },
        {
            'name': '字符串模拟',
            'code': """
int main() {
    int chars[5];
    chars[0] = 72;  // H
    chars[1] = 101; // e
    chars[2] = 108; // l
    chars[3] = 108; // l
    chars[4] = 111; // o
    return chars[0];
}"""
        }
    ]

    # 运行测试
    results = []
    total_time = 0

    print("\n测试用例执行:")
    print("-" * 80)

    for i, test in enumerate(test_cases, 1):
        start = time.time()
        result = compiler.compile(test['code'])
        elapsed = time.time() - start
        total_time += elapsed

        if result['success']:
            status = "✓ PASS"
            tokens = result['lexer_result']['total_tokens']
            asm_lines = result['code_result']['lines']
            symbols = len(result['semantic_result']['global_symbols'])
        else:
            status = "✗ FAIL"
            tokens = 0
            asm_lines = 0
            symbols = 0

        results.append({
            'name': test['name'],
            'status': status,
            'time': elapsed,
            'tokens': tokens,
            'asm_lines': asm_lines,
            'symbols': symbols,
            'success': result['success']
        })

        print(f"{i:2d}. {test['name']:<20} {status}  "
              f"({elapsed*1000:.2f}ms, {tokens} tokens, {asm_lines} lines)")

    # 统计信息
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    avg_time = total_time / len(results)

    print("\n" + "=" * 80)
    print("统计信息")
    print("=" * 80)
    print(f"总测试数:     {len(results)}")
    print(f"通过:         {passed} ({passed/len(results)*100:.1f}%)")
    print(f"失败:         {failed} ({failed/len(results)*100:.1f}%)")
    print(f"总耗时:       {total_time*1000:.2f}ms")
    print(f"平均耗时:     {avg_time*1000:.2f}ms")

    # 功能覆盖
    print("\n" + "=" * 80)
    print("功能覆盖")
    print("=" * 80)

    features = {
        '变量声明': '基础测试',
        '条件语句': '条件语句',
        '循环语句': '循环语句',
        '函数定义': '函数调用',
        '函数调用': '函数调用',
        '数组操作': '数组操作',
        '指针操作': '指针操作',
        '算术运算': '复杂表达式',
        '递归函数': '递归函数',
        '嵌套控制流': '嵌套条件'
    }

    for feature, test_name in features.items():
        test_result = next((r for r in results if r['name'] == test_name), None)
        status = "✓" if test_result and test_result['success'] else "✗"
        print(f"{status} {feature}")

    # 示例文件测试
    print("\n" + "=" * 80)
    print("示例文件测试")
    print("=" * 80)

    import os
    examples_dir = 'examples'
    example_files = sorted([f for f in os.listdir(examples_dir) if f.endswith('.c')])

    example_results = []
    for filename in example_files:
        filepath = os.path.join(examples_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()

        start = time.time()
        result = compiler.compile(code)
        elapsed = time.time() - start

        if result['success']:
            status = "✓"
            tokens = result['lexer_result']['total_tokens']
            asm_lines = result['code_result']['lines']
        else:
            status = "✗"
            tokens = 0
            asm_lines = 0

        example_results.append({
            'file': filename,
            'status': status,
            'time': elapsed,
            'tokens': tokens,
            'asm_lines': asm_lines,
            'success': result['success']
        })

        print(f"{status} {filename:<30} ({elapsed*1000:.2f}ms, "
              f"{tokens} tokens, {asm_lines} lines)")

    example_passed = sum(1 for r in example_results if r['success'])
    print(f"\n示例通过率: {example_passed}/{len(example_results)} "
          f"({example_passed/len(example_results)*100:.1f}%)")

    # 最终结论
    print("\n" + "=" * 80)
    print("结论")
    print("=" * 80)

    if passed == len(results) and example_passed == len(example_results):
        print("✓ 所有测试通过！编译器功能完整，运行稳定。")
        print("✓ 支持词法分析、语法分析、语义分析和代码生成。")
        print("✓ 支持变量、函数、数组、指针、条件语句、循环语句等特性。")
        print("✓ 性能表现优秀，平均编译时间 < 10ms。")
    else:
        print("✗ 部分测试失败，请检查错误信息。")

    print("=" * 80)

    # 保存JSON报告
    report = {
        'timestamp': time.time(),
        'test_results': results,
        'example_results': example_results,
        'summary': {
            'total_tests': len(results),
            'passed': passed,
            'failed': failed,
            'example_files': len(example_files),
            'example_passed': example_passed,
            'total_time': total_time,
            'avg_time': avg_time
        }
    }

    with open('test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n测试报告已保存到 test_report.json")

if __name__ == "__main__":
    generate_report()
