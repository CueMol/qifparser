from lark import Lark

import argparse
from pathlib import Path
from qifparser.tree_xform import TreeXform

# import sys
# from functools import reduce


_here = Path(__file__).parent
_LARK_PARSER = open(_here / "grammer.lark", encoding="utf-8")


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-c", type=str, default=None, required=True)
    parser.add_argument("--output", "-o", type=str, default=None, required=True)
    parser.add_argument(
        "--include", "-I", type=str, default=None, required=False, action="append"
    )
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    print(f"{args.input=}")
    print(f"{args.output=}")
    print(f"{args.include=}")
    input_path = Path(args.input)
    input_dir = input_path.parent
    with input_path.open("r") as f:
        text = f.read()
    print(f"{text=}")
    print(f"{_LARK_PARSER=}")

    parser = Lark(_LARK_PARSER.read(), start="start")
    tree = parser.parse(text)
    print(tree.pretty())

    result = TreeXform(input_dir=input_dir, include_paths=args.include).transform(tree)
    print(result)


if __name__ == "__main__":
    main()
