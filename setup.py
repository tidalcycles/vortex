import os

from setuptools import find_packages, setup

_base_dir = os.path.dirname(__file__)

package_name = "vortex"

def get_requirements():
    with open(os.path.join(_base_dir, "requirements.txt")) as fp:
        return fp.read().splitlines()


setup(
    name=package_name,
    version="0.0.1",  # TODO: replace that an automated version generator
    description="Python Tidal port",
    author="Tydal Ciclists",
    author_email="vortex@tidalcycles.org",
    url="http://tidalcycles.org",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["vortex=vortex.console.vortex:run"],
    },
    include_package_data=True,
    package_data={package_name: ["res/*"]},
    install_requires=get_requirements(),
    classifiers=[
        "Programming Language :: Python :: 3.9",
    ],
)
