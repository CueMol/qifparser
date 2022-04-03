def get_var_type_name(typenm):
    if typenm == "boolean":
        return "Bool"
    elif typenm == "integer" or typenm == "enum":
        return "Int"
    elif typenm == "real":
        return "Real"
    elif typenm == "string":
        return "String"
    elif typenm == "array":
        return "Array"
    elif typenm == "list":
        return "List"
    elif typenm == "dict":
        return "Dict"
    elif typenm == "void":
        return "Void"
    else:
        return "Object"


_intr_types = ["boolean", "integer", "real", "string", "enum", "array", "list", "dict"]


def is_intrinsic_type(typenm):
    if typenm in _intr_types:
        return True
    else:
        return False


def format_type(typeobj):
    if typeobj.type_name == "object":
        return f"object<{typeobj.obj_type}>"
    else:
        return typeobj.type_name
