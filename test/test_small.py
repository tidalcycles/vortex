from vortex.mini.small import small
from vortex.pattern import pure
import pytest


@pytest.mark.parametrize(
    "test_input,expected",
    [
        # numbers
        ("45", pure(45)),
        ("-2.", pure(-2.0)),
        ("4.64", pure(4.64)),
        ("-3", pure(-3)),
        # words
        ("foo", pure("foo")),
        ("Bar", pure("Bar")),
        # modifiers
        ("bd*2", pure("bd").fast(2)),
        ("bd/3", pure("bd").slow(3)),
        # ("hh!", pure("hh")),
        # ("hh?", )
    ],
)
def test_eval(test_input, expected):
    assert small(test_input).first_cycle() == expected.first_cycle()
