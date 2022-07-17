import logging
from pathlib import Path

from lark import Lark

from qifparser.class_def import ClassDef

logger = logging.getLogger(__name__)
_here = Path(__file__).parent
_GRAMMER_DEF = open(_here / "grammer.lark", encoding="utf-8").read()
file_db = {}
class_db = {}

parser = None


def get_class_def(clsname):
    if clsname not in class_db:
        raise RuntimeError(f"class def not found: {clsname}")
    return class_db[clsname]


def is_class_defined(clsname):
    return clsname in class_db


def parse_file(xformer):
    global parser
    input_path = xformer.target_file
    if input_path in file_db:
        clsname = file_db[input_path]
        if clsname in class_db:
            logger.debug(f"*** file already loaded: {input_path}::{clsname}")
            return class_db[clsname]
        else:
            logger.debug(f"*** file is loading: {input_path}")
            return None

    logger.info(f"=== parsing file: {input_path} ===")
    file_db[input_path] = "*"
    with input_path.open("r") as f:
        text = f.read()

    if parser is None:
        parser = Lark(_GRAMMER_DEF, start="start")
    tree = parser.parse(text)

    result = xformer.transform(tree)
    if isinstance(result, ClassDef):
        clsname = result.curcls
        file_db[input_path] = clsname
        class_db[clsname] = result

    logger.debug(f"=== parsing file DONE: {input_path} ===")
    return result
