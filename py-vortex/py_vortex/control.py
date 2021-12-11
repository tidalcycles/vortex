from .pattern import S, F
# Create functions for making control patterns (patterns of dictionaries)
controls = [
    (S, "S", ["s", "vowel"]),
    (F, "F", ["n", "note", "gain", "pan", "speed", "room", "size"])
]

# This had to go in its own function, for weird scoping reasons..
def setter(cls, clsname, name):
    setattr(cls, name, lambda pat: Control(pat.fmap(lambda v: {name: v}).query))

for controltype in controls:
    cls = controltype[0]
    clsname = controltype[1]
    for name in controltype[2]:
        setter(cls, clsname, name)
        # Couldn't find a better way of adding functions to __main__ ..
        exec("%s = %s.%s" % (name, clsname, name))