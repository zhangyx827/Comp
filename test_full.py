"""全面检查编译器功能"""
from compiler.compiler import Compiler

def test_all_features():
    compiler = Compiler()
    
    # 测试用例
    test_cases = [
        {
            'name': '基础变量和运算',
            'code': """int main() {
    int x = 10;
    int y = 20;
    return x + y;
}""",
            'expected_tokens': ['INT', 'IDENTIFIER', 'LEFT_PAREN', 'RIGHT_PAREN', 'LEFT_BRACE',
                              'INT', 'IDENTIFIER', 'ASSIGN', 'INTEGER_LITERAL', 'SEMICOLON',
                              'INT', 'IDENTIFIER', 'ASSIGN', 'INTEGER_LITERAL', 'SEMICOLON',
                              'RETURN', 'IDENTIFIER', 'PLUS', 'IDENTIFIER', 'SEMICOLON',
                              'RIGHT_BRACE']
        },
        {
            'name': '条件语句',
            'code': """int main() {
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
            'code': """int main() {
    int sum = 0;
    for (int i = 0; i < 10; i++) {
        sum = sum + i;
    }
    return sum;
}"""
        },
        {
            'name': '函数调用',
            'code': """int add(int a, int b) {
    return a + b;
}
int main() {
    return add(3, 5);
}"""
        },
        {
            'name': '数组操作',
            'code': """int main() {
    int arr[5];
    arr[0] = 100;
    return arr[0];
}"""
        },
        {
            'name': '指针操作',
            'code': """int main() {
    int x = 42;
    int *ptr = &x;
    return *ptr;
}"""
        },
        {
            'name': '复杂表达式',
            'code': """int main() {
    int a = 1, b = 2, c = 3;
    return a * b + c / 2;
}"""
        },
        {
            'name': '递归函数',
            'code': """int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
int main() {
    return factorial(5);
}"""
        }
    ]
    
    print("=" * 70)
    print("全面测试编译器功能")
    print("=" * 70)
    
    all_passed = True
    for i, tc in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] 测试: {tc['name']}")
        print("-" * 50)
        
        try:
            result = compiler.compile(tc['code'])
            
            if result['success']:
                print(f"✓ 编译成功")
                
                # 检查词法分析
                if 'lexer_result' in result and result['lexer_result']:
                    tokens = result['lexer_result']
                    print(f"  - 词法分析: {tokens['total_tokens']} 个 tokens")
                
                # 检查语法分析
                if 'parser_result' in result and result['parser_result']:
                    ast = result['parser_result']
                    print(f"  - 语法分析: AST类型 = {ast['type']}")
                
                # 检查语义分析
                if 'semantic_result' in result and result['semantic_result']:
                    sem = result['semantic_result']
                    symbols = sem.get('global_symbols', [])
                    print(f"  - 语义分析: {len(symbols)} 个全局符号")
                
                # 检查代码生成
                if 'code_result' in result and result['code_result']:
                    code = result['code_result']
                    print(f"  - 代码生成: {code['lines']} 行汇编")
                
                print("  ✓ 所有阶段通过")
            else:
                print(f"✗ 编译失败")
                for err in result.get('errors', []):
                    print(f"  Error: {err}")
                all_passed = False
                
        except Exception as e:
            print(f"✗ 异常: {e}")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 70)

if __name__ == "__main__":
    test_all_features()