from lark import Transformer
from pathlib import Path

from qifparser.parser import parse_file


class TreeXform(Transformer):
    def __init__(self, input_dir, include_paths=None):
        self.args_inc_path = include_paths
        self.include_paths = [str(input_dir)]
        if include_paths is not None:
            self.include_paths = include_paths

    def include_stmt(self, tree):
        print(f"include_stmt: {tree}")
        token = tree[0]
        value = token.value
        print(f"file: {value}")
        load_file = None
        for path in self.include_paths:
            chk_file = Path(path) / value
            if not chk_file.is_file():
                print(f"not found: {chk_file}")
                continue
            print(f"File OK: {chk_file}")
            load_file = chk_file
            break
        if load_file is None:
            raise RuntimeError(f"file not found: {value}")

        result = parse_file(TreeXform, load_file, self.args_inc_path)
        print(f"parse file {value} OK: {result}")
        return result
