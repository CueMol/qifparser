import logging
import argparse
from pathlib import Path
from qifparser.tree_xform import TreeXform
from qifparser.parser import parse_file
from qifparser.cxx_wrapper import gen_cxx_source
from qifparser.tree_xform import get_pending_load, remove_pending_load


logger = logging.getLogger(__name__)


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-c", type=str, default=None, required=True)
    parser.add_argument("--output", "-o", type=str, default=None, required=True)
    parser.add_argument(
        "--include", "-I", type=str, default=None, required=False, action="append"
    )
    # mode_choice = ["cxx_src", "cxx_hdr", "mod", "js", "ts", "py"]
    parser.add_argument("--mode", "-m", type=str, default="cxx_src", required=False)

    parser.add_argument("--top_srcdir", type=str, default=None, required=True)
    parser.add_argument("--top_builddir", type=str, default=None, required=True)

    return parser


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(levelname)1.1s %(module)s:%(funcName)s] %(message)s",
    )

    parser = create_parser()
    args = parser.parse_args()

    logger.info(f"{args.input=}")
    logger.info(f"{args.output=}")
    logger.info(f"{args.include=}")

    top_srcdir = Path(args.top_srcdir).resolve()
    top_builddir = Path(args.top_builddir).resolve()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = (top_srcdir / input_path).resolve()

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (top_builddir / output_path).resolve()
    # input_rel_path = input_path.relative_to(top_srcdir)
    # logger.info(f"input relative path: {input_rel_path}")

    xformer = TreeXform(
        target_file=input_path, top_srcdir=top_srcdir, include_paths=args.include
    )

    result = parse_file(xformer)

    while True:
        pd = get_pending_load()
        if len(pd) == 0:
            logger.info("all pending files loaded")
            break
        for item in pd:
            xfm = TreeXform(
                target_file=item, top_srcdir=top_srcdir, include_paths=args.include
            )
            parse_file(xfm)
            remove_pending_load(item)

    if args.mode == "cxx_src":
        logger.debug(f"{result=}")
        gen_cxx_source(result, output_path)


if __name__ == "__main__":
    main()
