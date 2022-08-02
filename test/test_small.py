import pytest

from vortex.mini.small import small
from vortex.pattern import Pattern, degrade, fast, fastcat, pure, silence, slow, timecat


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
        # rest
        ("~", silence()),
        # modifiers
        ("bd*2", fast(2, "bd")),
        ("bd/3", slow(3, "bd")),
        ("hh!", fastcat("hh", "hh")),
        ("hh!!", fastcat("hh", "hh", "hh")),
        ("hh?", degrade("hh")),
        ("hh??", degrade(degrade("hh"))),
        (
            "hh!??!",
            fastcat(
                degrade(degrade(fastcat("hh", "hh"))),
                degrade(degrade(fastcat("hh", "hh"))),
            ),
        ),
        pytest.param("hh@2", timecat((2, "hh")), marks=pytest.mark.xfail),
    ],
)
def test_eval(test_input, expected):
    pat = small(test_input)
    assert isinstance(pat, Pattern)
    assert pat.first_cycle() == expected.first_cycle()
