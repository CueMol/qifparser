import logging

logger = logging.getLogger(__name__)


class BaseSrcGen:
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
                self.generate_impl(output_path)
            except Exception:
                if output_path.is_file():
                    output_path.unlink()
                raise
            finally:
                self.f = None
                self.output_path = None
        logger.info(f"Wrote file: {output_path}")

    def generate_impl(self):
        raise NotImplementedError()

    def wr(self, s):
        self.f.write(s)
