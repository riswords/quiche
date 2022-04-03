## Introduction
Quiche is a python implementation of egraphs based on
[egraphs-good (egg)](https://egraphs-good.github.io/).

For usage examples, check out the demo code in demo/demo.py!

Additional documentation coming soon!


## Installation:

Currently, Quiche only works with python 3.7, but additional version support
will be coming soon.

We recommend using venv.
See [the Python documentation](https://docs.python.org/3/library/venv.html)
for venv setup. E.g., in Bash:

    $ python3.7 -m venv .

Activate your virtual environment, e.g. in Bash:

    $ source ./bin/activate

To install (from the top-level `quiche` directory):

    $ pip install .


## Running Tests
To run the tests (from the top-level `quiche` directory):

  1. Install testing dependencies from requirements.txt:

    $ pip install -r requirements.txt

  2. Run tests (from top-level `quiche` directory):

    $ pytest

Questions, issues, or requests? Please file an issue on this repo!
