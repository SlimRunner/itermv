from os.path import dirname

def nonNegativeNumber(arg: str):
    value = int(arg)
    if value < 0:
        raise ValueError("Staring number must be positive")
    return value


def positiveRadix(arg: str):
    value = int(arg)
    if value <= 1:
        raise ValueError("Radix must be greater than 1")
    return value


def identifyCycle(
    graph: dict[str, str], visited: set[str], seed: str
) -> tuple[str | None, str | None]:
    # this function can only handle graphs without branching
    visited.add(seed)
    prev = None
    node = graph[seed]
    while node is not None and node != seed:
        if node not in graph or node in visited:
            visited.add(node)
            prev = node
            node = None
        else:
            visited.add(node)
            node = graph[node]

    return (node, prev)


def isTopLevelPath(name: str):
    path = dirname(name)
    return path == '' or path == '.'


def validateFilename(name: str) -> None:
    # this was used as reference
    # https://stackoverflow.com/a/31976060

    # For the sake of cross compatibility I will disallow everything
    # regardless of platform. My reasoning is that mass renaming lots of
    # files to things that aren't cross compatible is like willingly
    # asking to get shot in the foot.

    BLC_WINDOWS = '<>:"/\\|?*'
    BLN_WINDOWS = [
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    ]

    BLC_UNIX = "/"
    BLN_UNIX = [".", ".."]

    BLC_MACOS = ":/"

    for case in BLN_WINDOWS:
        if name.upper() == case:
            raise SystemError(f"'{name}' is reserved by Windows.")
        elif name == BLN_UNIX:
            raise SystemError(f"'{name}' is reserved by Unix systems.")

    if name[-1] == ".":
        raise SystemError("Filenames in Windows cannot end in dot.")

    for char in BLC_UNIX:
        if char in name:
            raise SystemError(f"'{char}' is a reserved character in Unix systems.")

    for char in BLC_MACOS:
        if char in name:
            raise SystemError(f"'{char}' is a reserved character in MacOS.")

    for char in BLC_WINDOWS:
        if char in name:
            raise SystemError(f"'{char}' is a reserved character in Windows.")
