import pytest
from vortex.mini import grammar


@pytest.mark.parametrize(
    "test_input,expected",
    [
        # words
        ("bd ", []),
        ("bd#32", []),
        ("drum_sound", []),
        # sequences
        ("bd bd", []),
        ("bd bd bd ", []),
        # modifiers
        ("drum_sound/4", []),
        ("sn*4 cp!4 bd@8 hh/3", []),
        ("sn%4", []),  # doesn't work in tidal but works here
        ("sn*(3/5)", []),  # scalar (fraction) argument of '*'
        ("sn:35 sn:2 sn", []),  # scalar (fraction) argument of '*'
        # brackets
        (" [ bd ] ", []),
        ("[bd#32]", []),
        ("[ bd bd bd ]", []),
        ("[bd@3 ]", []),
        # bracket modifiers
        ("[bd#32@3 ]@3", []),
        ("[-1.000!3 ]@3", []),
        ("[-1.000!3 bd@3 ]@3", []),
        # nesting
        ("[[bd#32@3 ]]", []),
        ("[ [bd@3 ]@3 bd ]", []),
        (" [[ bd@3 ]@3] ", []),
        (" [[ 0.3333@3 ]@3] ", []),
        (" [[ bd@3 ]@3 bd!2]!3 ", []),
        # deeper nesting
        (" [ bd bd [bd bd]@3 [bd [bd bd]!3 ] ]", []),
        (" [ bd bd [bd bd] [bd [bd bd] ] ]", []),
        (" [ bd bd [bd bd] [bd [bd bd] ] ]@3", []),
        (" [ bd [bd [bd [bd [bd  [bd]]]]]]", []),
        # angle brackets
        ("< bd cp hh >", []),
        ("< bd cp <bd hh> >", []),
        ("< bd cp <bd hh>!2 >!3", []),
        # curly brackets
        ("{ bd cp bd }", []),
        ("{ bd cp bd }%4", []),
        ("{ bd cp {bd cp sn}%5 }%4", []),
        # bracket mixtures
        ("{ bd <cp sn> <bd [cp sn]> [bd hh <hh sn [hh hh hh]>] }", []),
        # euclidean
        (" bd(3,8) ", []),
        (" cp( 3,8, 2) ", []),
        ("bd(3,4) cp( 3,8, 2) ", []),
        (" cp( 3,8)!2 ", []),
        (" cp( 3,8, 2)!2 ", []),
        (" [bd cp ](3,8) ", []),
        # patterned euclidean
        (
            "bd(3 5 2/3, 5)",
            [],
        ),  # works  but i think 3/2 is a fraction, not a slow-modified element
        (
            "bd(3 5 <2 3>, <5 7 4>)",
            [],
        ),  # works but i don't undertand how we can pattern numbers yet.
        # euclidean bracket mixtures
        (
            "{ bd(3,7) <cp sn(5,8,2)> <bd!3 [cp sn(9,16,5)]> [bd hh(3,5) <hh sn [hh hh(5,8)!3 hh]@2>] }",
            [],
        ),
        # stacks
        ("[bd, bd bd bd]", []),
        ("[bd, bd bd bd, cp cp cp cp]", []),
        ("[bd, [cp cp]!2, [sn sn sn]]", []),
        ("[bd, [bd bd] bd [sn bd hh] hh hh  ]", []),
        # euclidan in stacks
        ("[bd, cp(3,8) ]", []),
        ("[bd,cp(3,8)]", []),
        ("[bd, cp(3,8) sn(5,8) ]", []),
        ("[bd, cp(3,8) sn!3 sn, cp ]", []),
        ("[bd, cp(3,8), cp(5, 19) ]", []),
        ("[bd, cp(3,8), bd(3,2,4), cp(5, 19) ]", []),
        ("[bd, cp(3,8), bd(3 ,<3 8>,4), cp(5, 19) ]", []),
        # nested stacks
        ("[bd, [cp, sn!5]  ]", []),
        ("[bd, cp [cp*2, sn!5]  ]", []),
        pytest.param(
            " [[ (3/8)@3 ]@3] ", [], marks=pytest.mark.xfail
        ),  # fails because number elements aren't handled yet.
        pytest.param(
            "[(-1.000/32)@3 ]@3", [], marks=pytest.mark.xfail
        ),  # fails because number elements aren't handled yet.
    ],
)
def test_parse(benchmark, test_input, expected):
    # FIXME: Assert expected output
    assert benchmark(grammar.parse, test_input)
