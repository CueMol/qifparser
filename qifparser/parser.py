from lark import Lark
from pathlib import Path

_here = Path(__file__).parent

_GRAMMER_DEF = open(_here / "grammer.lark", encoding="utf-8").read()

file_db = {}
class_db = {}


def get_class_def(clsname):
    return class_db[clsname]


def is_class_defined(clsname):
    return clsname in class_db


def parse_file(xform_cls, input_path, include_paths=None):
    if input_path in file_db:
        clsname = file_db[input_path]
        if clsname in class_db:
            print(f"*** file already loaded: {input_path}::{clsname}")
            return class_db[clsname]
        else:
            print(f"*** file is loading: {input_path}")
            return None

    print(f"=== parsing file: {input_path} ===")
    file_db[input_path] = "*"
    with input_path.open("r") as f:
        text = f.read()

    parser = Lark(_GRAMMER_DEF, start="start")
    tree = parser.parse(text)

    xformer = xform_cls(target_file=input_path, include_paths=include_paths)
    result = xformer.transform(tree)
    clsname = result.curcls

    file_db[input_path] = clsname
    class_db[clsname] = result

    print(f"=== parsing file DONE: {input_path} ===")
    return result
