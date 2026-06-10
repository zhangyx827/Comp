from .core import ASTNode

class Optimizer:
    def __init__(self):
        self.optimizations_applied = []
    
    def optimize(self, ast: ASTNode) -> ASTNode:
        ast = self.constant_folding(ast)
        ast = self.dead_code_elimination(ast)
        return ast
    
    def constant_folding(self, node: ASTNode) -> ASTNode:
        if node is None:
            return None
        
        if node.type == 'variable_declarations':
            node.children = [self.constant_folding(c) for c in node.children]
            return node
        
        if node.type == 'binary_expression':
            node.children = [self.constant_folding(c) for c in node.children]
            
            if (node.children[0] and node.children[0].type == 'integer_literal' and
                node.children[1] and node.children[1].type == 'integer_literal'):
                
                left_val = node.children[0].value['value']
                right_val = node.children[1].value['value']
                op = node.value['operator']
                
                try:
                    if op == '+': result = left_val + right_val
                    elif op == '-': result = left_val - right_val
                    elif op == '*': result = left_val * right_val
                    elif op == '/': result = left_val // right_val if right_val != 0 else 0
                    elif op == '%': result = left_val % right_val if right_val != 0 else 0
                    else: return node
                    
                    self.optimizations_applied.append(f"常量折叠: {left_val} {op} {right_val} = {result}")
                    return ASTNode('integer_literal', [], {'value': result}, node.line, node.column)
                except:
                    return node
        
        node.children = [self.constant_folding(c) for c in node.children]
        return node
    
    def dead_code_elimination(self, node: ASTNode) -> ASTNode:
        return node
