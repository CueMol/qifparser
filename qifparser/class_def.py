from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ClassDef:
    curcls: Optional[str] = None
    qifname: Optional[str] = None
    supcls: Optional[str] = None
    extends: List[str] = field(default_factory=list)
    extends_wrapper: List[str] = field(default_factory=list)
    options: List[str] = field(default_factory=list)
    decl_hdr: str = ""
    cxx_name: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    methods: Dict[str, Any] = field(default_factory=dict)
    enumdefs: Dict[str, str] = field(default_factory=dict)

    def set_class_name(self, cls_name):
        self.curcls = cls_name
        self.qifname = cls_name

    def extend_class(self, supcls):
        self.supcls = supcls
        self.extends = [supcls]
        self.extends_wrapper = [f"{supcls}_wrap"]
        # TODO: append refer QIDL

    def add_option(self, opt):
        self.options.append(opt)

    def add_property(self, prop_def):
        prop_name = prop_def.prop_name
        if prop_name in self.properties:
            raise RuntimeError(f"property {prop_name} already defined in {self.curcls}")
        self.properties[prop_name] = prop_def

    def add_method(self, method_def):
        method_name = method_def.method_name
        if method_name in self.methods:
            raise RuntimeError(f"method {method_name} already defined in {self.curcls}")
        self.methods[method_name] = method_def

    def add_enumdef(self, enum_def):
        name = enum_def.enum_name
        if name in self.methods:
            raise RuntimeError(f"enumdef {name} already defined in {self.curcls}")
        self.enumdefs[name] = enum_def


@dataclass
class TypeObj:
    type_name: Optional[str] = None
    ref: bool = False
    obj_type: Optional[str] = None


@dataclass
class PropertyDef:
    prop_name: Optional[str] = None
    prop_type: Optional[TypeObj] = None

    redirect: bool = False
    cxx_getter_name: Optional[str] = None
    cxx_setter_name: Optional[str] = None
    cxx_field_name: Optional[str] = None

    modifiers: List[str] = field(default_factory=list)


@dataclass
class MethodDef:
    method_name: Optional[str] = None
    return_type: Optional[TypeObj] = None
    args: List[TypeObj] = field(default_factory=list)

    redirect: bool = False
    cxx_name: Optional[str] = None


@dataclass
class EnumDef:
    enum_name: Optional[str] = None
    enum_data: Dict[str, str] = field(default_factory=dict)
