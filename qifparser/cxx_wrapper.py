import logging
from qifparser.parser import get_class_def
from qifparser._version import __version__
from qifparser.utils import get_var_type_name, is_intrinsic_type
from qifparser.class_def import MethodDef, TypeObj

logger = logging.getLogger(__name__)

# TODO: config
common_inc = "<common.h>"


def qif_to_cli_clsname(qifname):
    cls_obj = get_class_def(qifname)
    return cls_obj.cxx_name


class CxxWrapGen:
    def __init__(self, class_def):
        self.cls = class_def
        self.f = None
        self.output_path = None

    def generate(self, output_path):
        output_path.parent.mkdir(exist_ok=True, parents=True)
        with output_path.open("w") as f:
            self.f = f
            self.output_path = output_path
            try:
                self._gen_cxx_src_impl(output_path)
            except Exception:
                if output_path.is_file():
                    output_path.unlink()
                raise
            finally:
                self.f = None
                self.output_path = None
        logger.info(f"Wrote file: {output_path}")

    def _gen_invoke_code(self):
        return

    def _gen_regfunc_code(self):
        return

    def _gen_property_code(self):
        f = self.f
        cls = self.cls

        cxx_wp_clsname = cls.get_wp_clsname()
        props = cls.properties
        if len(props) == 0:
            return
        for propnm, prop in props.items():
            typenm = prop.prop_type.type_name
            # is_ptr = prop.prop_type.ref
            # qiftype = prop.prop_type.obj_type
            if prop.redirect:
                cppnm = prop.cxx_getter_name + "/" + prop.cxx_setter_name
            else:
                cppnm = prop.cxx_field_name
            tid = get_var_type_name(typenm)
            getter_name = _mk_get_fname(propnm)
            setter_name = _mk_set_fname(propnm)

            f.write("\n")
            f.write(f"// property handling impl for {propnm} ({typenm} {cppnm})\n")
            f.write("\n")

            # Getter
            f.write("// static\n")
            f.write(f"bool {cxx_wp_clsname}::{_make_prop_signature(getter_name)}\n")
            f.write("{\n")

            mth = _make_getter_mth(prop, "*")
            self._gen_lvar_to_cxx_conv(mth)
            self._gen_get_set_impl(prop, "get")

            f.write("  return true;\n")
            f.write("}\n")

            # Setter
            # next if (contains($prop->{"options"}, "readonly"));
            if prop.is_readonly():
                continue
            f.write("// static\n")
            f.write(f"bool {cxx_wp_clsname}::{_make_prop_signature(setter_name)}\n")
            f.write("{\n")

            # $mth = makeFakeSetterMth($prop, "dset_$propnm");
            mth = _make_setter_mth(prop, f"dset_{propnm}")
            # genLVarToCxxConv($cls, $mth);
            self._gen_lvar_to_cxx_conv(mth)
            # genGetSetImpl($cls, $prop, "set");
            self._gen_get_set_impl(prop, "set")

            f.write("  return true;\n")
            f.write("}\n")

        return

    # generate code for converting LVarArgs to C++ arguments
    def _gen_lvar_to_cxx_conv(self, mth):
        f = self.f
        cls = self.cls

        args = mth.args
        nargs = len(args)
        argsnm = "vargs"

        f.write(f"  {argsnm}.checkArgSize({nargs});\n")
        f.write("  \n")
        f.write(f"  client_t* pthis = {argsnm}.getThisPtr<client_t>();\n")
        f.write("  \n")

        ind = 0
        for arg in args:
            cxxtype = _gen_conv_to_cxx_type(arg)
            vrnt_mth = _make_var_getter_method(arg)

            if arg.type_name == "enum":
                cxx_wp_clsname = cls.get_wp_clsname()
                vrnt_mth = f"{vrnt_mth}<{cxx_wp_clsname}>"

            f.write(f"  {cxxtype} arg{ind}\n")
            f.write(
                f'  convTo{vrnt_mth}(arg{ind}, {argsnm}.get({ind}), "{arg.name}");\n'
            )

            ind += 1

        return

    # generate common invocation body code
    def _gen_invoke_body(self, mth):
        f = self.f
        cls = self.cls
        thisnm = "pthis"
        cxxnm = mth.cxx_name
        rettype = mth.return_type
        tmp = []
        for i in range(len(mth.args)):
            tmp.append(f"arg{i}")
        strargs = ",".join(tmp)

        rval_typename = rettype.type_name

        if rval_typename == "void":
            f.write("\n")
            f.write(f"  {thisnm}->{cxxnm}({strargs});\n")
            f.write("\n")
            f.write("  vargs.setRetVoid();\n")
        else:
            vrnt_mth = _make_var_getter_method(rettype)
            type_name = rettype.type_name
            if type_name == "enum":
                cxx_wp_clsname = cls.get_wp_clsname()
                vrnt_mth = f"{vrnt_mth}<{cxx_wp_clsname}>"

            # Right-hand side
            rhs = f"{thisnm}->{cxxnm}({strargs})"

            f.write("  LVariant &rval = vargs.retval();\n")
            f.write("\n")
            # f.write("  rval.set${vrnt_mth}( ${thisnm}->${cxxnm}($strargs) );\n")
            f.write(f'  setBy{vrnt_mth}( rval, {rhs}, "{type_name}" );\n')
            f.write("\n")
        return

    #
    # Generate getter/setter implementation code
    #
    def _gen_get_set_impl(self, prop, flag):
        f = self.f
        cls = self.cls
        thisnm = "pthis"
        mth = None

        # # Redirection (1) <-- not used in current impl
        # if contains(prop.options, "redirect"):
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
            cxx_wp_clsname = cls.get_wp_clsname()
            vrnt_mth = f"{vrnt_mth}<{cxx_wp_clsname}>"

        if flag == "get":
            # Right-hand side
            rhs = f"{thisnm}->{cxxnm}"
            prop_name = prop.prop_name

            f.write("\n")
            f.write("  LVariant &rval = vargs.retval();\n")
            f.write("\n")
            # f.write("  rval.set${vrnt_mth}( ${thisnm}->${cxxnm} );\n")
            f.write(f'  setBy{vrnt_mth}( rval, {rhs}, "{prop_name}");\n')
            f.write("\n")
        elif flag == "set":
            f.write("\n")
            f.write(f"  {thisnm}->{cxxnm} = arg0;\n")
            f.write("\n")

        return

    def _gen_src_preamble(self):
        f = self.f
        cls = self.cls
        f.write("//\n")
        f.write(f"// Auto-generated by qifparser {__version__}. Don't edit.\n")
        f.write("//\n")
        f.write("\n")
        f.write(f"#include {common_inc}\n")
        f.write("\n")

    def _gen_src_class_loader(self):
        f = self.f
        cls = self.cls
        cxx_wp_clsname = cls.get_wp_clsname()
        cxx_cli_clsname = cls.cxx_name

        f.write("\n")
        f.write(f"SINGLETON_BASE_IMPL({cxx_wp_clsname});\n")
        f.write("\n")

        if cls.is_cloneable():
            f.write("MC_CLONEABLE_IMPL({cxx_cli_clsname});\n")
            f.write("\n")

        f.write(f"MC_DYNCLASS_IMPL2({cxx_cli_clsname}, {cxx_wp_clsname});\n")
        f.write(f"MC_PROP_IMPL2({cxx_cli_clsname}, {cxx_wp_clsname});\n")
        f.write(f"MC_INVOKE_IMPL2({cxx_cli_clsname}, {cxx_wp_clsname});\n")
        f.write("\n")

    def _gen_cxx_src_impl(self, output_path):
        f = self.f
        target = self.cls
        qif_name = target.qifname
        cls = get_class_def(qif_name)
        cxx_cli_clsname = cls.cxx_name
        cxx_wp_clsname = cls.get_wp_clsname()
        print(f"generating C++ wrapper ({cxx_cli_clsname}) src for {qif_name}")

        if cls.is_smart_ptr():
            cxx_cli_clsname = f"qlib::LScrSp<{cxx_cli_clsname}>"

        self._gen_src_preamble()

        f.write(f'#include "{cls.get_cxx_wp_incname()}"\n')

        f.write("\n")
        f.write("#include <qlib/ClassRegistry.hpp>\n")
        f.write("#include <qlib/LVariant.hpp>\n")
        # f.write("#include <qlib/LPropEvent.hpp>\n")
        f.write("\n")

        # TODO: impl?? (not used in current qif)
        # foreach my $f (@Parser::user_cxx_incfiles) {
        #   print $fhout "\#include $f\n";
        # }

        if len(target.refers) > 0:
            for ref in target.refers:
                ref_cls = get_class_def(ref)
                if ref_cls is None:
                    raise RuntimeError(f"class def not found: {ref}")
                f.write(f'#include "{ref_cls.get_cxx_wp_incname()}"\n')
            f.write("\n")

        f.write("\n")
        f.write("using qlib::LString;\n")
        f.write("using qlib::LVariant;\n")
        f.write("using qlib::LVarArgs;\n")
        f.write("using qlib::LClass;\n")
        f.write("using qlib::ClassRegistry;\n")
        f.write("\n")
        f.write(f"// XXX {cxx_wp_clsname}\n")

        f.write("/////////////////////////////////////\n")
        f.write(f"// Class loader code for the client class {cxx_cli_clsname}\n")
        self._gen_src_class_loader()
        f.write("\n")

        f.write("/////////////////////////////////////\n")
        f.write("//\n")
        f.write(f"// Wrapper class for {cxx_cli_clsname}\n")
        f.write("//\n")
        f.write("\n")

        f.write("/////////////////////////////////////\n")
        f.write("// Dispatch interface code\n")
        f.write("\n")
        f.write("//\n")
        f.write("// Property getter/setter wrappers\n")
        f.write("//\n")
        self._gen_property_code()

        f.write("\n")
        f.write("//\n")
        f.write("// Method invocation wrappers\n")
        f.write("//\n")
        self._gen_invoke_code()

        f.write("\n")
        f.write("//\n")
        f.write("// Function table registration code\n")
        f.write("//\n")
        self._gen_regfunc_code()


def _mk_get_fname(nm):
    return f"get_{nm}"


def _mk_set_fname(nm):
    return f"set_{nm}"


def _mk_mth_fname(nm):
    return f"mth_{nm}"


def _make_prop_signature(func_name):
    return f"{func_name}(qlib::LVarArgs &vargs)"


def _make_method_signature(mth):
    return f"{_mk_mth_fname(mth.name)}(qlib::LVarArgs &vargs)"


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
