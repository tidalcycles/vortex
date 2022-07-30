# Vortex: Algorithmic pattern experiments in Python

Inspired by [TidalCycles](https://tidalcycles.org) and
[Tidal Remake](https://github.com/yaxu/remake). TidalCycles experimental port
for Python 3+.

**This is free software, but currently free as in _free puppies_. It is moving
fast and only really useful for playing with, not serious work.**

## Usage

From a terminal, run `vortex` to fire up a GUI editor. You can evaluate blocks
of code by pressing <kbd>Ctrl</kbd>+<kbd>Enter</kbd> or
<kbd>Command</kbd>+<kbd>Enter</kbd>.

Alternatively, you can start a Vortex REPL by running `vortex --cli`. This REPL
uses [IPython](https://ipython.org/) to evaluate Python code.

## Install

There is no package published on PyPi yet, but you can install everything from
the repository by following the instructions for development below.

## Development

First clone the repository, or download the zip file and unzip it somewhere on
your file system.

### Dependencies

Vortex depends on:

* Python >= 3.8 or < 3.11
* liblo
* qt5

#### Linux

On Linux, you might need to install `liblo-dev`:

* `Debian/Ubuntu` (`apt`): `sudo apt install liblo-dev`
* `Arch` and arch-based: `sudo pacman -S liblo` or check the `Aur`.

#### MacOS

On MacOS, there are a few packages you might need to install manually. Check
your installation beforehand because you might already have everything you need.
Run these commands only if a component appear to be missing. You can use
[brew](https://brew.sh/) to get them:

* `brew install liblo`
* `pip install -U pyqt5 pyqt5-sip sip`

### Poetry

You will need to install [Poetry](https://python-poetry.org/). Please follow
the instructions [here](https://python-poetry.org/docs/master/#installation).

After installing, check that you have Poetry working correctly by running
`poetry -V`. You should see something like this:

```bash
$ poetry -V
Poetry version 1.1.14
```

### Install dependencies and Vortex package

To install everything, run `poetry install`.  This will create a virtual
environment for you and install all dependencies there, allowing you to isolate
Vortex from other Python packages in your system.

```
poetry install
```

This will also install the `vortex` package.

Now refer to the Usage section.  Please note that for running the `vortex` CLI command, you will need to preprend `poetry run`:

For example:

```
poetry run vortex --cli
```

Alternatively, you can active the virtual environment first:

```
poetry shell
vortex --cli
```

### Tests

To run tests, use `pytest`:

```bash
poetry run pytest
```

or:

```bash
poetry shell
pytest
```

To run a single test:

```
pytest -k "regex"
```

`pytest` will look for any test that match regex in their function name.

You can run `ptw` to start watching file for changes and run tests
automatically, useful for developing in a test-driven way.

## Contributing

Bug reports and pull requests are welcome on GitHub at the
[issues page](https://github.com/tidalcycles/vortex/issues). This project is
intended to be a safe, welcoming space for collaboration, and contributors are
expected to adhere to the [Contributor Covenant](http://contributor-covenant.org)
code of conduct.

<a href="https://github.com/tidalcycles/vortex/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=tidalcycles/vortex" />
</a>

Made with [contrib.rocks](https://contrib.rocks).

## License

This project is licensed under the GNU Public License version 3. Refer to
[LICENSE](https://github.com/tidalcycles/vortex/blob/main/LICENSE).
