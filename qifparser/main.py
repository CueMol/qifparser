import sys
from lark import Lark
from lark import Transformer
from functools import reduce
import argparse

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
    parser.add_argument(
        "--infile", "-c", type=str, default=None, required=True
    )
    parser.add_argument(
        "--include", "-I", type=str, default=None, required=False, action="append"
    )
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    with open(args.infile, "r") as f:
        text = f.read()

    with open("./test1.lark", encoding="utf-8") as grammar:
        parser = Lark(grammar.read(), start="start")
        tree = parser.parse(text)
        print(tree.pretty())
        result = CalcTransformer().transform(tree)
        # print(result)

if __name__ == "__main__":
    main()
