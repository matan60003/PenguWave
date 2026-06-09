import ast
import os

def check_function_lengths(directory, max_lines=60):
    long_functions = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
                
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start_line = node.lineno
                    end_line = node.end_lineno
                    length = end_line - start_line + 1
                    
                    if length > max_lines:
                        long_functions.append({
                            'file': filepath,
                            'function': node.name,
                            'length': length,
                            'start': start_line,
                            'end': end_line
                        })
                        
    return long_functions

if __name__ == '__main__':
    directory = 'backend-service/app'
    long_functions = check_function_lengths(directory)
    
    if long_functions:
        print(f"Found {len(long_functions)} functions longer than 60 lines:")
        for lf in long_functions:
            print(f"{lf['file']}: {lf['function']} ({lf['length']} lines, {lf['start']}-{lf['end']})")
    else:
        print("All functions are under 60 lines.")
