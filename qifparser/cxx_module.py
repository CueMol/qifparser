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

# TODO: config
common_inc = "<common.h>"

class CxxModGen(BaseSrcGen):
    def _gen_preamble(self):
        self.wr("//\n")
        self.wr(f"// Auto-generated by qifparser {__version__}. Don't edit.\n")
        self.wr("//\n")
        self.wr("\n")
        self.wr(f"#include {common_inc}\n")
        self.wr("\n")

    def generate_impl(self, output_path):
        target = self.cls
        qif_name = target.qifname
        cls = get_class_def(qif_name)
        self._gen_preamble()
        