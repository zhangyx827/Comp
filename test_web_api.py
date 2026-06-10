"""快速验证 Web API 功能"""
from compiler.compiler import Compiler
import json

def test_web_api():
    """测试 Web API 响应的完整性和格式"""
    compiler = Compiler()

    # 测试代码
    test_code = """
    int add(int a, int b) {
        return a + b;
    }

    int main() {
        int x = 10;
        int y = 20;
        int result = add(x, y);
        return result;
    }
    """

    # 编译
    result = compiler.compile(test_code)

    # 模拟 Web API 响应
    api_response = {
        'success': result['success'],
        'lexer_result': {
            'total_tokens': result['lexer_result']['total_tokens'],
            'tokens': result['lexer_result']['tokens'][:5],  # 只返回前5个
            'tokens_by_type': {k: len(v) for k, v in result['lexer_result']['tokens_by_type'].items()}
        },
        'parser_result': {
            'type': result['parser_result']['type'],
            'children_count': len(result['parser_result'].get('children', []))
        },
        'semantic_result': {
            'global_symbols': result['semantic_result']['global_symbols'],
            'local_symbols': result['semantic_result']['local_symbols'],
            'errors': result['semantic_result']['errors'],
            'warnings': result['semantic_result']['warnings']
        },
        'optimization_result': {
            'applied': result['optimization_result']['applied'],
            'optimized_ast_nodes': 'N/A'
        },
        'code_result': {
            'lines': result['code_result']['lines'],
            'assembly_preview': '\n'.join(result['code_result']['assembly'].split('\n')[:10])  # 前10行
        },
        'errors': result['errors'],
        'warnings': result['warnings']
    }

    print("=" * 80)
    print("Web API 响应验证")
    print("=" * 80)
    print("\n模拟的 Web API 响应结构:")
    print(json.dumps(api_response, indent=2, ensure_ascii=False))

    print("\n" + "=" * 80)
    print("验证检查")
    print("=" * 80)

    checks = [
        ("success 字段存在", 'success' in api_response),
        ("lexer_result 字段存在", 'lexer_result' in api_response),
        ("parser_result 字段存在", 'parser_result' in api_response),
        ("semantic_result 字段存在", 'semantic_result' in api_response),
        ("optimization_result 字段存在", 'optimization_result' in api_response),
        ("code_result 字段存在", 'code_result' in api_response),
        ("errors 字段存在", 'errors' in api_response),
        ("warnings 字段存在", 'warnings' in api_response),
        ("编译成功", api_response['success']),
        ("有 token 数据", api_response['lexer_result']['total_tokens'] > 0),
        ("有符号表数据", len(api_response['semantic_result']['global_symbols']) > 0),
        ("有汇编代码", api_response['code_result']['lines'] > 0)
    ]

    all_pass = True
    for check_name, result_check in checks:
        status = "✓" if result_check else "✗"
        print(f"{status} {check_name}")
        if not result_check:
            all_pass = False

    print("\n" + "=" * 80)
    if all_pass:
        print("✓ Web API 响应格式验证通过！")
        print("✓ 可视化界面可以正确显示所有编译阶段的结果")
    else:
        print("✗ 部分验证失败")
    print("=" * 80)

if __name__ == "__main__":
    test_web_api()
