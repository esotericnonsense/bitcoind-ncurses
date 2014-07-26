#!/usr/bin/env python

# thanks go to wumpus / laanwj
def read_file(filename):
    f = open(filename)
    try:
        cfg = {}
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    # replace maintains compatibility with older config files
                    (key, value) = line.replace(' = ','=').split('=', 1)
                    cfg[key] = value
                except ValueError:
                    pass # Happens when line has no '=', ignore
    finally:
        f.close()
    return cfg
