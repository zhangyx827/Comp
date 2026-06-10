import argparse
import sys
import os

from compiler.compiler import Compiler
from web.app import run_server

def main():
    parser = argparse.ArgumentParser(description="自定义编译器 CLI & Web 启动器")
    parser.add_argument('file', nargs='?', help='要编译的源代码文件路径')
    parser.add_argument('--web', action='store_true', help='启动 Web 可视化服务器')
    parser.add_argument('--port', type=int, default=8888, help='Web 服务器端口 (默认: 8888)')
    
    args = parser.parse_args()
    
    # 如果没有指定文件，或者指定了 --web，则启动服务器
    if args.web or not args.file:
        run_server(port=args.port)
    else:
        if not os.path.exists(args.file):
            print(f"错误: 文件 '{args.file}' 不存在。")
            sys.exit(1)
            
        with open(args.file, 'r', encoding='utf-8') as f:
            source_code = f.read()
            
        compiler = Compiler()
        result = compiler.compile(source_code)
        
        print("=== 编译结果 ===")
        print(f"成功: {result['success']}")
        
        if result['success']:
            print("\n>>> 生成的汇编代码 <<<\n")
            print(result['code_result']['assembly'])
            print("\n>>> 符号表 <<<\n")
            for sym in result['semantic_result']['global_symbols']:
                print(sym)
            for sym in result['semantic_result']['local_symbols']:
                print(sym)
        else:
            print("\n编译失败，错误信息:")
            for error in result['errors']:
                if isinstance(error, dict) and 'message' in error:
                    print(f"  - {error['message']}")
                else:
                    print(f"  - {error}")
            
        if result.get('warnings'):
            print("\n警告信息:")
            for warning in result['warnings']:
                if isinstance(warning, dict) and 'message' in warning:
                    print(f"  - {warning['message']}")
                else:
                    print(f"  - {warning}")

if __name__ == '__main__':
    main()
