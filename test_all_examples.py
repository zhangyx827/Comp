"""全面测试所有示例文件"""
from compiler.compiler import Compiler
import os
import time

def test_examples():
    """测试所有示例文件"""
    compiler = Compiler()
    examples_dir = 'examples'

    # 获取所有.c文件
    test_files = [f for f in os.listdir(examples_dir) if f.endswith('.c')]
    test_files.sort()

    print("=" * 80)
    print("全面测试编译器 - 所有示例文件")
    print("=" * 80)

    results = []
    total_time = 0

    for i, filename in enumerate(test_files, 1):
        filepath = os.path.join(examples_dir, filename)
        print(f"\n[{i}/{len(test_files)}] 测试文件: {filename}")
        print("-" * 60)

        start_time = time.time()

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source_code = f.read()

            # 编译
            result = compiler.compile(source_code)
            elapsed = time.time() - start_time
            total_time += elapsed

            if result['success']:
                # 统计信息
                tokens = result['lexer_result']['total_tokens']
                semantic = result['semantic_result']
                global_syms = len(semantic['global_symbols'])
                local_syms = len(semantic['local_symbols'])
                asm_lines = result['code_result']['lines']

                print(f"✓ 编译成功 ({elapsed:.3f}s)")
                print(f"  - 词法分析: {tokens} 个 tokens")
                print(f"  - 语法分析: 生成 AST")
                print(f"  - 语义分析: {global_syms} 个全局符号, {local_syms} 个局部符号")
                print(f"  - 代码生成: {asm_lines} 行汇编")

                # 检查优化
                if result.get('optimization_result'):
                    opts = result['optimization_result']['applied']
                    if opts:
                        print(f"  - 优化: {len(opts)} 项优化")

                # 输出部分汇编代码（展示关键部分）
                assembly = result['code_result']['assembly']
                func_count = assembly.count(':\n')
                print(f"  - 生成 {func_count} 个函数")

                results.append({
                    'file': filename,
                    'status': 'PASS',
                    'time': elapsed,
                    'tokens': tokens,
                    'asm_lines': asm_lines
                })

            else:
                print(f"✗ 编译失败 ({elapsed:.3f}s)")
                for err in result.get('errors', []):
                    print(f"  错误: {err}")

                results.append({
                    'file': filename,
                    'status': 'FAIL',
                    'time': elapsed,
                    'errors': result.get('errors', [])
                })

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ 异常: {e}")
            results.append({
                'file': filename,
                'status': 'ERROR',
                'time': elapsed,
                'error': str(e)
            })

    # 汇总统计
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)

    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] in ['FAIL', 'ERROR'])

    print(f"总文件数: {len(results)}")
    print(f"通过: {passed} ({passed/len(results)*100:.1f}%)")
    print(f"失败: {failed} ({failed/len(results)*100:.1f}%)")
    print(f"总耗时: {total_time:.3f}s")
    print(f"平均耗时: {total_time/len(results):.3f}s")

    # 详细结果表
    print("\n详细结果:")
    print("-" * 80)
    print(f"{'文件名':<30} {'状态':<8} {'时间(s)':<10} {'Tokens':<10} {'汇编行数':<10}")
    print("-" * 80)

    for r in results:
        status_icon = "✓" if r['status'] == 'PASS' else "✗"
        print(f"{r['file']:<30} {status_icon} {r['status']:<6} {r['time']:<10.3f} "
              f"{r.get('tokens', 0):<10} {r.get('asm_lines', 0):<10}")

    print("=" * 80)

    # 测试一个具体示例的完整输出
    print("\n详细示例: 09_complex_sort.c")
    print("=" * 80)

    with open('examples/09_complex_sort.c', 'r', encoding='utf-8') as f:
        complex_code = f.read()

    result = compiler.compile(complex_code)

    if result['success']:
        print("\n【源代码】")
        print(complex_code)

        print("\n【生成的汇编代码】")
        print(result['code_result']['assembly'])

        print("\n【符号表 - 全局】")
        for sym in result['semantic_result']['global_symbols']:
            print(f"  - {sym['name']}: {sym['type']}, 返回类型: {sym.get('return_type', 'N/A')}")

        print("\n【符号表 - 局部】")
        for sym in result['semantic_result']['local_symbols'][:10]:  # 只显示前10个
            print(f"  - {sym['name']}: {sym['type']}, 类型: {sym.get('data_type', 'N/A')}")

    print("\n" + "=" * 80)
    print("✓ 全部测试完成！")
    print("=" * 80)

if __name__ == "__main__":
    test_examples()
