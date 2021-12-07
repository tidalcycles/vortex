import re
import os
import codecs
from setuptools import setup, find_packages


_base_dir = os.path.dirname(__file__)

package_name = "py-vortex".replace("_", "-").lower()

def get_requirements():
    with open(os.path.join(_base_dir, "requirements.txt")) as fp:
        return fp.read().splitlines()

setup(
    name = package_name,
    version = "0.0.1", # TODO: replace that an automated version generator
    description = "Python Tidal port",
    author = "Tydal Ciclists",
    author_email = "vortex@tidalcycles.org",
    url = "http://tidalcycles.org",
    packages = find_packages(),
    include_package_data = True,
    install_requires = get_requirements(),
    classifiers = [
        "Programming Language :: Python :: 3.9",
    ],
)
