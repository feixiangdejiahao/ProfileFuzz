import ast


class ScopeFinder(ast.NodeVisitor):
    def __init__(self):
        self.scopes = []

    def visit_For(self, node):
        self.scopes.append(['For Loop Body', node.lineno, node.end_lineno])
        self.generic_visit(node)

    def visit_While(self, node):
        self.scopes.append(['While Loop Body', node.lineno, node.end_lineno])
        self.generic_visit(node)

    def visit_If(self, node):
        self.scopes.append(['If Statement Body', node.lineno, node.end_lineno])
        self.generic_visit(node)


def find_scopes(code):
    tree = ast.parse(code)
    finder = ScopeFinder()
    finder.visit(tree)
    return finder.scopes


# Example Python code to test the function
example_code = """
def example_function():
    for i in range(5):
        if i > 2:
            print(i)
        else:
            print(i + 1)

class ExampleClass:
    def class_method(self):
        while True:
            pass
"""

# Find scopes in the example code
scopes = find_scopes(example_code)
scopes
