# Vortex: Algorithmic pattern experiments in Python
Inspired by TidalCycles


## Installation

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
