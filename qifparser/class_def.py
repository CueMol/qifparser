import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ClassDef:
    curcls: Optional[str] = None
    qifname: Optional[str] = None
    supcls: Optional[str] = None
    extends: List[str] = field(default_factory=list)
    extends_wrapper: List[str] = field(default_factory=list)
    cli_header_name: str = ""
    cxx_name: str = ""
    input_rel_path: Optional[str] = None
    dllexport: str = ""

    options: List[str] = field(default_factory=list)
    refers: Set[str] = field(default_factory=set)

    properties: Dict[str, Any] = field(default_factory=dict)
    methods: Dict[str, Any] = field(default_factory=dict)
    enumdefs: Dict[str, Any] = field(default_factory=dict)

    def set_class_name(self, cls_name):
        self.curcls = cls_name
        self.qifname = cls_name

    def extend_class(self, supcls):
        self.supcls = supcls
        self.extends = [supcls]
        self.extends_wrapper = [f"{supcls}_wrap"]

        # Append refer QIDL
        self.append_refer_qif(supcls)

    def add_option(self, opt):
        self.options.append(opt)

    def add_property(self, prop_def):
        prop_name = prop_def.prop_name
        if prop_name in self.properties:
            raise RuntimeError(f"property {prop_name} already defined in {self.curcls}")
        self.properties[prop_name] = prop_def

        # Append refer QIDL
        self.append_refer_typeobj(prop_def.prop_type)

    def add_method(self, method_def):
        method_name = method_def.method_name
        if method_name in self.methods:
            raise RuntimeError(f"method {method_name} already defined in {self.curcls}")
        self.methods[method_name] = method_def

        # Append refer QIDL
        self.append_refer_typeobj(method_def.return_type)
        for item in method_def.args:
            self.append_refer_typeobj(item)

    def add_enumdef(self, enum_def):
        name = enum_def.enum_name
        if name in self.methods:
            raise RuntimeError(f"enumdef {name} already defined in {self.curcls}")
        self.enumdefs[name] = enum_def

    def is_singleton(self):
        return "singleton" in self.options

    def is_smart_ptr(self):
        return "smartptr" in self.options

    def is_cloneable(self):
        return "cloneable" in self.options

    def get_wp_clsname(self):
        # TODO: configurable??
        return f"{self.qifname}_wrap"

    def append_refer_qif(self, qifname):
        if qifname == self.qifname:
            return
        if qifname in self.refers:
            return
        logger.debug(f"refer QIF type: {qifname}")
        self.refers.add(qifname)

    def append_refer_typeobj(self, type_obj):
        if type_obj.type_name != "object":
            return
        refcls = type_obj.obj_type
        self.append_refer_qif(refcls)

    def get_wp_hdr_fname(self):
        if self.input_rel_path.parent is not None:
            return self.input_rel_path.parent / f"{self.qifname}_wrap.hpp"
        else:
            return Path(f"{self.qifname}_wrap.hpp")

    def get_cli_hdr_fname(self):
        if self.cli_header_name is not None:
            return self.cli_header_name
        else:
            return f"{self.qifname}.hpp"


@dataclass
class TypeObj:
    type_name: str
    ref: bool = False
    obj_type: Optional[str] = None
    name: str = ""


@dataclass
class PropertyDef:
    prop_name: Optional[str] = None
    prop_type: Optional[TypeObj] = None

    redirect: bool = False
    cxx_getter_name: Optional[str] = None
    cxx_setter_name: Optional[str] = None
    cxx_field_name: Optional[str] = None
    default_cxx_rval: Optional[str] = None
    modifiers: List[str] = field(default_factory=list)

    def is_readonly(self):
        return "readonly" in self.modifiers


@dataclass
class MethodDef:
    method_name: Optional[str] = None
    return_type: Optional[TypeObj] = None
    args: List[TypeObj] = field(default_factory=list)

    redirect: bool = False
    cxx_name: Optional[str] = None

    def get_cxx_name(self):
        if self.cxx_name is not None:
            return self.cxx_name
        else:
            return self.method_name


@dataclass
class EnumDef:
    enum_name: Optional[str] = None
    enum_data: Dict[str, str] = field(default_factory=dict)
    enum_alias: Optional[str] = None
