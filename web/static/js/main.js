        const sampleCodes = {
            complex: `// 综合示例程序：struct / enum / union
enum Status {
    STATUS_INIT = 0,
    STATUS_RUNNING = 1,
    STATUS_DONE = 2
};

union Payload {
    int number;
    int flag;
};

struct Task {
    int id;
    enum Status status;
    union Payload payload;
};

int make_task_id(int base, int offset) {
    return base + offset;
}

int main() {
    struct Task task;
    task.id = make_task_id(100, 7);
    task.status = STATUS_RUNNING;
    task.payload.number = 42;

    if (task.status == STATUS_RUNNING) {
        task.payload.flag = task.payload.number + task.id;
    } else {
        task.payload.flag = 0;
    }

    return task.payload.flag;
}`,
            math: `// 示例: 基础运算
int main() {
    int x = 10;
    int y = 20;
    int result = x + y * 2;
    return result;
}`,
            loop: `// 示例: 循环结构
int main() {
    int sum = 0;
    for (int i = 1; i <= 10; ++i) {
        if (i % 2 == 0) {
            sum = sum + i;
        }
    }
    return sum;
}`,
            func: `// 示例: 函数调用
int multiply(int a, int b) {
    return a * b;
}

int main() {
    int x = 5;
    int y = 4;
    int result = multiply(x, y);
    return result;
}`,
            fibonacci: `// 示例: 斐波那契数列计算 (递归)
int fibonacci(int n) {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main() {
    int n = 10;
    int result = fibonacci(n);
    return result;
}`,
            primes: `// 示例: 寻找素数
int is_prime(int n) {
    if (n <= 1) {
        return 0; // false
    }
    for (int i = 2; i < n; ++i) {
        if (n % i == 0) {
            return 0; // false
        }
    }
    return 1; // true
}

int main() {
    int limit = 20;
    int count = 0;
    
    for (int num = 2; num <= limit; ++num) {
        if (is_prime(num)) {
            count = count + 1;
        }
    }
    
    return count;
}`,
            array: `// 示例: 数组操作
int main() {
    int arr[5];
    arr[0] = 10;
    arr[1] = 20;
    arr[2] = arr[0] + arr[1];
    return arr[2];
}`,
            pointer: `// 示例: 指针操作
int main() {
    int x = 10;
    int *ptr = &x;
    return *ptr;
}`
        };

        function loadExample() {
            const select = document.getElementById('example-select');
            const code = sampleCodes[select.value];
            editor.setValue(code);
            resetPipeline();
        }

        // Initialize CodeMirror editor
        const codeEditor = document.getElementById('code-editor');
        const editor = CodeMirror.fromTextArea(codeEditor, {
            mode: 'text/x-csrc',
            theme: 'dracula',
            lineNumbers: true,
            indentUnit: 4,
            matchBrackets: true
        });
        editor.setValue(sampleCodes.complex);

        // Compile function
        async function compileCode() {
            const code = editor.getValue();
            const target = document.getElementById('target-select').value;
            
            // Reset status
            resetPipeline();
            
            // Activate stages
            setTimeout(() => activateStage('lexer'), 100);
            
            try {
                const response = await fetch('/compile', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code, target })
                });
                
                const result = await response.json();
                displayResult(result);
                
            } catch (error) {
                // Fallback to mock data if server not available
                displayMockResult();
            }
        }

        function resetPipeline() {
            ['lexer', 'parser', 'semantic', 'tac', 'code'].forEach(stage => {
                document.getElementById(`status-${stage}`).className = 'stage-status';
                document.getElementById(`stage-${stage}`).classList.remove('active');
            });
            document.getElementById('errors-section').style.display = 'none';
        }

        function activateStage(stage) {
            document.getElementById(`stage-${stage}`).classList.add('active');
        }

        function setStageStatus(stage, status) {
            const el = document.getElementById(`status-${stage}`);
            el.className = 'stage-status ' + status;
        }

        function displayResult(result) {
            // Lexer
            activateStage('lexer');
            if (result.lexer_result) {
                setStageStatus('lexer', 'success');
                displayLexerResult(result.lexer_result);
                document.getElementById('stat-tokens').textContent = result.lexer_result.total_tokens;
            }
            
            // Parser
            setTimeout(() => {
                activateStage('parser');
                if (result.parser_result) {
                    setStageStatus('parser', 'success');
                    displayParserResult(result.parser_result);
                    document.getElementById('stat-ast-nodes').textContent = countASTNodes(result.parser_result);
                }
            }, 200);
            
            // Semantic
            setTimeout(() => {
                activateStage('semantic');
                if (result.semantic_result) {
                    if (result.semantic_result.success) {
                        setStageStatus('semantic', 'success');
                    } else {
                        setStageStatus('semantic', 'error');
                    }
                    displaySemanticResult(result.semantic_result);
                    document.getElementById('stat-symbols').textContent = result.semantic_result.global_symbols.length;
                }
            }, 400);
            
            // TAC Generation
            setTimeout(() => {
                activateStage('tac');
                if (result.tac_result) {
                    setStageStatus('tac', 'success');
                    displayTacResult(result.tac_result, result.original_tac_result, result.optimization_result);
                    document.getElementById('stat-tac-lines').textContent = result.tac_result.lines;
                }
            }, 600);

            // Code Generation
            setTimeout(() => {
                activateStage('code');
                if (result.code_result) {
                    setStageStatus('code', 'success');
                    displayCodeResult(result.code_result);
                    document.getElementById('stat-lines').textContent = result.code_result.lines;
                }
            }, 800);
            
            // Errors
            if (result.errors && result.errors.length > 0) {
                document.getElementById('errors-section').style.display = 'block';
                displayErrors(result.errors);
            }
        }

        function displayLexerResult(result) {
            const container = document.getElementById('content-lexer');
            let html = '<div class="token-list">';
            
            result.tokens.slice(0, 50).forEach(token => {
                html += `
                    <div class="token-item slide-in">
                        <span class="token-type">${token.type}</span>
                        <span class="token-value">${escapeHtml(token.value)}</span>
                        <span class="token-location">行${token.line}:${token.column}</span>
                    </div>
                `;
            });
            
            if (result.tokens.length > 50) {
                html += `<p style="text-align: center; color: var(--text-tertiary); padding: 1rem;">... 还有 ${result.tokens.length - 50} 个 tokens</p>`;
            }
            
            html += '</div>';
            container.innerHTML = html;
        }

        function displayParserResult(ast) {
            const container = document.getElementById('content-parser');
            container.innerHTML = '<div class="ast-container"><div class="ast-tree">' + renderAST(ast) + '</div></div>';
        }

        function renderAST(node, depth = 0) {
            if (!node) return '';
            
            // 节点类型颜色映射
            const typeColors = {
                'program': '#6366f1',
                'function_declaration': '#8b5cf6',
                'block': '#64748b',
                'variable_declaration': '#10b981',
                'identifier': '#f59e0b',
                'integer_literal': '#ef4444',
                'float_literal': '#f97316',
                'char_literal': '#84cc16',
                'string_literal': '#22c55e',
                'boolean_literal': '#06b6d4',
                'binary_expression': '#3b82f6',
                'unary_expression': '#ec4899',
                'postfix_expression': '#d946ef',
                'assignment_expression': '#14b8a6',
                'if_statement': '#f43f5e',
                'while_statement': '#8b5cf6',
                'for_statement': '#a855f7',
                'return_statement': '#22c55e',
                'break_statement': '#ef4444',
                'continue_statement': '#f97316',
                'function_call': '#06b6d4',
                'array_access': '#f59e0b',
                'address_of': '#84cc16',
                'expression_statement': '#64748b'
            };
            
            const color = typeColors[node.type] || '#94a3b8';
            const bgColor = color + '20'; // 20% opacity
            
            let html = `<div class="ast-node" style="margin-left: ${depth * 20}px; border-left: 3px solid ${color};">
                <div class="ast-node-content" style="background: ${bgColor}; border: 1px solid ${color}40;">
                    <div class="ast-node-type" style="color: ${color};">${node.type}</div>`;
            
            if (node.value) {
                if (typeof node.value === 'object') {
                    const valueStr = Object.entries(node.value)
                        .map(([k, v]) => `<span style="color: ${color};">${k}</span>: ${JSON.stringify(v)}`)
                        .join(', ');
                    html += `<div class="ast-node-value">{${valueStr}}</div>`;
                } else {
                    html += `<div class="ast-node-value">${JSON.stringify(node.value)}</div>`;
                }
            }
            
            html += `<div class="ast-node-line">行 ${node.line || '?'} 列 ${node.column || '?'}</div>`;
            html += '</div>';
            
            if (node.children && node.children.length > 0) {
                html += '<div class="ast-children">';
                node.children.forEach((child, index) => {
                    html += `<div style="position: relative; padding-left: 10px;">`;
                    html += `<div style="position: absolute; left: 0; top: 0; width: 10px; height: 100%; border-left: 1px dashed #475569; border-bottom: 1px dashed #475569;"></div>`;
                    html += renderAST(child, 0);
                    html += '</div>';
                });
                html += '</div>';
            }
            
            html += '</div>';
            return html;
        }

        function displaySemanticResult(result) {
            const container = document.getElementById('content-semantic');
            let html = '<h4 style="margin-bottom: 1rem; color: var(--accent-primary);">符号表</h4>';
            
            result.global_symbols.forEach(symbol => {
                html += `
                    <div class="symbol-item">
                        <div class="symbol-name">${symbol.name}</div>
                        <div class="symbol-info">
                            <span class="symbol-type">类型: ${symbol.type}</span>
                            ${symbol.return_type ? `<span class="symbol-data-type">返回: ${symbol.return_type}</span>` : ''}
                            ${symbol.data_type ? `<span class="symbol-data-type">数据类型: ${symbol.data_type}</span>` : ''}
                        </div>
                    </div>
                `;
            });
            
            if (result.warnings && result.warnings.length > 0) {
                html += '<h4 style="margin: 1.5rem 0 1rem; color: var(--warning);">警告</h4>';
                result.warnings.forEach(w => {
                    const msg = typeof w === 'string' ? w : (w.message || JSON.stringify(w));
                    html += `<div class="warning-item">${escapeHtml(msg)}</div>`;
                });
            }
            
            container.innerHTML = html;
        }

        function displayCodeResult(result) {
            const container = document.getElementById('content-code');
            const lines = result.assembly.split('\n');
            
            let html = `<div style="margin-bottom: 0.75rem; color: var(--text-secondary); font-size: 0.9rem;">Target: ${escapeHtml(result.target || 'x86_64')}</div>`;
            html += '<div class="assembly-code">';
            lines.forEach(line => {
                const trimmed = line.trim();
                if (trimmed.endsWith(':')) {
                    html += `<div class="assembly-line"><span class="assembly-label">${trimmed}</span></div>`;
                } else if (trimmed.startsWith('.') || trimmed.startsWith('#')) {
                    html += `<div class="assembly-line"><span class="assembly-comment">${trimmed}</span></div>`;
                } else if (trimmed) {
                    const parts = trimmed.split(/\s+/);
                    html += `<div class="assembly-line">
                        <span class="assembly-instruction">${parts.join(' ')}</span>
                    </div>`;
                } else {
                    html += '<div class="assembly-line">&nbsp;</div>';
                }
            });
            html += '</div>';
            
            container.innerHTML = html;
        }

        function displayTacResult(result, originalResult, optimizationResult) {
            const container = document.getElementById('content-tac');
            const originalLines = originalResult && originalResult.text
                ? originalResult.text.split('\n')
                : [];
            const optimizedLines = result.text ? result.text.split('\n') : [];
            const savedLines = originalResult ? originalResult.lines - result.lines : 0;

            let html = '<div class="tac-summary">';
            if (originalResult) {
                html += `<span>优化前 ${originalResult.lines} 行</span>`;
                html += `<span>优化后 ${result.lines} 行</span>`;
                html += `<span>${savedLines >= 0 ? '减少' : '增加'} ${Math.abs(savedLines)} 行</span>`;
            } else {
                html += `<span>优化后 ${result.lines} 行</span>`;
            }
            if (optimizationResult && optimizationResult.applied && optimizationResult.applied.length > 0) {
                html += `<span>优化 ${optimizationResult.applied.length} 项</span>`;
            }
            html += '</div>';

            if (originalResult) {
                html += '<div class="tac-compare">';
                html += renderTacPanel('优化前 TAC', originalLines);
                html += renderTacPanel('优化后 TAC', optimizedLines);
                html += '</div>';
            } else {
                html += renderTacPanel('TAC', optimizedLines);
            }

            container.innerHTML = html;
        }

        function renderTacPanel(title, lines) {
            let html = `<div class="tac-panel"><div class="tac-panel-title">${escapeHtml(title)}</div><div class="assembly-code">`;
            lines.forEach(line => {
                const trimmed = line.trim();
                if (trimmed.endsWith(':')) {
                    html += `<div class="assembly-line"><span class="assembly-label">${escapeHtml(trimmed)}</span></div>`;
                } else if (trimmed.startsWith('function') || trimmed.startsWith('end function')) {
                    html += `<div class="assembly-line"><span class="assembly-comment">${escapeHtml(trimmed)}</span></div>`;
                } else if (trimmed) {
                    html += `<div class="assembly-line"><span class="assembly-instruction">${escapeHtml(trimmed)}</span></div>`;
                } else {
                    html += '<div class="assembly-line">&nbsp;</div>';
                }
            });
            html += '</div></div>';
            return html;
        }

        function displayErrors(errors) {
            const container = document.getElementById('content-errors');
            let html = '';
            
            errors.forEach(error => {
                const msg = typeof error === 'string' ? error : (error.message || JSON.stringify(error));
                html += `<div class="error-item">${escapeHtml(msg)}</div>`;
            });
            
            container.innerHTML = html;
        }

        function countASTNodes(node) {
            if (!node) return 0;
            let count = 1;
            if (node.children) {
                node.children.forEach(child => {
                    count += countASTNodes(child);
                });
            }
            return count;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Mock data for demo
        function displayMockResult() {
            const mockResult = {
                success: true,
                lexer_result: {
                    total_tokens: 88,
                    tokens: [
                        {type: 'INT', value: 'int', line: 2, column: 1},
                        {type: 'IDENTIFIER', value: 'add', line: 2, column: 5},
                        {type: 'LEFT_PAREN', value: '(', line: 2, column: 8},
                        {type: 'INT', value: 'int', line: 2, column: 9},
                        {type: 'IDENTIFIER', value: 'a', line: 2, column: 13}
                    ]
                },
                parser_result: {
                    type: 'program',
                    line: 1,
                    column: 1,
                    children: [
                        {
                            type: 'function_declaration',
                            value: {name: 'add', return_type: 'int'},
                            line: 2,
                            column: 1,
                            children: [{type: 'block', children: []}]
                        }
                    ]
                },
                semantic_result: {
                    success: true,
                    global_symbols: [
                        {name: 'add', type: 'function', return_type: 'int'},
                        {name: 'main', type: 'function', return_type: 'int'}
                    ]
                },
                original_tac_result: {
                    text: `function add:\nparam a\nparam b\nt1 = a + b\nsum = t1\nreturn sum\nend function add`,
                    lines: 7
                },
                tac_result: {
                    text: `function add:\nparam a\nparam b\nt1 = a + b\nreturn t1\nend function add`,
                    lines: 6
                },
                optimization_result: {
                    applied: ['dead code elimination']
                },
                code_result: {
                    assembly: `.text\n.global main\nadd:\n    push rbp\n    mov rbp, rsp\n    ret`,
                    lines: 6
                }
            };
            
            displayResult(mockResult);
        }

        // Keyboard shortcut
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                compileCode();
            }
        });
