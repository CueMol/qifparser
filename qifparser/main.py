from lark import Transformer
from lark import Lark

import argparse
from pathlib import Path

# import sys
# from functools import reduce


_here = Path(__file__).parent
_LARK_PARSER = open(_here / "grammer.lark", encoding="utf-8")


class CalcTransformer(Transformer):
    def __init__(self, include_path=None):
        if include_path is not None:
            self.include_path = []
        else:
            self.include_path = include_path

    def include_stmt(self, tree):
        print(f"include_stmt: {tree}")


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
    with open(args.input, "r") as f:
        text = f.read()
    print(f"{text=}")
    print(f"{_LARK_PARSER=}")

    parser = Lark(_LARK_PARSER.read(), start="start")
    tree = parser.parse(text)
    print(tree.pretty())
    #     result = CalcTransformer().transform(tree)
    #     # print(result)


if __name__ == "__main__":
    main()
