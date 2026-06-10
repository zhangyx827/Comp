# 自定义编译器及可视化平台

一个类似简单 C 语言的完整编译器，从词法分析到 x86 汇编生成，并提供 Web 可视化界面。

---

## 项目功能

### 完整编译流水线
- **词法分析**：识别关键字、标识符、字面量、运算符
- **语法分析**：递归下降解析，生成抽象语法树（AST）
- **语义分析**：符号表管理、作用域控制、类型检查
- **代码优化**：常量折叠（Constant Folding）
- **代码生成**：生成 Intel 语法 x86 汇编代码

### Web 可视化平台
- **代码编辑器**：CodeMirror 集成，支持语法高亮
- **阶段可视化**：Tokens、AST、符号表、汇编代码分阶段展示
- **错误提示**：实时显示语法和语义错误及行号

---

## 项目结构

```
.
├── compiler/              # 编译器核心模块
│   ├── core.py           # 核心数据结构（Token, ASTNode）+ 异常类
│   ├── lexer.py          # 词法分析器（正则表达式）
│   ├── parser.py         # 语法分析器（递归下降）
│   ├── semantic.py       # 语义分析器（符号表、类型检查）
│   ├── optimizer.py      # 代码优化器（常量折叠）
│   ├── codegen.py        # x86 汇编代码生成器
│   ├── compiler.py       # Compiler 主控类，串联流水线
│   └── __init__.py       # 模块入口
├── web/                   # Web 可视化平台
│   ├── app.py            # Flask 服务器路由与 API
│   ├── static/
│   │   ├── css/style.css # 样式表
│   │   └── js/main.js    # 前端交互逻辑
│   └── templates/
│       └── index.html    # Web 界面结构
├── examples/              # 示例源代码文件
│   ├── 00_test.c         # 基础变量和运算
│   ├── 01_math.c         # 基础数学运算
│   ├── 02_loop.c         # 循环结构示例
│   ├── 03_func.c         # 函数调用
│   ├── 04_fibonacci.c    # 递归斐波那契
│   ├── 05_primes.c       # 寻找素数
│   ├── 06_array.c        # 数组操作
│   ├── 07_pointer.c      # 指针基础
│   ├── 08_complex_ptr.c  # 复杂指针操作
│   └── 09_complex_sort.c # 综合排序算法
├── main.py                # 统一入口（CLI + Web）
├── requirements.txt       # Python 依赖
├── test_full.py           # 基础功能测试
├── test_all_examples.py   # 示例文件测试
├── test_performance.py    # 性能基准测试
├── test_final_report.py   # 综合报告生成器
└── README.md              # 本说明文档
```

---

## 支持的语法

| 类别 | 特性 | 示例 |
|------|------|------|
| **数据类型** | int, float, char, string, bool, void | `int x = 10;` |
| **变量声明** | 基本声明、多变量、数组、指针 | `int a = 1, b = 2;` |
| **控制流** | if-else, while, for, break, continue | `if (x > 0) return x;` |
| **函数** | 定义、调用、递归 | `int add(int a, int b) { return a + b; }` |
| **表达式** | 算术、比较、逻辑、位运算 | `a + b * c && (d > e)` |
| **数组** | 声明、下标访问 | `int arr[10]; arr[0] = 5;` |
| **指针** | 取地址、解引用 | `int *ptr = &x; int y = *ptr;` |

---

## 使用方法

### 环境准备
```bash
pip install -r requirements.txt
```

### 方式一：Web 可视化界面
```bash
# 启动服务器（默认端口 8888）
python main.py
# 或显式指定
python main.py --web --port 8888
```
浏览器访问：`http://localhost:8888`

### 方式二：命令行编译
```bash
# 编译单个文件并输出汇编
python main.py examples/00_test.c
```

### 运行测试
```bash
# 基础测试
python test_full.py

# 测试所有示例
python test_all_examples.py

# 性能测试
python test_performance.py

# 生成综合报告
python test_final_report.py
```

---

## 测试结果

- ✅ **基础测试**: 10/10 通过
- ✅ **示例文件**: 10/10 通过
- ✅ **平均编译时间**: < 10ms
