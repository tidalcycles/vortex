import pytest

from vortex.mini import parse_mini


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
                        "modifiers": [
                            {
                                "type": "modifier",
                                "op": "fast",
                                "value": {
                                    "type": "element",
                                    "value": {"type": "number", "value": 2},
                                    "modifiers": [],
                                },
                            }
                        ],
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
                        "modifiers": [
                            {
                                "type": "modifier",
                                "op": "slow",
                                "value": {
                                    "type": "element",
                                    "value": {"type": "number", "value": 3},
                                    "modifiers": [],
                                },
                            }
                        ],
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
                            {
                                "type": "modifier",
                                "op": "degrade",
                                "value": {
                                    "type": "degrade_arg",
                                    "op": "count",
                                    "value": 1,
                                },
                            }
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
                            {
                                "type": "modifier",
                                "op": "degrade",
                                "value": {
                                    "type": "degrade_arg",
                                    "op": "count",
                                    "value": 3,
                                },
                            }
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
                            {
                                "type": "modifier",
                                "op": "degrade",
                                "value": {
                                    "type": "degrade_arg",
                                    "op": "count",
                                    "value": 4,
                                },
                            }
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
                            {
                                "type": "modifier",
                                "op": "degrade",
                                "value": {
                                    "type": "degrade_arg",
                                    "op": "count",
                                    "value": 6,
                                },
                            }
                        ],
                    }
                ],
            },
        ),
        (
            "hh??0.87",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "hh", "index": 0},
                        "modifiers": [
                            {
                                "type": "modifier",
                                "op": "degrade",
                                "value": {
                                    "type": "degrade_arg",
                                    "op": "value",
                                    "value": 0.87,
                                },
                            }
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
                            {
                                "type": "modifier",
                                "op": "degrade",
                                "value": {
                                    "type": "degrade_arg",
                                    "op": "count",
                                    "value": 2,
                                },
                            },
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
                            {
                                "type": "modifier",
                                "op": "slow",
                                "value": {
                                    "type": "element",
                                    "value": {"type": "number", "value": 2},
                                    "modifiers": [
                                        {
                                            "type": "modifier",
                                            "op": "repeat",
                                            "count": 1,
                                        },
                                        {
                                            "type": "modifier",
                                            "op": "degrade",
                                            "value": {
                                                "type": "degrade_arg",
                                                "op": "count",
                                                "value": 1,
                                            },
                                        },
                                    ],
                                },
                            },
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
                            {
                                "type": "modifier",
                                "op": "degrade",
                                "value": {
                                    "type": "degrade_arg",
                                    "op": "count",
                                    "value": 1,
                                },
                            }
                        ],
                    },
                    {"type": "element", "value": {"type": "rest"}, "modifiers": []},
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "sd", "index": 0},
                        "modifiers": [
                            {
                                "type": "modifier",
                                "op": "slow",
                                "value": {
                                    "type": "element",
                                    "value": {"type": "number", "value": 2},
                                    "modifiers": [],
                                },
                            }
                        ],
                    },
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "cp", "index": 0},
                        "modifiers": [
                            {
                                "type": "modifier",
                                "op": "fast",
                                "value": {
                                    "type": "element",
                                    "value": {"type": "number", "value": 3},
                                    "modifiers": [],
                                },
                            }
                        ],
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
        # random sequence
        (
            "bd | sd cp",
            {
                "type": "random_sequence",
                "elements": [
                    {
                        "type": "sequence",
                        "elements": [
                            {
                                "type": "element",
                                "value": {"type": "word", "value": "bd", "index": 0},
                                "modifiers": [],
                            }
                        ],
                    },
                    {
                        "type": "sequence",
                        "elements": [
                            {
                                "type": "element",
                                "value": {"type": "word", "value": "sd", "index": 0},
                                "modifiers": [],
                            },
                            {
                                "type": "element",
                                "value": {"type": "word", "value": "cp", "index": 0},
                                "modifiers": [],
                            },
                        ],
                    },
                ],
            },
        ),
        (
            "bd _ _ sd",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "bd", "index": 0},
                        "modifiers": [{"type": "modifier", "op": "weight", "value": 3}],
                    },
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "sd", "index": 0},
                        "modifiers": [],
                    },
                ],
            },
        ),
        ("bd sd . cp . hh*2", parse_mini("[bd sd] [cp] [hh*2]")),
        (
            "bd*<2 3 4>",
            {
                "type": "sequence",
                "elements": [
                    {
                        "type": "element",
                        "value": {"type": "word", "value": "bd", "index": 0},
                        "modifiers": [
                            {
                                "type": "modifier",
                                "op": "fast",
                                "value": {
                                    "type": "element",
                                    "value": {
                                        "type": "polymeter",
                                        "seqs": [
                                            {
                                                "type": "sequence",
                                                "elements": [
                                                    {
                                                        "type": "element",
                                                        "value": {
                                                            "type": "number",
                                                            "value": 2,
                                                        },
                                                        "modifiers": [],
                                                    },
                                                    {
                                                        "type": "element",
                                                        "value": {
                                                            "type": "number",
                                                            "value": 3,
                                                        },
                                                        "modifiers": [],
                                                    },
                                                    {
                                                        "type": "element",
                                                        "value": {
                                                            "type": "number",
                                                            "value": 4,
                                                        },
                                                        "modifiers": [],
                                                    },
                                                ],
                                            }
                                        ],
                                        "steps": 1,
                                    },
                                    "modifiers": [],
                                },
                            }
                        ],
                    }
                ],
            },
        ),
    ],
)
def test_parse(input_code, expected_ast):
    ast = parse_mini(input_code)
    assert ast == expected_ast
