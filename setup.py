import os
import re

from setuptools import find_packages, setup

install_requires = []

with open("requirements.txt") as fp:
    install_requires += [
        line for line in fp.readlines() if not re.search("^[-=].*", line)
    ]

dev_requires = ""

with open("requirements-dev.txt") as fp:
    dev_requires += fp.read()

with open("README.md") as f:
    readme = f.read()

here = os.path.abspath(os.path.dirname(__file__))
# Get __version__ variable
exec(open(os.path.join(here, "qifparser", "_version.py")).read())

setup(
    name="Python QIF parser",
    version=__version__,  # NOQA
    description="Python QIF parser.",
    long_description=readme,
    author="Ryuichiro Ishitani",
    author_email='ishitani@users.sourceforge.net',
    url="https://github.com/CueMol/qifparser",
    packages=find_packages(exclude=("tests", "docs")),
    install_requires=install_requires,
    extras_require={"dev": dev_requires},
    entry_points={
        'console_scripts':[
            'qifparser = qifparser.main:main',
        ],
    },

)
