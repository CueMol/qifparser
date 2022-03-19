import argparse
from pathlib import Path
from qifparser.tree_xform import TreeXform
from qifparser.parser import parse_file


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

    parse_file(TreeXform, input_path, include_paths=args.include)


if __name__ == "__main__":
    main()
