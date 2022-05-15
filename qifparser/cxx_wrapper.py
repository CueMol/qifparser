import logging
from qifparser.parser import get_class_def
from qifparser._version import __version__
from qifparser.utils import get_var_type_name, is_intrinsic_type, format_type
from qifparser.class_def import MethodDef, TypeObj
from qifparser.base_srcgen import BaseSrcGen

logger = logging.getLogger(__name__)

# TODO: config
common_inc = "<common.h>"


def qif_to_cli_clsname(qifname):
    cls_obj = get_class_def(qifname)
    return cls_obj.cxx_name


class CxxWrapGen(BaseSrcGen):
    def _gen_invoke_code(self):
        cls = self.cls

        cxx_wp_clsname = cls.get_wp_clsname()
        mths = cls.methods
        for nm in sorted(mths.keys()):
            mth = mths[nm]
            self.wr("\n")
            self.wr(f"// method invocation impl for {nm}\n")
            self.wr("\n")
            self.wr("// static\n")
            self.wr(f"bool {cxx_wp_clsname}::{make_method_signature(mth)}\n")
            self.wr("{\n")
            self._gen_lvar_to_cxx_conv(mth)
            self._gen_invoke_body(mth)
            self.wr("  return true;\n")
            self.wr("}\n")

        return

    #
    # generate registration code
    #
    def _gen_regfunc_code(self):
        cls = self.cls

        cpp_wp_clsname = cls.get_wp_clsname()

        self.wr("\n")
        self.wr("// static\n")
        self.wr(f"void {cpp_wp_clsname}::funcReg(qlib::FuncMap *pmap)\n")
        self.wr("{\n")

        # Class name tag
        class_key = f"@implement_{cls.qifname}"
        self.wr(f'  pmap->putPropAttr("{class_key}", "yes");\n')
        self.wr("\n")

        # Properties
        props = cls.properties
        for propnm in sorted(props.keys()):
            prop = props[propnm]
            rprop_opts = prop.modifiers
            getter_name = mk_get_fname(propnm)
            setter_name = mk_set_fname(propnm)
            proptype = format_type(prop.prop_type)

            self.wr(f'  if (! pmap->hasProp("{propnm}") ) {{\n')

            # attribute (typename)
            self.wr(f'    pmap->putPropAttr("{propnm}", "{proptype}");\n')

            # attribute (nopersist)
            if "nopersist" in rprop_opts:
                self.wr(f'    pmap->putPropAttr("@{propnm}_nopersist", "yes");\n')

            # getter
            self.wr(
                f'    pmap->putFunc("{getter_name}", &{cpp_wp_clsname}::{getter_name});\n'
            )

            if "readonly" not in rprop_opts:
                # setter
                self.wr(
                    f'    pmap->putFunc("{setter_name}", &{cpp_wp_clsname}::{setter_name});\n'
                )

            self.wr("  }\n")

        # Methods
        mths = cls.methods
        for nm in sorted(mths.keys()):
            mth_name = _mk_mth_fname(nm)
            self.wr(f'  pmap->putFunc("{mth_name}", &{cpp_wp_clsname}::{mth_name});\n')

        enum_keys = sorted(cls.enumdefs.keys())
        for nm in enum_keys:
            enumdef = cls.enumdefs[nm]
            self.wr(f"  // Enum def for {nm}\n")
            # Check enum alias
            enum_alias = enumdef.enum_alias
            if enum_alias is not None:
                if enum_alias not in cls.enumdefs:
                    raise RuntimeError(f"enum alias {enum_alias} not defined")
                enumdef = cls.enumdefs[enumdef.enum_alias]
            enums = sorted(enumdef.enum_data.keys())
            for defnm in enums:
                cxx_def = enumdef.enum_data[defnm]
                self.wr(f'  pmap->putEnumDef("{nm}", "{defnm}", {cxx_def});\n')
        self.wr("\n")

        # Generate code for importing super classes
        extends = cls.extends_wrapper
        for i in extends:
            self.wr(f"  ::{i}_funcReg(pmap);\n")
        self.wr("\n")

        # Default value
        for propnm in sorted(props.keys()):
            prop = props[propnm]
            rprop_opts = prop.modifiers
            if prop.default_cxx_rval is not None and not prop.is_readonly():
                vrnt_mth = _make_var_getter_method(prop.prop_type)
                cxxdefault = prop.default_cxx_rval
                self.wr("  {\n")
                self.wr("    qlib::LVariant defval;\n")
                # self.wr("    defval.set${mthnm}($cxxdefault);\n")
                self.wr(f'    setBy{vrnt_mth}( defval, {cxxdefault}, "{propnm}" );\n')
                self.wr(f'    pmap->putDefVal("{propnm}", defval);\n')
                self.wr("  }\n")

        self.wr("}\n")
        self.wr("\n")

        # Register function def
        self.wr("\n")
        self.wr(f"void {cpp_wp_clsname}_funcReg(qlib::FuncMap *pmap)\n")
        self.wr("{\n")
        self.wr(f"    {cpp_wp_clsname}::funcReg(pmap);\n")
        self.wr("}\n")

        return

    def _gen_property_code(self):
        cls = self.cls

        cpp_wp_clsname = cls.get_wp_clsname()
        props = cls.properties
        for propnm in sorted(props.keys()):
            prop = props[propnm]
            typenm = prop.prop_type.type_name
            if prop.redirect:
                cppnm = prop.cxx_getter_name + "/" + prop.cxx_setter_name
            else:
                cppnm = prop.cxx_field_name
            # tid = get_var_type_name(typenm)
            getter_name = mk_get_fname(propnm)
            setter_name = mk_set_fname(propnm)

            self.wr("\n")
            self.wr(f"// property handling impl for {propnm} ({typenm} {cppnm})\n")
            self.wr("\n")

            # Getter
            self.wr("// static\n")
            self.wr(f"bool {cpp_wp_clsname}::{make_prop_signature(getter_name)}\n")
            self.wr("{\n")

            mth = _make_getter_mth(prop, "*")
            self._gen_lvar_to_cxx_conv(mth)
            self._gen_get_set_impl(prop, "get")

            self.wr("  return true;\n")
            self.wr("}\n")

            # Setter
            # next if (contains($prop->{"options"}, "readonly"));
            if prop.is_readonly():
                continue
            self.wr("// static\n")
            self.wr(f"bool {cpp_wp_clsname}::{make_prop_signature(setter_name)}\n")
            self.wr("{\n")

            # $mth = makeFakeSetterMth($prop, "dset_$propnm");
            mth = _make_setter_mth(prop, f"dset_{propnm}")
            # genLVarToCxxConv($cls, $mth);
            self._gen_lvar_to_cxx_conv(mth)
            # genGetSetImpl($cls, $prop, "set");
            self._gen_get_set_impl(prop, "set")

            self.wr("  return true;\n")
            self.wr("}\n")

        return

    # generate code for converting LVarArgs to C++ arguments
    def _gen_lvar_to_cxx_conv(self, mth):
        cls = self.cls

        args = mth.args
        nargs = len(args)
        argsnm = "vargs"

        self.wr(f"  {argsnm}.checkArgSize({nargs});\n")
        self.wr("  \n")
        self.wr(f"  client_t* pthis = {argsnm}.getThisPtr<client_t>();\n")
        self.wr("  \n")

        ind = 0
        for arg in args:
            cxxtype = _gen_conv_to_cxx_type(arg)
            vrnt_mth = _make_var_getter_method(arg)

            if arg.type_name == "enum":
                cpp_wp_clsname = cls.get_wp_clsname()
                vrnt_mth = f"{vrnt_mth}<{cpp_wp_clsname}>"

            self.wr(f"  {cxxtype} arg{ind};\n")
            self.wr(
                f'  convTo{vrnt_mth}(arg{ind}, {argsnm}.get({ind}), "{arg.name}");\n'
            )

            ind += 1

        return

    # generate common invocation body code
    def _gen_invoke_body(self, mth):
        cls = self.cls
        thisnm = "pthis"
        cxxnm = mth.get_cxx_name()
        rettype = mth.return_type
        tmp = []
        for i in range(len(mth.args)):
            tmp.append(f"arg{i}")
        strargs = ", ".join(tmp)

        rval_typename = rettype.type_name

        if rval_typename == "void":
            self.wr("\n")
            self.wr(f"  {thisnm}->{cxxnm}({strargs});\n")
            self.wr("\n")
            self.wr("  vargs.setRetVoid();\n")
        else:
            vrnt_mth = _make_var_getter_method(rettype)
            if rettype.type_name == "enum":
                cpp_wp_clsname = cls.get_wp_clsname()
                vrnt_mth = f"{vrnt_mth}<{cpp_wp_clsname}>"

            # Right-hand side (return value) processing
            rhs = f"{thisnm}->{cxxnm}({strargs})"

            self.wr("  LVariant &rval = vargs.retval();\n")
            self.wr("\n")
            self.wr(f'  setBy{vrnt_mth}( rval, {rhs}, "{rettype.name}" );\n')
            self.wr("\n")
        return

    #
    # Generate getter/setter implementation code
    #
    def _gen_get_set_impl(self, prop, flag):
        cls = self.cls
        thisnm = "pthis"
        mth = None

        # # Redirection (1) <-- not used in current impl
        # if contains(prop.modifiers, "redirect"):
        #     if flag == "get":
        #         mth = _make_getter_mth(prop, f"get_{prop.cppname}")
        #     elif flag == "set":
        #         mth = _make_setter_mth(prop, f"set_{prop.cppname}")
        #     _gen_invoke_body(f, cls, mth)
        #     return

        # Redirection
        if prop.redirect:
            getnm = prop.cxx_getter_name
            setnm = prop.cxx_setter_name
            if flag == "get":
                mth = _make_getter_mth(prop, getnm)
            elif flag == "set":
                mth = _make_setter_mth(prop, setnm)
            self._gen_invoke_body(mth)
            return

        # Direct access
        cxxnm = prop.cxx_field_name
        prop_type = prop.prop_type

        vrnt_mth = _make_var_getter_method(prop_type)
        if prop_type.type_name == "enum":
            cpp_wp_clsname = cls.get_wp_clsname()
            vrnt_mth = f"{vrnt_mth}<{cpp_wp_clsname}>"

        if flag == "get":
            # Right-hand side
            rhs = f"{thisnm}->{cxxnm}"
            prop_name = prop.prop_name

            self.wr("\n")
            self.wr("  LVariant &rval = vargs.retval();\n")
            self.wr("\n")
            # self.wr("  rval.set${vrnt_mth}( ${thisnm}->${cxxnm} );\n")
            self.wr(f'  setBy{vrnt_mth}( rval, {rhs}, "{prop_name}" );\n')
            self.wr("\n")
        elif flag == "set":
            self.wr("\n")
            self.wr(f"  {thisnm}->{cxxnm} = arg0;\n")
            self.wr("\n")

        return

    def _gen_preamble(self):
        self.wr("//\n")
        self.wr(f"// Auto-generated by qifparser {__version__}. Don't edit.\n")
        self.wr("//\n")
        self.wr("\n")
        self.wr(f"#include {common_inc}\n")
        self.wr("\n")

    def _gen_class_loader(self):
        cls = self.cls
        cpp_wp_clsname = cls.get_wp_clsname()
        cxx_cli_clsname = cls.cxx_name

        self.wr("\n")
        self.wr(f"SINGLETON_BASE_IMPL({cpp_wp_clsname});\n")
        self.wr("\n")

        if cls.is_cloneable():
            self.wr(f"MC_CLONEABLE_IMPL({cxx_cli_clsname});\n")
            self.wr("\n")

        self.wr(f"MC_DYNCLASS_IMPL2({cxx_cli_clsname}, {cpp_wp_clsname});\n")
        self.wr(f"MC_PROP_IMPL2({cxx_cli_clsname}, {cpp_wp_clsname});\n")
        self.wr(f"MC_INVOKE_IMPL2({cxx_cli_clsname}, {cpp_wp_clsname});\n")
        self.wr("\n")

    def generate_impl(self, output_path):
        target = self.cls
        qif_name = target.qifname
        cls = get_class_def(qif_name)
        cxx_cli_clsname = cls.cxx_name
        cpp_wp_clsname = cls.get_wp_clsname()
        logger.info(f"generating C++ wrapper ({cxx_cli_clsname}) src for {qif_name}")

        if cls.is_smart_ptr():
            cxx_cli_clsname = f"qlib::LScrSp<{cxx_cli_clsname}>"

        self._gen_preamble()

        self.wr(f'#include "{cls.get_wp_hdr_fname()}"\n')

        self.wr("\n")
        self.wr("#include <qlib/ClassRegistry.hpp>\n")
        self.wr("#include <qlib/LVariant.hpp>\n")
        # self.wr("#include <qlib/LPropEvent.hpp>\n")
        self.wr("\n")

        # TODO: impl?? (not used in current qif)
        # foreach my $f (@Parser::user_cxx_incfiles) {
        #   print $fhout "\#include $f\n";
        # }

        if len(target.refers) > 0:
            for ref in target.refers:
                ref_cls = get_class_def(ref)
                if ref_cls is None:
                    raise RuntimeError(f"class def not found: {ref}")
                self.wr(f'#include "{ref_cls.get_wp_hdr_fname()}"\n')
            self.wr("\n")

        self.wr("\n")
        self.wr("using qlib::LString;\n")
        self.wr("using qlib::LVariant;\n")
        self.wr("using qlib::LVarArgs;\n")
        self.wr("using qlib::LClass;\n")
        self.wr("using qlib::ClassRegistry;\n")
        self.wr("\n")
        self.wr(f"// XXX {cpp_wp_clsname}\n")

        self.wr("/////////////////////////////////////\n")
        self.wr(f"// Class loader code for the client class {cxx_cli_clsname}\n")
        self._gen_class_loader()
        self.wr("\n")

        self.wr("/////////////////////////////////////\n")
        self.wr("//\n")
        self.wr(f"// Wrapper class for {cxx_cli_clsname}\n")
        self.wr("//\n")
        self.wr("\n")

        self.wr("/////////////////////////////////////\n")
        self.wr("// Dispatch interface code\n")
        self.wr("\n")
        self.wr("//\n")
        self.wr("// Property getter/setter wrappers\n")
        self.wr("//\n")
        self._gen_property_code()

        self.wr("\n")
        self.wr("//\n")
        self.wr("// Method invocation wrappers\n")
        self.wr("//\n")
        self._gen_invoke_code()

        self.wr("\n")
        self.wr("//\n")
        self.wr("// Function table registration code\n")
        self.wr("//\n")
        self._gen_regfunc_code()

        return


def mk_get_fname(nm):
    return f"get_{nm}"


def mk_set_fname(nm):
    return f"set_{nm}"


def _mk_mth_fname(nm):
    return f"mth_{nm}"


def make_prop_signature(func_name):
    return f"{func_name}(qlib::LVarArgs &vargs)"


def make_method_signature(mth):
    return f"{_mk_mth_fname(mth.method_name)}(qlib::LVarArgs &vargs)"


def _make_getter_mth(prop, cxxname):
    mth = MethodDef(
        method_name=prop.prop_name,
        return_type=prop.prop_type,
        args=[],
        redirect=False,
        cxx_name=cxxname,
    )
    return mth


def _make_setter_mth(prop, cxxname):
    void_type = TypeObj(type_name="void")
    mth = MethodDef(
        method_name=prop.prop_name,
        return_type=void_type,
        args=[prop.prop_type],
        redirect=False,
        cxx_name=cxxname,
    )
    return mth


# convert type structure to C++ type name
def _gen_conv_to_cxx_type(type_obj):
    typename = type_obj.type_name
    if is_intrinsic_type(typename):
        vtn = get_var_type_name(typename)
        return f"qlib::L{vtn}"

    elif typename == "object":
        cxxname = qif_to_cli_clsname(type_obj.obj_type)
        if type_obj.ref:
            # To SmartPtr
            return f"qlib::LScrSp< {cxxname} >"
        else:
            # # To value (const reference)
            # return "const $cxxname &";

            # To value
            return f"{cxxname} "
    else:
        raise RuntimeError(f"unknown type: {type_obj}")


# make variant's C++ getter method name from type structure
def _make_var_getter_method(type_obj):
    typename = type_obj.type_name
    if typename == "enum":
        return "EnumInt"
    elif is_intrinsic_type(typename):
        # this just capitalize the typename
        vtn = get_var_type_name(typename)
        return f"{vtn}Value"
    elif typename == "object":
        cxxname = qif_to_cli_clsname(type_obj.obj_type)
        if type_obj.ref:
            # To SmartPtr
            return f"SPtrValueT< {cxxname} >"
        else:
            # To value (const reference)
            return f"ObjectRefT< {cxxname} >"
    else:
        raise RuntimeError(f"unknown type: {type_obj}")
