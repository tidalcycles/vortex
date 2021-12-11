# vortex

Algorithmic pattern experiments in Python, inspired by TidalCycles

To install module, first install pyenv (or conda if you prefer)
Once in your virtual environment, do:

`cd py-vortex` <br>
`pip install -r requirements` <br>
`pip install -e .` <br>

To run tests:
`cd test`
`pip install -r requirements`
`cd ..`
`pytest`

To run a single test
`pytest -k "regex"`

pytest will look for any test that match regex in their function name
