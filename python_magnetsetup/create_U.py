from typing import List, Optional


def add_create_U(template: str, debug: bool = False):
    """
    Create a py file
    """
    print(f"create_U.py from {template}")

    import chevron

    if debug:
        print("entry/loading %s" % str(template), type(template))
    with open(template, "r") as f:
        pyfile = chevron.render(f)
    pyfile = pyfile.replace("'", '"')
    if debug:
        print(f"create_U")

    with open("create_U.py", "w+") as out:
        out.write(pyfile)

    pass
