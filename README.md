# Vortex: Algorithmic pattern experiments in Python
Inspired by TidalCycles


## Installation

### Installing the Vortex module

To install module, first install pyenv (or conda if you prefer). Once in your
virtual environment, do:

```
cd py-vortex
pip install -r requirements.txt
pip install -e .
```

To run tests:
```
cd test
pip install -r test-requirements.txt
cd ..
pytest
```

To run a single test:
`pytest -k "regex"`

`pytest` will look for any test that match regex in their function name.

### Platform specific instructions
#### Linux

On Linux, you might need to install `liblo-dev`:
* `Debian/Ubuntu` (`apt`): `sudo apt install liblo-dev`
* `Arch` and arch-based: `sudo pacman -S liblo` or check the `Aur`.

#### MacOS

On MacOS, there are a few packages you need to install manually. You can use
the [brew](https://brew.sh/) to get them:
* `brew install liblo`
* `pip install pyqt5 --upgrade`
* `pip install pyqt5-sip --upgrade`
* `pip install sip --upgrade`

