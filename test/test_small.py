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
        ("hh?", degrade("hh")),
        ("hh??", degrade(degrade("hh"))),
        (
            "hh!??!",
            fastcat(
                degrade(degrade(fastcat("hh", "hh"))),
                degrade(degrade(fastcat("hh", "hh"))),
            ),
        ),
        # sequences
        ("bd sd", fastcat("bd", "sd")),
        ("bd hh sd", fastcat("bd", "hh", "sd")),
        ("hh@2", pure("hh")),
        ("bd hh@2", timecat((1, "bd"), (2, "hh"))),
        ("bd hh@3 sd@2", timecat((1, "bd"), (3, "hh"), (2, "sd"))),
        ("hh!", fastcat("hh", "hh")),
        ("hh!!", fastcat("hh", "hh", "hh")),
        pytest.param(
            "bd! hh? ~ sd/2 cp*3",
            fastcat(
                "bd",
                "bd",
                degrade("hh"),
                silence(),
                slow(2, "sd"),
                fast(3, "cp"),
            ),
            marks=pytest.mark.xfail,  # fails because the repeat (!) operator is not working correctly
        ),
    ],
)
def test_eval(test_input, expected):
    pat = small(test_input)
    assert isinstance(pat, Pattern)
    assert pat.first_cycle() == expected.first_cycle()
