import os
from setuptools import setup, find_packages


_base_dir = os.path.dirname(__file__)

package_name = "py-tidal-num".replace("_", "-").lower()

def get_requirements():
    with open(os.path.join(_base_dir, "requirements.txt")) as fp:
        return fp.read().splitlines()

setup(
    name = package_name,
    version = "0.0.1",
    description = "Python Tidal port with NumPy",
    author = "Tydal Ciclysts",
    author_email = "artheist@lgmail.com",
    url = "http://tidalcycles.org",
    packages = find_packages(),
    include_package_data = True,
    install_requires = get_requirements(),
    classifiers = [
        "Programming Language :: Python :: 3.9",
    ],
)
