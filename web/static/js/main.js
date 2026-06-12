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
            ['lexer', 'parser', 'semantic', 'tac', 'basic-blocks', 'code'].forEach(stage => {
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
                    displayBasicBlocks(result.tac_result, result.original_tac_result);
                    document.getElementById('stat-tac-lines').textContent = result.tac_result.lines;
                }
            }, 600);

            setTimeout(() => {
                activateStage('basic-blocks');
                if (result.tac_result) {
                    setStageStatus('basic-blocks', 'success');
                }
            }, 700);

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
            const totalTokens = result.tokens.length;
            const previewCount = Math.min(totalTokens, 12);
            let html = `
                <div class="token-table-wrap">
                    <div class="token-table-title">Token 表</div>
                    <div class="token-table-summary">共 ${totalTokens} 个 tokens`;
            if (totalTokens > previewCount) {
                html += `，默认展示前 ${previewCount} 个，展开可查看全部`;
            }
            html += `</div>
                    <details class="token-dropdown">
                        <summary class="token-dropdown-summary">
                            <span>查看完整 Token 表</span>
                            <span class="token-dropdown-hint">${totalTokens} 个 tokens</span>
                        </summary>
                        <div class="token-table-scroll">
                            <table class="token-table">
                                <thead>
                                    <tr>
                                        <th>类型</th>
                                        <th>值</th>
                                        <th>行</th>
                                        <th>列</th>
                                    </tr>
                                </thead>
                                <tbody>
            `;

            result.tokens.forEach(token => {
                html += `
                    <tr class="token-row slide-in">
                        <td><span class="token-type">${escapeHtml(token.type)}</span></td>
                        <td class="token-value">${escapeHtml(token.value)}</td>
                        <td class="token-location">${token.line ?? '-'}</td>
                        <td class="token-location">${token.column ?? '-'}</td>
                    </tr>
                `;
            });
            html += `
                                </tbody>
                            </table>
                        </div>
                    </details>
                </div>`;
            container.innerHTML = html;
        }

        function displayParserResult(ast) {
            const container = document.getElementById('content-parser');
            container.innerHTML = `
                <div class="ast-container">
                    <div class="ast-toolbar">
                        <div class="ast-toolbar-item">根节点: ${escapeHtml(ast?.type || 'unknown')}</div>
                        <div class="ast-toolbar-item">节点数: ${countASTNodes(ast)}</div>
                        <button class="ast-toggle-btn" id="ast-toggle-all-btn" type="button">全部展开</button>
                    </div>
                    <div class="ast-breadcrumb" id="ast-breadcrumb">
                        <span class="ast-breadcrumb-label">层级路径</span>
                        <div class="ast-breadcrumb-trail">点击节点查看路径</div>
                    </div>
                    <div class="ast-tree" id="ast-tree-root">${renderAST(ast)}</div>
                </div>
            `;

            const toggleBtn = document.getElementById('ast-toggle-all-btn');
            if (toggleBtn) {
                toggleBtn.addEventListener('click', () => toggleAllASTNodes());
            }
            bindASTInteractions();
        }

        function renderAST(node, depth = 0, path = [], siblingIndex = 0, siblingCount = 1) {
            if (!node) return '';
            const typeColors = {
                'program': '#6366f1',
                'function_declaration': '#8b5cf6',
                'block': '#64748b',
                'variable_declaration': '#10b981',
                'variable_declarations': '#14b8a6',
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
            const hasChildren = Array.isArray(node.children) && node.children.length > 0;
            const valueHtml = formatASTValue(node.value, color);
            const meta = [];
            if (node.line) meta.push(`行 ${node.line}`);
            if (node.column) meta.push(`列 ${node.column}`);
            const nodePath = [...path, siblingIndex];
            const breadcrumbLabel = formatASTBreadcrumbLabel(node);

            let html = `
                <div class="ast-node" data-depth="${depth}" data-path="${nodePath.join('/')}" data-label="${escapeHtml(breadcrumbLabel)}">
                    <div class="ast-node-branch">
                        <div class="ast-node-content" style="--ast-accent: ${color};">
                            <div class="ast-node-top">
                                <button class="ast-node-toggle ${hasChildren ? '' : 'is-empty'}" type="button" ${hasChildren ? '' : 'disabled'} aria-label="切换节点">
                                    ${hasChildren ? '▾' : '•'}
                                </button>
                                <div class="ast-node-main">
                                    <div class="ast-node-type">${escapeHtml(node.type)}</div>
                                    ${valueHtml}
                                    <div class="ast-node-line">${meta.join(' · ') || '行 ? · 列 ?'}</div>
                                </div>
                                <div class="ast-node-badge">${hasChildren ? `${node.children.length} 子节点` : '叶子'}</div>
                            </div>
                        </div>`;

            if (hasChildren) {
                html += '<div class="ast-children">';
                node.children.forEach((child, index) => {
                    html += renderAST(child, depth + 1, nodePath, index, node.children.length);
                });
                html += '</div>';
            }

            html += '</div></div>';
            return html;
        }

        function formatASTBreadcrumbLabel(node) {
            if (!node) return 'unknown';
            if (node.value === null || node.value === undefined || node.value === '') {
                return node.type;
            }
            if (typeof node.value === 'object') {
                return `${node.type}`;
            }
            return `${node.type}: ${String(node.value)}`;
        }

        function formatASTValue(value, color) {
            if (value === null || value === undefined) return '';
            if (typeof value === 'object') {
                const parts = Object.entries(value).map(([key, item]) => {
                    return `<span class="ast-value-key" style="color: ${color};">${escapeHtml(key)}</span>: ${escapeHtml(String(item))}`;
                });
                return `<div class="ast-node-value">{ ${parts.join(', ')} }</div>`;
            }
            return `<div class="ast-node-value">${escapeHtml(JSON.stringify(value))}</div>`;
        }

        function toggleAllASTNodes() {
            const tree = document.getElementById('ast-tree-root');
            const btn = document.getElementById('ast-toggle-all-btn');
            if (!tree || !btn) return;
            const shouldCollapse = !tree.classList.contains('is-collapsed-all');
            tree.classList.toggle('is-collapsed-all', shouldCollapse);
            btn.textContent = shouldCollapse ? '全部展开' : '全部折叠';
            tree.querySelectorAll('.ast-node').forEach(node => {
                const branch = node.firstElementChild;
                const content = branch ? branch.firstElementChild : null;
                const toggle = content ? content.querySelector('.ast-node-toggle') : null;
                if (!toggle || toggle.disabled) return;
                node.classList.toggle('collapsed', shouldCollapse);
                toggle.textContent = shouldCollapse ? '▸' : '▾';
            });
        }

        function bindASTInteractions() {
            const tree = document.getElementById('ast-tree-root');
            const breadcrumb = document.getElementById('ast-breadcrumb');
            const toggleBtn = document.getElementById('ast-toggle-all-btn');
            if (!tree) return;

            if (toggleBtn) {
                toggleBtn.onclick = (event) => {
                    event.preventDefault();
                    toggleAllASTNodes();
                };
            }

            tree.addEventListener('click', (event) => {
                const toggle = event.target.closest('.ast-node-toggle');
                if (!toggle || toggle.disabled) return;
                const node = toggle.closest('.ast-node');
                if (!node) return;
                node.classList.toggle('collapsed');
                toggle.textContent = node.classList.contains('collapsed') ? '▸' : '▾';
                event.stopPropagation();
            });

            tree.addEventListener('click', (event) => {
                const content = event.target.closest('.ast-node-content');
                if (!content) return;
                const toggle = event.target.closest('.ast-node-toggle');
                if (toggle && !toggle.disabled) return;
                const node = content.closest('.ast-node');
                if (!node) return;
                const nodeToggle = node.querySelector(':scope > .ast-node-branch .ast-node-toggle');
                if (nodeToggle && !nodeToggle.disabled) {
                    node.classList.toggle('collapsed');
                    nodeToggle.textContent = node.classList.contains('collapsed') ? '▸' : '▾';
                }
                highlightASTPath(tree, breadcrumb, node);
            });
        }

        function highlightASTPath(tree, breadcrumb, node) {
            const path = node.dataset.path || '';
            const segments = path ? path.split('/') : [];
            const pathSet = new Set();
            segments.reduce((acc, segment) => {
                const next = acc ? `${acc}/${segment}` : segment;
                pathSet.add(next);
                return next;
            }, '');

            tree.querySelectorAll('.ast-node').forEach(item => {
                const itemPath = item.dataset.path || '';
                item.classList.toggle('is-selected', itemPath === path);
                item.classList.toggle('is-path', pathSet.has(itemPath));
            });

            if (breadcrumb) {
                const labels = [];
                let current = node;
                while (current) {
                    labels.unshift(current.dataset.label || 'unknown');
                    current = current.parentElement ? current.parentElement.closest('.ast-node') : null;
                }
                breadcrumb.querySelector('.ast-breadcrumb-trail').innerHTML = labels
                    .map(label => `<span class="ast-breadcrumb-item">${escapeHtml(label)}</span>`)
                    .join('<span class="ast-breadcrumb-sep">/</span>');
            }
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

        function displayBasicBlocks(tacResult, originalTacResult) {
            const container = document.getElementById('content-basic-blocks');
            const optimizedBlocks = getBasicBlockData(tacResult);
            const originalBlocks = getBasicBlockData(originalTacResult);
            const removedCount = originalBlocks?.unreachable_count || 0;

            let html = '<div class="basic-block-algorithm">';
            html += '<div class="basic-block-algorithm-title">划分规则</div>';
            html += '<div class="basic-block-algorithm-steps">';
            html += '<span>1. 求入口语句：程序/函数入口、标号语句、转移目标、转移或停语句之后的下一语句。</span>';
            html += '<span>2. 每个入口到下一入口前，或到转移/停语句止，构成一个基本块。</span>';
            html += '<span>3. 没有被控制流到达的基本块标为不可达，优化后删除。</span>';
            html += '</div></div>';

            if (originalBlocks && tacResult?.basic_blocks) {
                html += '<div class="basic-block-compare">';
                html += renderBasicBlockSet('优化前基本块', originalBlocks, originalTacResult?.lines, true);
                html += renderBasicBlockSet('优化后基本块', optimizedBlocks, tacResult?.lines, false);
                html += '</div>';
            } else {
                html += renderBasicBlockSet('基本块', optimizedBlocks, tacResult?.lines, false);
            }

            if (removedCount > 0) {
                html += `<div class="basic-block-note">优化前检测到 ${removedCount} 条不可达 TAC，优化后已从代码流中删除。</div>`;
            }
            container.innerHTML = html;
        }

        function getBasicBlockData(tacResult) {
            if (tacResult?.basic_blocks) {
                return tacResult.basic_blocks;
            }
            const instructions = Array.isArray(tacResult?.instructions) ? tacResult.instructions : [];
            return buildBasicBlocksFallback(instructions);
        }

        function renderBasicBlockSet(title, blockData, lineCount, showUnreachable) {
            const blocks = Array.isArray(blockData?.blocks) ? blockData.blocks : [];
            let html = `<div class="basic-block-set">
                <div class="basic-block-summary">
                    <span>${escapeHtml(title)}</span>
                    <span>${blocks.length} 个基本块</span>`;
            if (typeof lineCount === 'number') {
                html += `<span>${lineCount} 条 TAC</span>`;
            }
            if (showUnreachable && blockData?.unreachable_count) {
                html += `<span class="basic-block-unreachable-count">${blockData.unreachable_count} 条不可达</span>`;
            }
            html += '</div>';

            if (!blocks.length) {
                html += '<div class="empty-state"><div class="empty-state-icon">🧱</div><p>没有可划分的基本块</p></div></div>';
                return html;
            }

            html += '<div class="basic-block-list">';
            blocks.forEach(block => {
                const unreachableClass = block.reachable === false ? ' is-unreachable' : '';
                html += `<div class="basic-block-card${unreachableClass}">
                    <div class="basic-block-header">
                        <div>
                            <span class="basic-block-title">B${block.id}</span>
                            <span class="basic-block-range">#${block.start} - #${block.end}</span>
                        </div>
                        <span class="basic-block-size">${block.size || block.instructions.length} 条</span>
                    </div>
                    <div class="basic-block-meta">
                        <span>入口：${escapeHtml((block.leader_reasons || []).join('、') || '入口语句')}</span>
                        <span>后继：${block.successors?.length ? block.successors.map(id => `B${id}`).join(', ') : '无'}</span>
                        ${block.reachable === false ? '<span class="basic-block-unreachable">不可达</span>' : ''}
                    </div>
                    <div class="assembly-code">`;
                block.instructions.forEach(instruction => {
                    const text = escapeHtml(instruction.text || formatTacInstruction(instruction));
                    const index = instruction.index ?? '';
                    const lineClass = instruction.op === 'label' ? 'assembly-label' : 'assembly-instruction';
                    html += `<div class="assembly-line basic-block-line">
                        <span class="basic-block-index">${index}</span>
                        <span class="${lineClass}">${text}</span>
                    </div>`;
                });
                html += '</div></div>';
            });
            html += '</div></div>';
            return html;
        }

        function buildBasicBlocksFallback(instructions) {
            if (!instructions.length) return { blocks: [], entry_indexes: [], unreachable_indexes: [], unreachable_count: 0 };

            const leaders = new Set([0]);
            const labelPositions = new Map();
            const branchOps = new Set(['goto', 'if_false']);
            const terminators = new Set(['goto', 'if_false', 'return', 'end_function']);

            instructions.forEach((instruction, index) => {
                if (instruction.op === 'label') {
                    leaders.add(index);
                }
                if (instruction.op === 'label' && instruction.result != null) {
                    labelPositions.set(instruction.result, index);
                }
            });

            instructions.forEach((instruction, index) => {
                if (terminators.has(instruction.op) && index + 1 < instructions.length) {
                    leaders.add(index + 1);
                }
                if (branchOps.has(instruction.op) && labelPositions.has(instruction.result)) {
                    leaders.add(labelPositions.get(instruction.result));
                }
            });

            const sortedLeaders = [...leaders].filter(i => i >= 0 && i < instructions.length).sort((a, b) => a - b);
            const blocks = [];
            for (let i = 0; i < sortedLeaders.length; i++) {
                const start = sortedLeaders[i];
                const end = i + 1 < sortedLeaders.length ? sortedLeaders[i + 1] : instructions.length;
                const blockInstructions = instructions.slice(start, end).map((instruction, offset) => ({
                    ...instruction,
                    index: start + offset
                }));
                if (blockInstructions.length) {
                    blocks.push({
                        id: blocks.length + 1,
                        start,
                        end: start + blockInstructions.length - 1,
                        size: blockInstructions.length,
                        leader_reasons: ['入口语句'],
                        reachable: true,
                        successors: [],
                        instructions: blockInstructions
                    });
                }
            }
            return { blocks, entry_indexes: sortedLeaders, unreachable_indexes: [], unreachable_count: 0 };
        }

        function formatTacInstruction(instruction) {
            if (!instruction) return '';
            if (instruction.text) return instruction.text;
            const { op, arg1, arg2, result } = instruction;
            if (op === 'function') return `function ${result}:`;
            if (op === 'end_function') return `end function ${result}`;
            if (op === 'label') return `${result}:`;
            if (op === 'goto') return `goto ${result}`;
            if (op === 'if_false') return `if_false ${arg1} goto ${result}`;
            if (op === 'return') return arg1 != null ? `return ${arg1}` : 'return';
            if (op === 'assign') return `${result} = ${arg1}`;
            if (op === 'arg') return `arg ${arg1}`;
            return `${result} = ${arg1} ${op} ${arg2}`;
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
                    lines: 7,
                    instructions: [
                        { op: 'function', result: 'add', text: 'function add:' },
                        { op: 'param_decl', result: 'a', text: 'param a' },
                        { op: 'param_decl', result: 'b', text: 'param b' },
                        { op: '+', arg1: 'a', arg2: 'b', result: 't1', text: 't1 = a + b' },
                        { op: 'assign', arg1: 't1', result: 'sum', text: 'sum = t1' },
                        { op: 'return', arg1: 'sum', text: 'return sum' },
                        { op: 'end_function', result: 'add', text: 'end function add' }
                    ],
                    basic_blocks: {
                        blocks: [
                            {
                                id: 1,
                                start: 0,
                                end: 4,
                                size: 5,
                                leader_reasons: ['函数入口'],
                                reachable: true,
                                successors: [],
                                instructions: [
                                    { op: 'function', result: 'add', text: 'function add:', index: 0 },
                                    { op: 'param_decl', result: 'a', text: 'param a', index: 1 },
                                    { op: 'param_decl', result: 'b', text: 'param b', index: 2 },
                                    { op: '+', arg1: 'a', arg2: 'b', result: 't1', text: 't1 = a + b', index: 3 },
                                    { op: 'return', arg1: 't1', text: 'return t1', index: 4 }
                                ]
                            }
                        ],
                        entry_indexes: [0],
                        unreachable_indexes: [],
                        unreachable_count: 0
                    }
                },
                tac_result: {
                    text: `function add:\nparam a\nparam b\nt1 = a + b\nreturn t1\nend function add`,
                    lines: 6,
                    instructions: [
                        { op: 'function', result: 'add', text: 'function add:' },
                        { op: 'param_decl', result: 'a', text: 'param a' },
                        { op: 'param_decl', result: 'b', text: 'param b' },
                        { op: '+', arg1: 'a', arg2: 'b', result: 't1', text: 't1 = a + b' },
                        { op: 'return', arg1: 't1', text: 'return t1' },
                        { op: 'end_function', result: 'add', text: 'end function add' }
                    ]
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
