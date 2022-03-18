from lark import Transformer
from pathlib import Path

from qifparser.parser import parse_file
from qifparser.class_def import ClassDef


class TreeXform(Transformer):
    def __init__(self, input_dir, include_paths=None):
        self.args_inc_path = include_paths
        self.include_paths = [str(input_dir)]
        if include_paths is not None:
            self.include_paths = include_paths

    def include_stmt(self, tree):
        # print(f"include_stmt: {tree}")
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

        # result = parse_file(TreeXform, load_file, self.args_inc_path)
        # print(f"parse file {value} OK: {result}")
        return f"import {value}"

    def iface_def_stmt(self, tree):
        print("iface_def_stmt:")
        target = ClassDef()
        for item in tree:
            print(f"{item=}")
            print(f"{item.data=}")
            if item.data == "class_name":
                print("class name")
                print(f"{item.children=}")
                cls_name = item.children[0].value
                target.set_class_name(cls_name)

            elif item.data == "extn_clause":
                print(f"{item.children=}")
                cls_name = item.children[0].value
                target.extend_class(cls_name)

            elif item.data == "class_stmt":
                self.parse_class_stmt(item.children, target)

            if not hasattr(item, "value"):
                continue
            print(f"{item.value=}")

        print(f"{target=}")
        return f"class {0}"

    def parse_class_stmt(self, tree, target):
        stmt_name = tree[0].data
        print(f"=== {stmt_name=}")
        if stmt_name == "client_header_stmt":
            header_name = tree[0].children[0].value
            print(f"{header_name=}")
            target.decl_hdr = header_name
        elif stmt_name == "client_name_stmt":
            cxx_name = tree[0].children[0].value
            print(f"{cxx_name=}")
            target.cxx_name = cxx_name
        elif stmt_name == "attribute_stmt":
            option = tree[0].children[0].data
            print(f"{option=}")
            target.add_option(option)
        elif stmt_name == "property_stmt":
            self.parse_prop_stmt(tree[0].children, target)
        elif stmt_name == "method_stmt":
            print("method def")
        elif stmt_name == "enumdef_stmt":
            print("enumdef def")
        else:
            raise RuntimeError(f"unknown statement: {stmt_name}")

    def parse_prop_stmt(self, tree, target):
        print(f"property {tree=}")

    # def attribute_stmt(self, tree):
    #     print(f"class_attribute: {tree[0].data}")
    #     # print(f"class_attribute: {dir(tree[0])}")
    #     return tree[0].data
