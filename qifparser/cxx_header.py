import logging
from qifparser.parser import get_class_def
from qifparser._version import __version__
from qifparser.base_srcgen import BaseSrcGen
from qifparser.cxx_wrapper import (
    mk_get_fname,
    mk_set_fname,
    make_prop_signature,
    make_method_signature,
)

logger = logging.getLogger(__name__)


class CxxHdrGen(BaseSrcGen):
    def generate_impl(self, output_path):

        target = self.cls
        qif_name = target.qifname
        cls = get_class_def(qif_name)
        cxx_cli_clsname = cls.cxx_name
        # cxx_wp_clsname = cls.get_wp_clsname()
        print(f"generating C++ wrapper ({cxx_cli_clsname}) hdr for {qif_name}")

        self._gen_preamble()
        self._gen_class_decl()

    def _gen_preamble(self):
        cls = self.cls
        # qif_name = cls.qifname
        cpp_decl_hdrname = cls.get_cli_hdr_fname()

        self.wr("//")
        self.wr(f"// Auto-generated by qifparser {__version__}. Don't edit.\n")
        self.wr("//")
        self.wr("\n")
        # self.wr("#ifndef $hdr_defined_macro\n")
        # self.wr("#define $hdr_defined_macro\n")
        self.wr("#pragma once\n")
        self.wr("\n")

        self.wr("#include <qlib/LClassUtils.hpp>\n")
        self.wr("#include <qlib/LWrapper.hpp>\n")
        self.wr("#include <qlib/SingletonBase.hpp>\n")
        self.wr("\n")

        self.wr(f'#include "{cpp_decl_hdrname}"\n')
        self.wr("\n")

    def _gen_class_decl(self):
        cls = self.cls
        cpp_cli_clsname = cls.cxx_name
        cpp_wp_clsname = cls.get_wp_clsname()

        if cls.is_singleton():  # contains(ropts, "singleton"):
            clscls_super = f"qlib::LSingletonSpecificClass<{cpp_cli_clsname}>"
        elif cls.is_smart_ptr():  # contains(ropts, "smartptr"):
            clscls_super = f"qlib::LSmartPtrSupportClass<{cpp_cli_clsname}>"
        else:
            clscls_super = f"qlib::LSpecificClass<{cpp_cli_clsname}>"

        self.wr("//\n")
        self.wr(f"// Wrapper class for {cpp_cli_clsname}\n")
        self.wr("//\n")
        self.wr("\n")
        self.wr(f"class {cpp_wp_clsname} :\n")
        self.wr(f"  public {clscls_super},\n")
        self.wr(f"  public qlib::SingletonBase<{cpp_wp_clsname}>,\n")
        self.wr("  public qlib::LWrapperImpl\n")
        self.wr("{\n")

        # Declare typedefs
        self.wr("public:\n")
        self.wr(f"  typedef {cpp_cli_clsname} client_t;\n")
        self.wr(f"  typedef {clscls_super} super_t;\n")
        self.wr("\n")

        # Declare ctor/dtor
        self.wr("\n")
        self.wr("public:\n")
        self.wr(f'  {cpp_wp_clsname}() : super_t("{cls.qifname}")\n')
        self.wr("  {\n")
        self.wr("    funcReg(this);\n")
        self.wr("  }\n")
        self.wr("\n")
        self.wr(f"  virtual ~{cpp_wp_clsname}()\n")
        self.wr("  {\n")
        self.wr(f'    // MB_DPRINTLN("{cpp_wp_clsname} destructed");\n')
        self.wr("  }\n")
        self.wr("\n")

        # Funcmap registration
        self.wr("  // setup function map (called by init())\n")
        self.wr("  static void funcReg(qlib::FuncMap *pmap);\n")
        self.wr("\n")

        # Dispatch invocation decl
        self.wr("\n")
        self.wr("  //\n")
        self.wr("  // Dispatch interfaces\n")
        self.wr("  //\n")
        self.gen_prop_decl()
        self.gen_invoke_decl()

        self.wr("\n")
        self.wr("};\n")

        modifier = ""
        # $cls->{"dllexport"};
        self.wr("\n")
        self.wr(f"{modifier} void {cpp_wp_clsname}_funcReg(qlib::FuncMap *pmap);\n")

    def gen_prop_decl(self):
        cls = self.cls
        # cpp_wp_clsname = cls.get_wp_clsname()
        props = cls.properties
        for name in sorted(props.keys()):
            prop = props[name]
            typenm = prop.prop_type.type_name

            # getter
            fn = make_prop_signature(mk_get_fname(name))
            self.wr(f"  static bool {fn};\n")

            if prop.is_readonly():
                continue

            # setter
            fn = make_prop_signature(mk_set_fname(name))
            self.wr(f"  static bool {fn};\n")

        self.wr("\n")
        return

    def gen_invoke_decl(self):
        cls = self.cls
        # cxx_wp_clsname = cls.get_wp_clsname()
        mths = cls.methods
        for name in sorted(mths.keys()):
            mth = mths[name]
            fn = make_method_signature(mth)
            self.wr(f"  static bool {fn};\n")
        self.wr("\n")
        return