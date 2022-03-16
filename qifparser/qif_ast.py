class ClassDef:
    def __init__(self, name, file_name, supcls_name=None):
        self.qif_name = name
        self.file_name = file_name
        self.options = []
        self.methods = {}
        self.properties = {}
        if supcls_name is None:
            self.extends = []
        else:
            self.extends = [supcls_name]

class MethodDef:
    def __init__(self, name, cxx_name, return_type):
        self.name = name
        self.cxx_name = cxx_name
        self.return_type = return_type
        self.args = []
        

class PropDef:
    def __init__(self, name, cxx_name, prop_type):
        self.name = name
        self.cxx_name = cxx_name
        self.prop_type = prop_type


