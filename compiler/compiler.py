from typing import Dict, Any
from .lexer import EnhancedLexer
from .parser import EnhancedParser
from .semantic import EnhancedSemanticAnalyzer
from .optimizer import Optimizer
from .codegen import EnhancedCodeGenerator

class Compiler:
    """编译器主类"""
    
    def __init__(self):
        self.lexer = None
        self.parser = None
        self.semantic_analyzer = None
        self.optimizer = None
        self.code_generator = None
    
    def compile(self, source_code: str) -> Dict[str, Any]:
        """编译源代码"""
        result = {
            'success': True,
            'source_code': source_code,
            'lexer_result': None,
            'parser_result': None,
            'semantic_result': None,
            'optimization_result': None,
            'code_result': None,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 词法分析
            self.lexer = EnhancedLexer(source_code)
            lexer_result = self.lexer.analyze()
            result['lexer_result'] = lexer_result
            result['warnings'].extend(lexer_result.get('warnings', []))
            
            if lexer_result.get('errors'):
                result['errors'].extend(lexer_result['errors'])
                result['success'] = False
                return result
            
            # 语法分析
            self.parser = EnhancedParser(self.lexer.tokenize())
            ast = self.parser.parse()
            result['parser_result'] = ast.to_dict()
            result['warnings'].extend([{'message': w} for w in self.parser.warnings])
            
            if self.parser.errors:
                result['errors'].extend(self.parser.errors)
                result['success'] = False
            
            # 语义分析
            if result['success']:
                self.semantic_analyzer = EnhancedSemanticAnalyzer()
                semantic_result = self.semantic_analyzer.analyze(ast)
                result['semantic_result'] = semantic_result
                result['warnings'].extend([{'message': w} for w in semantic_result.get('warnings', [])])
                
                if semantic_result.get('errors'):
                    result['errors'].extend(semantic_result['errors'])
                    result['success'] = False
                
                # 代码优化
                self.optimizer = Optimizer()
                optimized_ast = self.optimizer.optimize(ast)
                result['optimization_result'] = {
                    'applied': self.optimizer.optimizations_applied,
                    'optimized_ast': optimized_ast.to_dict()
                }
                
                # 代码生成
                self.code_generator = EnhancedCodeGenerator()
                assembly_code = self.code_generator.generate(optimized_ast)
                result['code_result'] = {
                    'assembly': assembly_code,
                    'lines': len(assembly_code.split('\n'))
                }
        
        except Exception as e:
            result['success'] = False
            result['errors'].append({'message': str(e)})
        
        return result
