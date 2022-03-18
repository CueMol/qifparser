from dataclasses import dataclass, field
from typing import Optional, List


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

    def __init__(self):
        self.curcls = None
        self.supcls = None
        self.options = []

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
