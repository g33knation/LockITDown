import ast
import logging

class ASTScanner:
    @staticmethod
    def scan_content(content: str) -> list:
        vulnerabilities = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Not valid Python code, skip AST analysis
            return []

        for node in ast.walk(tree):
            # 1. Detect Dangerous Function Calls (eval, exec)
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec']:
                        # Check if it's NOT safe (simple heuristic)
                        # We accept ast.literal_eval, but here checking raw 'eval' name
                        vulnerabilities.append({
                            "id": f"ast-call-{node.lineno}-{node.func.id}",
                            "line": node.lineno,
                            "content": f"{node.func.id}(...)",
                            "type": "Insecure Function (AST)",
                            "severity": "MEDIUM",
                            "description": f"Dangerous usage of {node.func.id}() detected via AST."
                        })

            # 2. Detect Hardcoded Secrets in Assignments
            # Looking for: variable_name = "literal_string"
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        # Check if variable name looks sensitive
                        if any(s in var_name for s in ['password', 'secret', 'api_key', 'access_key', 'token']):
                            # Check if value is a string literal (Constant in Py3.8+, Str in older)
                            value_node = node.value
                            is_string_literal = False
                            
                            if isinstance(value_node, ast.Constant) and isinstance(value_node.value, str):
                                is_string_literal = True
                                str_val = value_node.value
                            elif isinstance(value_node, ast.Str): # Legacy Python AST
                                is_string_literal = True
                                str_val = value_node.s
                                
                            if is_string_literal:
                                # Heuristic: Ignore short strings or placeholders
                                if len(str_val) > 8 and "env" not in str_val and "getenv" not in str_val:
                                     vulnerabilities.append({
                                        "id": f"ast-secret-{node.lineno}-{target.id}",
                                        "line": node.lineno,
                                        "content": f"{target.id} = \"***\"", 
                                        "type": "Hardcoded Secret (AST)",
                                        "severity": "HIGH",
                                        "description": f"Variable '{target.id}' appears to contain a hardcoded secret."
                                    })

        return vulnerabilities
