## Introduction
Quiche is a python implementation of egraphs based on
[egraphs-good (egg)](https://egraphs-good.github.io/).

For usage examples, check out the demo code in `demo/egraphs_demo.py`,
as well as the `tests` directory: `test_asts.py`, `test_expr.py`, and
`test_prop.py`!

Additional documentation coming soon!

Until then, my slides from the 2022 PLDI EGRAPHS workshop are available in this repo
([EGRAPHS22.pdf](https://github.com/riswords/quiche/blob/main/EGRAPHS22.pdf)), and
the recording of that talk is available on YouTube
[here](https://www.youtube.com/watch?v=dbgZJyw3hnk&t=8690s) (along with the other
amazing talks from the EGRAPHS '22 workshop).

For a more guided walkthrough of e-graphs and code in Quiche, the slides from my intro to
e-graphs talk at the Women in Compilers and Tools meetup are available
[here](https://github.com/riswords/quiche/blob/main/WiCTSlides.pptx). The demo code for those
slides is in `demo/arithmetic_demo.py`.


## Installation:

Currently, Quiche works with python 3.7-3.10.

We recommend using venv.
See [the Python documentation](https://docs.python.org/3/library/venv.html)
for venv setup. E.g., in Bash, you can do the following to set up a python 3.7
virtual environment:

    $ python3.7 -m venv .

Activate your virtual environment, e.g. in Bash:

    $ source ./bin/activate

And when you're finished you can deactivate it as well:

    $ deactivate


To install Quiche, clone this repo and use pip (from the top-level `quiche` directory):

    $ pip install .

If you want to generate SVG images of `QuicheTree`s or `EGraphs` you should
also install `graphviz`:

    $ pip install graphviz


## Running Tests
To run the tests (from the top-level `quiche` directory):

  1. Install testing dependencies from requirements.txt:

    $ pip install -r requirements.txt

  2. Run tests (from top-level `quiche` directory):

    $ pytest


## More Information

Questions, issues, or requests? Please file an issue on this repo!

Want to chat about Quiche? Join the Slack channel!

https://join.slack.com/t/quiche-group/shared_invite/zt-1ow1puw1t-gar3wVzBJl60olXC~AjLTA

If you're interested in e-graphs more generally, check out the e-graphs Zulip!

https://egraphs.zulipchat.com/
