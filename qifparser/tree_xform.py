import logging
from lark import Transformer, Token
from pathlib import Path

# from qifparser.parser import parse_file
from qifparser.class_def import ClassDef, PropertyDef, TypeObj, MethodDef, EnumDef

logger = logging.getLogger(__name__)
_pending_load = []
logger.debug(f"===== {_pending_load=}")


def add_pending_load(file_path):
    global _pending_load
    _pending_load.append(file_path)
    # print(f"add_pending_load {_pending_load=}")


def remove_pending_load(file_path):
    global _pending_load
    # print(f"remove_pending_load******************** {_pending_load=}")
    _pending_load = [i for i in _pending_load if i != file_path]


def get_pending_load():
    global _pending_load
    # print(f"get_pending_load******************** {_pending_load=}")
    return _pending_load


def remove_quot(inp):
    if inp[0] == '"' and inp[-1] == '"':
        return inp[1:-1]
    else:
        return inp


class TreeXform(Transformer):
    def __init__(self, target_file, top_srcdir, include_paths=None, moddef_mode=False):
        input_dir = target_file.parent
        self.target_file = target_file
        self.top_srcdir = top_srcdir
        self.args_inc_path = include_paths
        self.include_paths = [str(input_dir)]
        if include_paths is not None:
            self.include_paths.extend(include_paths)
        self.moddef_mode = moddef_mode

    def start(self, tree):
        class_def = None
        mod_def = None
        for item in tree:
            # print(f"start: {type(item)=} {item=}")
            assert item.data == "statement"
            assert len(item.children) >= 1
            val = item.children[0]
            if isinstance(val, ClassDef):
                if class_def is None:
                    class_def = val
                else:
                    raise RuntimeError("more than one runtime_class defs")

        if self.moddef_mode:
            if mod_def is None:
                raise RuntimeError("no module definition found")
            else:
                return mod_def
        else:
            if class_def is None:
                raise RuntimeError("no runtime_class definition found")
            else:
                return class_def

    def include_stmt(self, tree):
        # print(f"include_stmt: {tree}")
        token = tree[0]
        value = token.value
        # print(f"file: {value}")
        load_file = None
        for path in self.include_paths:
            chk_file = Path(path) / value
            if not chk_file.is_file():
                # print(f"not found: {chk_file}")
                continue
            # print(f"File OK: {chk_file}")
            load_file = chk_file
            break
        if load_file is None:
            raise RuntimeError(f"file not found: {value} in {self.include_paths}")

        if load_file == self.target_file:
            raise RuntimeError("reentrant include statement")
        # parse_file(self, load_file)
        add_pending_load(load_file)
        return f"import {load_file}"

    def iface_def_stmt(self, tree):
        # print("iface_def_stmt:")
        target = ClassDef()
        target.input_rel_path = self.target_file.relative_to(self.top_srcdir)
        for item in tree:
            # print(f"{item=}")
            # print(f"{item.data=}")
            if item.data == "class_name":
                # print("class name")
                # print(f"{item.children=}")
                cls_name = item.children[0].value
                target.set_class_name(cls_name)
            elif item.data == "extn_clause":
                # print(f"{item.children=}")
                cls_name = item.children[0].value
                target.extend_class(cls_name)
            elif item.data == "class_stmt":
                self.parse_class_stmt(item.children, target)
            else:
                raise RuntimeError(f"unknown token: {item.data}")

        # print(f"{target=}")
        return target

    class_attrib_names = (
        "scriptable",
        "abstract",
        "smartptr",
        "cloneable",
        "singleton",
    )

    def parse_class_stmt(self, tree, target):
        if isinstance(tree[0], PropertyDef):
            # print(f"property: {tree[0]}")
            target.add_property(tree[0])
            return

        if isinstance(tree[0], MethodDef):
            # print(f"method: {tree[0]}")
            target.add_method(tree[0])
            return

        if isinstance(tree[0], EnumDef):
            # print(f"enumdef: {tree[0]}")
            target.add_enumdef(tree[0])
            return

        # print(f"{tree=}")
        stmt_name = tree[0].data
        # print(f"=== {stmt_name=}")
        if stmt_name == "client_header_stmt":
            header_name = tree[0].children[0].value
            # print(f"{header_name=}")
            target.cli_header_name = remove_quot(header_name)
        elif stmt_name == "client_name_stmt":
            cxx_name = tree[0].children[0].value
            # print(f"{cxx_name=}")
            target.cxx_name = cxx_name
        elif stmt_name == "dllexport_stmt":
            # TODO: impl
            logger.warning("dllexport ignored")
        elif stmt_name in self.class_attrib_names:
            # Attributes
            option = stmt_name
            target.add_option(option)
        elif stmt_name == "using_stmt":
            type_ref = tree[0].children[0].children[0].value
            logger.debug(f"using {type_ref=}")
            target.append_refer_qif(type_ref)
        elif stmt_name == "default_propval_stmt":
            assert len(tree[0].children) == 2
            prop_name_node, prop_val_node = tree[0].children
            prop_name = prop_name_node.children[0].value
            prop_val = prop_val_node.children[0].value
            logger.debug(f"default {prop_name=}")
            logger.debug(f"default {prop_val=}")
            if prop_name not in target.properties:
                raise RuntimeError(f"undefined prop ({prop_name}) in default decl")
            prop_def = target.properties[prop_name]
            prop_def.default_cxx_rval = prop_val
        else:
            raise RuntimeError(f"unknown statement: {stmt_name}")

    def property_stmt(self, tree):
        # print(f"property {tree=}")
        prop = PropertyDef()
        for item in tree:
            # print(f"property {item.data=}")
            if item.data == "property_type":
                prop_type = item.children[0]
                # print(f"proprety type : {prop_type}")
                prop.prop_type = prop_type
            elif item.data == "property_name":
                prop_name = item.children[0].value
                # print(f"proprety name : {prop_name}")
                prop.prop_name = prop_name
                if prop.prop_type is not None:
                    prop.prop_type.name = prop_name
            elif item.data == "prop_redirect_clause":
                assert len(item.children) == 2
                getter, setter = item.children
                assert getter.data == "getter_name"
                getter_name = getter.children[0].value
                assert setter.data == "setter_name"
                setter_name = setter.children[0].value
                # print(f"{getter_name=}")
                # print(f"{setter_name=}")
                prop.redirect = True
                prop.cxx_getter_name = getter_name
                prop.cxx_setter_name = setter_name
            elif item.data == "prop_access_clause":
                assert len(item.children) == 1
                assert isinstance(item.children[0], Token)
                field_name = item.children[0].value
                # print(f"{field_name=}")
                prop.redirect = False
                prop.cxx_field_name = field_name
            elif item.data == "prop_modif_list":
                for modif in item.children:
                    # print(f"modifier: {modif.data}")
                    prop.modifiers.append(modif.data)

        return prop

    def method_stmt(self, tree):
        method = MethodDef()
        for item in tree:
            # print(f"method {item.data=}")
            if item.data == "return_type":
                return_type = item.children[0]
                # print(f"return type : {return_type}")
                method.return_type = return_type
            elif item.data == "method_name":
                method_name = item.children[0].value
                # print(f"method name : {method_name}")
                method.method_name = method_name
            elif item.data == "method_arg_list":
                # print(f"{item=}")
                method.args = self.make_method_args(item.children)
            elif item.data == "mth_redirect_clause":
                # print(f"Method redirect {item=}")
                method.redirect = True
                method.cxx_name = item.children[0].value

        return method

    def make_method_args(self, tree):
        args = []
        for item in tree:
            assert item.data == "method_arg"
            assert len(item.children) >= 1
            arg = item.children[0]
            # if len(item.children) >= 2:
            #     name = item.children[1]
            #     arg.name = name.value
            # XXX: perl ver compat
            arg.name = ""
            args.append(arg)
            # print(f"method_arg {arg=}")
        return args

    def enumdef_stmt(self, tree):
        logger.debug(f"{tree=}")
        target = EnumDef()
        for item in tree:
            logger.debug(f"enumdef {item=}")
            if item.data == "enum_name":
                name = item.children[0].value
                # print(f"enum name : {name}")
                target.enum_name = name
            elif item.data == "enum_decl_stmt":
                # print(f"{item=}")
                assert len(item.children) >= 2
                enumkey = item.children[0].children[0].value
                enumdef = item.children[1].children[0].value
                # print(f"{enumkey=}")
                # print(f"{enumdef=}")
                if enumkey in target.enum_data:
                    raise RuntimeError(
                        f"enum {enumkey} already defined in {target.enum_name}"
                    )
                target.enum_data[enumkey] = enumdef
            elif item.data == "enum_alias_def":
                alias_def = item.children[0].value
                target.enum_alias = alias_def
                logger.debug(f"alias: {alias_def}")
                break
            else:
                raise RuntimeError(f"unknown node: {item=}")

        return target

    def type_name(self, tree):
        item = tree[0]
        if len(item.children) == 0:
            result = TypeObj(type_name=item.data)
        else:
            assert item.data == "object_type_name"
            type_spec = item.children[0].data
            obj_type = item.children[0].children[0].value
            if type_spec == "object_type_spec":
                ref = False
            elif type_spec == "object_reftype_spec":
                ref = True
            else:
                raise RuntimeError(f"unknown type spec: {type_spec}")
            result = TypeObj(type_name="object", ref=ref, obj_type=obj_type)
        # print(f"type_name: {result}")
        return result

    # def attribute_stmt(self, tree):
    #     print(f"class_attribute: {tree[0].data}")
    #     # print(f"class_attribute: {dir(tree[0])}")
    #     return tree[0].data
