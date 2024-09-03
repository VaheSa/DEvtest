import os
import ast
import subprocess
import hashlib
import sys

executed_commands = set()


def read_files(directory):
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    python_files.sort()

    return python_files


def execute_commands(cmds, file_path):
    # print(f"Executing commands from file: {file_path}")
    for cmd in cmds:
        if not isinstance(cmd, str):
            continue
        cmd_hash = hashlib.md5(cmd.encode()).hexdigest()
        if cmd_hash in executed_commands:
            print(f"Command already executed: {cmd}")
        else:
            try:
                subprocess.run(cmd, shell=True, check=False)
                executed_commands.add(cmd_hash)
            except subprocess.CalledProcessError as e:
                pass
                # print(f"Failed to execute command: {cmd}. Error: {e}")


def extract_cmds_from_file(file_path):

    # print(f"Extracting commands from file: {file_path}")
    with open(file_path, 'r') as file:
        found_values = []
        context = {}
        node = ast.parse(file.read(), filename=file_path)

    find_list_variables(node, "CMDS", found_values, context)

    return found_values


def find_list_variables(node, target_name, found_values, context):
    """Recursively find all instances of a list variable with the target name."""
    if isinstance(node, ast.Assign):
        if isinstance(node.value, ast.List):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == target_name:
                    list_value = extract_list_value(node.value, context)
                    for value in list_value:

                        found_values.append(value)

        else:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    context[target.id] = extract_value(node.value, context)

    # Recursively visit all child nodes
    for child in ast.iter_child_nodes(node):
        find_list_variables(child, target_name, found_values, context)


def extract_list_value(list_node, context):
    """Extracts the values from an ast.List node."""
    x = [extract_value(element, context) for element in list_node.elts]

    return x


def extract_value(node, context):
    """Extract the value from different types of AST nodes."""
    if isinstance(node, ast.Constant):  # Python 3.8+
        return node.value
    elif isinstance(node, ast.BinOp):
        left = str(extract_value(node.left, context))
        op = extract_operator(node.op)
        right = str(extract_value(node.right, context))
        return eval(f"{repr(left)} {op} {repr(right)}")
    elif isinstance(node, ast.Name):
        return context.get(node.id, node.id)
    elif isinstance(node, ast.List):
        return extract_list_value(node,context)
    else:
        pass
        # print(f"Unsupported node type: {type(node)}")
    return None


def extract_operator(op_node):
    operators = {
        ast.Add: '+',
    }
    return operators[type(op_node)]


if __name__ == '__main__':
    directory = './'
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    python_files = read_files(directory)
    for file_path in python_files:
        cmds = extract_cmds_from_file(file_path)
        execute_commands(cmds, file_path)


