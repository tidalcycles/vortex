# Vortex: Algorithmic pattern experiments in Python

Inspired by [TidalCycles](https://tidalcycles.org) and 
[Tidal Remake](https://github.com/yaxu/remake). Tidalcycles experimental port
for Python 3+.

**This is free software, but currently free as in _free puppies_. It is moving fast and not yet ready for use.
**

## Installation

### Installing the Vortex module

To install module, first install [pyenv](https://github.com/pyenv/pyenv) (or [conda](https://docs.conda.io/en/latest/) if you prefer). Once in your virtual environment, do:

```
cd py-vortex
pip install -r requirements.txt
pip install -e .
```

### Testing the module

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

On MacOS, there are a few packages you need to install manually. Check your installation beforehand because you might already have everything you need. Run these commands only if a component appear to be missing. You can use [brew](https://brew.sh/) to get them:
* `brew install liblo`
* `pip install pyqt5 --upgrade`
* `pip install pyqt5-sip --upgrade`
* `pip install sip --upgrade`

## Usage

* Run `vortex --cli` for an [IPython](https://ipython.org/) based REPL.
* Run `vortex` for the QtScintilla experimental GUI window.
