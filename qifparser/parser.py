from lark import Lark
from pathlib import Path

_here = Path(__file__).parent

_LARK_PARSER = Lark(
    open(_here / "grammer.lark", encoding="utf-8").read(), start="start"
)

file_db = {}


def parse_file(xform_cls, input_path, include_paths=None):
    if str(input_path) in file_db:
        print(f"file already loaded: {input_path}")
        return file_db[str(input_path)]

    input_dir = input_path.parent
    with input_path.open("r") as f:
        text = f.read()

    # parser = Lark(_LARK_PARSER.read(), start="start")
    tree = _LARK_PARSER.parse(text)
    # print(tree.pretty())

    result = xform_cls(input_dir=input_dir, include_paths=include_paths).transform(tree)
    file_db[input_path] = result
    return result
