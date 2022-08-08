import pytest

from vortex.mini import mini
from vortex.pattern import (
    Pattern,
    TimeSpan,
    cat,
    choose_cycles,
    degrade,
    fast,
    polyrhythm,
    pure,
    silence,
    slow,
    slowcat,
    stack,
    timecat,
)


@pytest.mark.parametrize(
    "input_code,query_span,expected_pat",
    [
        # numbers
        ("45", None, pure(45)),
        ("-2.", None, pure(-2.0)),
        ("4.64", None, pure(4.64)),
        ("-3", None, pure(-3)),
        # words
        ("foo", None, pure("foo")),
        ("Bar", None, pure("Bar")),
        # rest
        ("~", None, silence()),
        # modifiers
        ("bd*2", None, fast(2, "bd")),
        ("bd/3", None, slow(3, "bd")),
        ("hh?", None, degrade("hh")),
        ("hh??", None, degrade(degrade("hh"))),
        (
            "hh!!??",
            None,
            degrade(degrade(cat("hh", "hh", "hh"))),
        ),
        # sequences
        ("bd sd", None, cat("bd", "sd")),
        ("bd hh sd", None, cat("bd", "hh", "sd")),
        ("hh@2", None, pure("hh")),
        ("bd hh@2", None, timecat((1, "bd"), (2, "hh"))),
        ("bd hh@3 sd@2", None, timecat((1, "bd"), (3, "hh"), (2, "sd"))),
        ("hh!", None, cat("hh", "hh")),
        ("hh!!", None, cat("hh", "hh", "hh")),
        ("bd! cp", None, cat("bd", "bd", "cp")),
        (
            "bd! hh? ~ sd/2 cp*3",
            None,
            timecat(
                (1, "bd"),
                (1, "bd"),
                (1, degrade("hh")),
                (1, silence()),
                (1, slow(2, "sd")),
                (1, fast(3, "cp")),
            ),
        ),
        ("bd | sd", TimeSpan(0, 10), choose_cycles("bd", "sd")),
        (
            "[bd [~ sd]] cp",
            None,
            cat(polyrhythm(["bd", polyrhythm([silence(), "sd"])]), "cp"),
        ),
        (
            "{a b c, D E}%2",
            TimeSpan(0, 3),
            slowcat(
                stack(cat("a", "b"), cat("D", "E")),
                stack(cat("c", "a"), cat("D", "E")),
                stack(cat("b", "c"), cat("D", "E")),
            ),
        ),
        ("<a b, c d e>", TimeSpan(0, 3), mini("{a b, c d e}%1")),
        ("bd(3,8)", None, pure("bd").euclid(3, 8)),
        ("bd(3,8,2)", None, pure("bd").euclid(3, 8, 2)),
        ("bd(<3 5>,8,<2 4>)", None, pure("bd").euclid(slowcat(3, 5), 8, slowcat(2, 4))),
        ("bd _ _ sd", None, mini("bd@3 sd")),
        ("bd cp . sd", None, polyrhythm([cat("bd", "cp"), "sd"])),
        ("bd*<2 3 4>", TimeSpan(0, 4), pure("bd").fast(slowcat(2, 3, 4))),
        ("bd/[2 3]", TimeSpan(0, 4), pure("bd").slow(cat(2, 3))),
    ],
)
def test_eval(input_code, query_span, expected_pat):
    pat = mini(input_code)
    assert isinstance(pat, Pattern)
    if not query_span:
        query_span = TimeSpan(0, 1)
    assert sorted(pat.query(query_span)) == sorted(expected_pat.query(query_span))


# @pytest.mark.parametrize(
#     "test_input,expected",
#     [
#         # words
#         ("bd ", []),
#         ("bd#32", []),
#         ("drum_sound", []),
#         # sequences
#         ("bd bd", []),
#         ("bd bd bd ", []),
#         # modifiers
#         ("drum_sound/4", []),
#         ("sn*4 cp!4 bd@8 hh/3", []),
#         ("sn%4", []),  # doesn't work in tidal but works here
#         ("sn*(3/5)", []),  # scalar (fraction) argument of '*'
#         ("sn:35 sn:2 sn", []),  # scalar (fraction) argument of '*'
#         # brackets
#         (" [ bd ] ", []),
#         ("[bd#32]", []),
#         ("[ bd bd bd ]", []),
#         ("[bd@3 ]", []),
#         # bracket modifiers
#         ("[bd#32@3 ]@3", []),
#         ("[-1.000!3 ]@3", []),
#         ("[-1.000!3 bd@3 ]@3", []),
#         # nesting
#         ("[[bd#32@3 ]]", []),
#         ("[ [bd@3 ]@3 bd ]", []),
#         (" [[ bd@3 ]@3] ", []),
#         (" [[ 0.3333@3 ]@3] ", []),
#         (" [[ bd@3 ]@3 bd!2]!3 ", []),
#         # deeper nesting
#         (" [ bd bd [bd bd]@3 [bd [bd bd]!3 ] ]", []),
#         (" [ bd bd [bd bd] [bd [bd bd] ] ]", []),
#         (" [ bd bd [bd bd] [bd [bd bd] ] ]@3", []),
#         (" [ bd [bd [bd [bd [bd  [bd]]]]]]", []),
#         # angle brackets
#         ("< bd cp hh >", []),
#         ("< bd cp <bd hh> >", []),
#         ("< bd cp <bd hh>!2 >!3", []),
#         # curly brackets
#         ("{ bd cp bd }", []),
#         ("{ bd cp bd }%4", []),
#         ("{ bd cp {bd cp sn}%5 }%4", []),
#         # bracket mixtures
#         ("{ bd <cp sn> <bd [cp sn]> [bd hh <hh sn [hh hh hh]>] }", []),
#         # euclidean
#         (" bd(3,8) ", []),
#         (" cp( 3,8, 2) ", []),
#         ("bd(3,4) cp( 3,8, 2) ", []),
#         (" cp( 3,8)!2 ", []),
#         (" cp( 3,8, 2)!2 ", []),
#         (" [bd cp ](3,8) ", []),
#         # patterned euclidean
#         (
#             "bd(3 5 2/3, 5)",
#             [],
#         ),  # works  but i think 3/2 is a fraction, not a slow-modified element
#         (
#             "bd(3 5 <2 3>, <5 7 4>)",
#             [],
#         ),  # works but i don't undertand how we can pattern numbers yet.
#         # euclidean bracket mixtures
#         (
#             "{ bd(3,7) <cp sn(5,8,2)> <bd!3 [cp sn(9,16,5)]> [bd hh(3,5) <hh sn [hh hh(5,8)!3 hh]@2>] }",
#             [],
#         ),
#         # stacks
#         ("[bd, bd bd bd]", []),
#         ("[bd, bd bd bd, cp cp cp cp]", []),
#         ("[bd, [cp cp]!2, [sn sn sn]]", []),
#         ("[bd, [bd bd] bd [sn bd hh] hh hh  ]", []),
#         # euclidan in stacks
#         ("[bd, cp(3,8) ]", []),
#         ("[bd,cp(3,8)]", []),
#         ("[bd, cp(3,8) sn(5,8) ]", []),
#         ("[bd, cp(3,8) sn!3 sn, cp ]", []),
#         ("[bd, cp(3,8), cp(5, 19) ]", []),
#         ("[bd, cp(3,8), bd(3,2,4), cp(5, 19) ]", []),
#         ("[bd, cp(3,8), bd(3 ,<3 8>,4), cp(5, 19) ]", []),
#         # nested stacks
#         ("[bd, [cp, sn!5]  ]", []),
#         ("[bd, cp [cp*2, sn!5]  ]", []),
#         pytest.param(
#             " [[ (3/8)@3 ]@3] ", [], marks=pytest.mark.xfail
#         ),  # fails because number elements aren't handled yet.
#         pytest.param(
#             "[(-1.000/32)@3 ]@3", [], marks=pytest.mark.xfail
#         ),  # fails because number elements aren't handled yet.
#     ],
# )
# def test_parse(benchmark, test_input, expected):
#     # FIXME: Assert expected output
#     assert benchmark(grammar.parse, test_input)


# @pytest.mark.parametrize(
#     "test_input,expected",
#     [
#         ("bd", pure("bd")),
#         ("bd sd", cat(pure("bd"), pure("sd"))),
#         ("drum_sound/4", pure("drum_sound").slow(4)),
#     ],
# )
# def test_eval(test_input, expected):
#     assert mini(test_input).first_cycle() == expected.first_cycle()
