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
