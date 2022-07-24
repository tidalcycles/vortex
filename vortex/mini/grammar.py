"""
Mini-notation grammar for Vortex.

Grammmar is defined using the PEG parsing library 'parsimonious' version 0.8.1.
Given the set of rules and definitions (grammar) defined in this file,
calling grammar.parse(mn) generates an abstract syntax tree (AST) for a given input mini-notation string named 'mn'.

printing the tree object shows the generated ASTs. e.g.:

```
tree = grammar.parse('"bd(3, 8) cp")
```

yields the following (truncated) AST:

```
<Node called "valid" matching "bd(3, 8) cp">
    <Node called "sequence" matching "bd(3, 8) cp">
        <Node matching "">
            <RegexNode called "ws" matching "">
        <Node called "element" matching "bd(3, 8) ">
            <Node called "modified" matching "bd(3, 8) ">
                <Node called "modifiable" matching "bd">
                    <Node called "word" matching "bd">
                    ...
        <Node matching "cp">
            <Node matching "cp">
                <RegexNode called "ws" matching "">
                <Node matching "cp">
                    <Node called "element" matching "cp">
                        <Node called "word" matching "cp">
```

the '__main__' program contains 54 successfully parsed mini-notation test examples.

The parsimonious lib's readme (https://github.com/erikrose/parsimonious) was all I needed to get started writing
a 'port' of the TidalCycles mini-notation grammar for Vortex.

The strudel PEG grammar written in pegjs by Felix Roos was a valuable starting point, and many ideas were taken from there.
https://github.com/tidalcycles/strudel/blob/main/packages/mini/krill.pegjs

Reach out on the TidalCycles discord or club.tidalcycles.org if you have any bugs, optimizations, or questions.

-Tyler

"""

from parsimonious import Grammar

grammar = Grammar(
    r"""
    start = sequence / (ws? element ws?)

    # contains at least two sequences (or words), comma separated, and surrounded by square brackets
    # e.g., [ bd, [cp cp]]
    stack = ws? lsquare (sequence / (ws? element ws?)) (comma (sequence / (ws? element ws?)))+ rsquare ws?

    # a white-space separated collection of 2 or more elements like "bd bd" or "[bd bd] [bd bd]"
    # underscores (continuation symbol) can be part of a sequence but cannot be the first element.
    sequence = ws? element (ws (element / underscore ))+ ws?

    # an element is a piece of the pattern like "[bd, bd]" , "[bd bd]@2", "bd@2", "[bd bd]" or "bd".
    # does not include things like "bd bd" or "[bd bd]@2" or "bd!2 bd!2" which are each a 'sequence', a collection of elements.
    element = stack / modified / bracketed / sample_select / word / rest

    # TODO:  get groups e.g. "bd bd . hh hh hh" working
    # group = ws? (sequence / element) (ws period ws (sequence / element))+ ws?

    rest = tilde

    ##  [bd sd@3 [bd, sd ] ] with no outer modifier.
    bracketed = square_bracketed / angle_bracketed / curly_bracketed

    square_bracketed = ws? lsquare bracket_contents rsquare ws?

    angle_bracketed = langle bracket_contents rangle

    curly_bracketed = lcurly bracket_contents rcurly

    # valid things that can go inside brackets.
    bracket_contents = ws? ( sequence / element ) ws?

    # a pair containing a modifiable element e.g. "[bd bd]" and a modifier e.g. "@3"
    modified = modifiable modifier

    modifiable = bracketed / word

    # e.g. bd:3
    sample_select = word colon pos_integer

    # single word definition (e.g bd, drum_sound, sample#2)
    word = word_char+
    word_char =  ~"\w" / minus / hashtag / period / "^" / underscore

    # TODO: add numeric element definition?


    #modifier = basic_modifier
    modifier = bjorklund / basic_modifier

    # (3,8), (33 23 15, 16 17, 35),  (3, 8)!3
    # Q: should euclidean pattern arguments take numeric-only patterns? "bd(bd, 8)" is valid tidalcycles.
    # if so, i should make a numeric-only element definition
    # Q:  should we support fractions in bjorklund?
    # Q: why do these fail in tidal:  "bd(3,8)/3" "bd(3,8)*3" "bd(3,8)%3"
    bjorklund = bjork_three_arg / bjork_two_arg
    bjork_three_arg = lparen ws? (sequence / element / number) ws? comma ws? (sequence / element / number) ws? comma ws? (sequence / element / number) ws? rparen ws? basic_modifier?
    bjork_two_arg = lparen ws? (sequence / element / number) ws?  comma ws? (sequence / element / number) ws? rparen ws? basic_modifier?

    basic_modifier = weight / replicate / fast / slow / fixed_step

    # e.g., @7
    weight = at_symbol scalar

    # e.g., !3
    replicate = exclamation_point scalar

    # e.g., *5
    fast = asterisk scalar

    # e.g., /5
    slow = slash scalar

    # e.g., /5
    fixed_step = percent_sign scalar

    # scalars are 3.00001 , (16/15), -35, -343.555, (-10000/15)
    scalar = number / fraction
    fraction = lparen ws? number ws? "/" ws? number ws? rparen
    # NOTE:  consider whether "1." should be valid as opposed to "1.0"  ; "1." is not valid in haskell.
    number = (integer period pos_integer)  / integer
    integer = minus? pos_integer
    pos_integer = !minus ~"[0-9]+"

    # names for symbols
    hashtag = "#"
    underscore = "_"
    tilde = "~"
    minus = "-"
    plus = "+"
    period = "."
    colon = ":"
    comma = ","

    # symbol names for basic modifiers
    asterisk = "*"
    slash = "/"
    at_symbol = "@"
    exclamation_point = "!"
    percent_sign = "%"

    # names for brackets
    lsquare = "["
    rsquare = "]"
    lcurly = "{"
    rcurly = "}"
    langle = "<"
    rangle = ">"
    lparen = "("
    rparen = ")"
    # TODO:  implement random choice with the pipe symbol.
    pipe = "|"

    # NOTE do we care about tabs?
    ws = ~"\s*"
    """
)
