"""性能测试：测试编译器在大量代码下的性能"""
from compiler.compiler import Compiler
import time

def test_performance():
    """测试编译器性能"""
    compiler = Compiler()

    # 生成大量测试代码
    large_code = """
    // 大型测试程序
    int add(int a, int b) { return a + b; }
    int sub(int a, int b) { return a - b; }
    int mul(int a, int b) { return a * b; }
    int div(int a, int b) { if (b == 0) return 0; return a / b; }
    
    int factorial(int n) {
        if (n <= 1) return 1;
        return n * factorial(n - 1);
    }
    
    int fibonacci(int n) {
        if (n <= 1) return n;
        return fibonacci(n - 1) + fibonacci(n - 2);
    }
    
    int is_prime(int n) {
        if (n <= 1) return 0;
        for (int i = 2; i < n; i = i + 1) {
            if (n % i == 0) return 0;
        }
        return 1;
    }
    
    int sum_range(int start, int end) {
        int total = 0;
        for (int i = start; i <= end; i = i + 1) {
            total = total + i;
        }
        return total;
    }
    
    int gcd(int a, int b) {
        if (b == 0) return a;
        return gcd(b, a % b);
    }
    
    int lcm(int a, int b) {
        return (a * b) / gcd(a, b);
    }
    
    int power(int base, int exp) {
        if (exp == 0) return 1;
        return base * power(base, exp - 1);
    }
    
    int count_primes(int limit) {
        int count = 0;
        for (int i = 2; i <= limit; i = i + 1) {
            if (is_prime(i)) {
                count = count + 1;
            }
        }
        return count;
    }
    
    int max3(int a, int b, int c) {
        if (a > b) {
            if (a > c) return a;
            return c;
        } else {
            if (b > c) return b;
            return c;
        }
    }
    
    int min3(int a, int b, int c) {
        if (a < b) {
            if (a < c) return a;
            return c;
        } else {
            if (b < c) return b;
            return c;
        }
    }
    
    int abs_val(int x) {
        if (x < 0) return -x;
        return x;
    }
    
    int sign(int x) {
        if (x > 0) return 1;
        if (x < 0) return -1;
        return 0;
    }
    
    int is_even(int n) {
        if (n % 2 == 0) return 1;
        return 0;
    }
    
    int is_odd(int n) {
        return 1 - is_even(n);
    }
    
    int square(int x) {
        return x * x;
    }
    
    int cube(int x) {
        return x * x * x;
    }
    
    int main() {
        int a = 10, b = 20, c = 30;
        int result = 0;
        
        // 基本运算
        result = add(a, b);
        result = sub(b, a);
        result = mul(a, b);
        result = div(b, a);
        
        // 数学函数
        result = factorial(5);
        result = fibonacci(10);
        result = is_prime(17);
        result = sum_range(1, 100);
        result = gcd(48, 18);
        result = lcm(4, 6);
        result = power(2, 10);
        result = count_primes(50);
        result = max3(a, b, c);
        result = min3(a, b, c);
        result = abs_val(-42);
        result = sign(-5);
        result = sign(5);
        result = sign(0);
        result = is_even(4);
        result = is_odd(3);
        result = square(5);
        result = cube(3);
        
        // 循环测试
        for (int i = 0; i < 100; i = i + 1) {
            result = result + i;
        }
        
        // 嵌套循环
        for (int k = 0; k < 10; k = k + 1) {
            for (int j = 0; j < 10; j = j + 1) {
                result = result + 1;
            }
        }
        
        // 条件测试
        if (result > 0) {
            if (result > 1000) {
                result = result - 1000;
            } else {
                result = result + 100;
            }
        } else {
            result = 0;
        }
        
        return result;
    }
    """

    print("=" * 80)
    print("性能测试")
    print("=" * 80)

    # 测试单次编译性能
    iterations = [1, 5, 10, 20]

    for n in iterations:
        times = []
        for i in range(n):
            start = time.time()
            result = compiler.compile(large_code)
            elapsed = time.time() - start
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        if result['success']:
            tokens = result['lexer_result']['total_tokens']
            asm_lines = result['code_result']['lines']
            print(f"\n{n} 次编译:")
            print(f"  平均耗时: {avg_time*1000:.2f}ms")
            print(f"  最短耗时: {min_time*1000:.2f}ms")
            print(f"  最长耗时: {max_time*1000:.2f}ms")
            print(f"  Tokens: {tokens}, 汇编行数: {asm_lines}")
        else:
            print(f"\n{n} 次编译: 编译失败")
            for err in result.get('errors', []):
                print(f"  错误: {err}")

    # 测试各个编译阶段的时间
    print("\n" + "=" * 80)
    print("编译阶段性能分析")
    print("=" * 80)

    from compiler.lexer import EnhancedLexer
    from compiler.parser import EnhancedParser
    from compiler.semantic import EnhancedSemanticAnalyzer
    from compiler.optimizer import Optimizer
    from compiler.codegen import EnhancedCodeGenerator

    times = {
        '词法分析': 0,
        '语法分析': 0,
        '语义分析': 0,
        '代码优化': 0,
        '代码生成': 0
    }

    for i in range(100):
        # 词法分析
        start = time.time()
        lexer = EnhancedLexer(large_code)
        tokens = lexer.tokenize()
        times['词法分析'] += time.time() - start

        # 语法分析
        start = time.time()
        parser = EnhancedParser(tokens)
        ast = parser.parse()
        times['语法分析'] += time.time() - start

        # 语义分析
        start = time.time()
        semantic = EnhancedSemanticAnalyzer()
        semantic_result = semantic.analyze(ast)
        times['语义分析'] += time.time() - start

        # 代码优化
        start = time.time()
        optimizer = Optimizer()
        optimized_ast = optimizer.optimize(ast)
        times['代码优化'] += time.time() - start

        # 代码生成
        start = time.time()
        codegen = EnhancedCodeGenerator()
        assembly = codegen.generate(optimized_ast)
        times['代码生成'] += time.time() - start

    print(f"\n100次编译平均耗时:")
    for stage, t in times.items():
        avg = (t / 100) * 1000
        print(f"  {stage}: {avg:.3f}ms")

    total = sum(times.values())
    print(f"\n总计: {total/100*1000:.3f}ms")

    print("\n" + "=" * 80)
    print("✓ 性能测试完成")
    print("=" * 80)

if __name__ == "__main__":
    test_performance()
