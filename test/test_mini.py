import pytest

from vortex.mini import mini, parse_mini
from vortex.pattern import Pattern, degrade, fast, fastcat, pure, silence, slow, timecat


@pytest.mark.parametrize(
    "input_code,expected_ast",
    [
        # numbers
        (
            "45",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "number", "value": 45},
                        "modifiers": [],
                    }
                ],
            },
        ),
        (
            "-2.",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "number", "value": -2.0},
                        "modifiers": [],
                    }
                ],
            },
        ),
        (
            "4.64",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "number", "value": 4.64},
                        "modifiers": [],
                    }
                ],
            },
        ),
        (
            "-3",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "number", "value": -3},
                        "modifiers": [],
                    }
                ],
            },
        ),
        # words
        (
            "foo",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "foo", "index": 0},
                        "modifiers": [],
                    }
                ],
            },
        ),
        (
            "Bar:2",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "Bar", "index": 2},
                        "modifiers": [],
                    }
                ],
            },
        ),
        # rest
        (
            "~",
            {
                "type": "sequence",
                "elements": [
                    {"type": "element", "value": {"type": "rest"}, "modifiers": []}
                ],
            },
        ),
        # modifiers
        (
            "bd*2",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "bd", "index": 0},
                        "modifiers": [{"type": "modifier", "op": "fast", "value": 2}],
                    }
                ],
            },
        ),
        (
            "bd/3",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "bd", "index": 0},
                        "modifiers": [{"type": "modifier", "op": "slow", "value": 3}],
                    }
                ],
            },
        ),
        (
            "hh?",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [
                            {"type": "modifier", "op": "degrade", "count": 1}
                        ],
                    }
                ],
            },
        ),
        (
            "hh???",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [
                            {"type": "modifier", "op": "degrade", "count": 3}
                        ],
                    }
                ],
            },
        ),
        (
            "hh?4",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [
                            {"type": "modifier", "op": "degrade", "count": 4}
                        ],
                    }
                ],
            },
        ),
        (
            "hh?4??",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [
                            {"type": "modifier", "op": "degrade", "count": 6}
                        ],
                    }
                ],
            },
        ),
        (
            "hh!",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [{"type": "modifier", "op": "repeat", "count": 1}],
                    }
                ],
            },
        ),
        (
            "hh!!!",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [{"type": "modifier", "op": "repeat", "count": 3}],
                    }
                ],
            },
        ),
        (
            "hh!4",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [{"type": "modifier", "op": "repeat", "count": 4}],
                    }
                ],
            },
        ),
        (
            "hh!4!!",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [{"type": "modifier", "op": "repeat", "count": 6}],
                    }
                ],
            },
        ),
        (
            "hh@2",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [{"type": "modifier", "op": "weight", "value": 2}],
                    }
                ],
            },
        ),
        (
            "hh!!??!",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [
                            {"type": "modifier", "op": "repeat", "count": 2},
                            {"type": "modifier", "op": "repeat", "count": 1},
                            {"type": "modifier", "op": "degrade", "count": 2},
                        ],
                    }
                ],
            },
        ),
        (
            "hh!/2?!",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [
                            {"type": "modifier", "op": "repeat", "count": 1},
                            {"type": "modifier", "op": "slow", "value": 2},
                            {"type": "modifier", "op": "repeat", "count": 1},
                            {"type": "modifier", "op": "degrade", "count": 1},
                        ],
                    }
                ],
            },
        ),
        # sequences
        (
            "bd sd",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "bd", "index": 0},
                        "modifiers": [],
                    },
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "sd", "index": 0},
                        "modifiers": [],
                    },
                ],
            },
        ),
        (
            "bd hh sd",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "bd", "index": 0},
                        "modifiers": [],
                    },
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [],
                    },
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "sd", "index": 0},
                        "modifiers": [],
                    },
                ],
            },
        ),
        (
            "bd! hh? ~ sd/2 cp*3",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "bd", "index": 0},
                        "modifiers": [{"type": "modifier", "op": "repeat", "count": 1}],
                    },
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [
                            {"type": "modifier", "op": "degrade", "count": 1}
                        ],
                    },
                    {"type": "element", "value": {"type": "rest"}, "modifiers": []},
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "sd", "index": 0},
                        "modifiers": [{"type": "modifier", "op": "slow", "value": 2}],
                    },
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "cp", "index": 0},
                        "modifiers": [{"type": "modifier", "op": "fast", "value": 3}],
                    },
                ],
            },
        ),
        # polyrhythms
        (
            "[bd sd] hh",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {
                            "type": "polyrhythm",
                            "seqs": [
                                {
                                    "type": "sequence",
                                    "elements": [
                                        {
                                            "type": "element",
                                            "value": {
                                                "type": "word",
                                                "value": "bd",
                                                "index": 0,
                                            },
                                            "modifiers": [],
                                        },
                                        {
                                            "type": "element",
                                            "value": {
                                                "type": "word",
                                                "value": "sd",
                                                "index": 0,
                                            },
                                            "modifiers": [],
                                        },
                                    ],
                                }
                            ],
                        },
                        "modifiers": [],
                    },
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [],
                    },
                ],
            },
        ),
    ],
)
def test_parse(input_code, expected_ast):
    ast = parse_mini(input_code)
    assert ast == expected_ast


@pytest.mark.parametrize(
    "input_code,expected_pat",
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
            "hh!!??",
            degrade(degrade(fastcat("hh", "hh", "hh"))),
        ),
        # sequences
        ("bd sd", fastcat("bd", "sd")),
        ("bd hh sd", fastcat("bd", "hh", "sd")),
        ("hh@2", pure("hh")),
        ("bd hh@2", timecat((1, "bd"), (2, "hh"))),
        ("bd hh@3 sd@2", timecat((1, "bd"), (3, "hh"), (2, "sd"))),
        ("hh!", fastcat("hh", "hh")),
        ("hh!!", fastcat("hh", "hh", "hh")),
        ("bd! cp", fastcat("bd", "bd", "cp")),
        (
            "bd! hh? ~ sd/2 cp*3",
            timecat(
                (1, "bd"),
                (1, "bd"),
                (1, degrade("hh")),
                (1, silence()),
                (1, slow(2, "sd")),
                (1, fast(3, "cp")),
            ),
        ),
    ],
)
def test_eval(input_code, expected_pat):
    pat = mini(input_code)
    assert isinstance(pat, Pattern)
    assert pat.first_cycle() == expected_pat.first_cycle()


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
#         ("bd sd", fastcat(pure("bd"), pure("sd"))),
#         ("drum_sound/4", pure("drum_sound").slow(4)),
#     ],
# )
# def test_eval(test_input, expected):
#     assert mini(test_input).first_cycle() == expected.first_cycle()
