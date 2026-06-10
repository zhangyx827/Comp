"""
Flask Web服务器 - 提供编译API和静态文件服务
"""
from flask import Flask, request, jsonify, render_template, url_for
import os
import sys

# 添加父目录到sys.path以导入compiler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from compiler.compiler import Compiler

app = Flask(__name__, static_folder='static', template_folder='templates')
compiler = Compiler()

@app.route('/')
def index():
    """提供主页"""
    return render_template('index.html')

@app.route('/compile', methods=['POST'])
def compile_code():
    """编译API"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        target = data.get('target', 'x86_64')
        
        result = compiler.compile(code, target=target)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'errors': [{'message': str(e)}],
            'warnings': []
        })

def run_server(host='0.0.0.0', port=8888, debug=True):
    print("启动编译器可视化平台...")
    print(f"访问地址: http://localhost:{port}")
    app.run(debug=debug, port=port, host=host)

if __name__ == '__main__':
    run_server()
