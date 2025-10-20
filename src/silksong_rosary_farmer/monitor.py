import mss


def list_monitors() -> list[tuple[str, int]]:
    """List all monitors with their descriptive labels and indices.

    Returns:
    - Single monitor: ("main", 0)
    - Two monitors: ("left", 1), ("right", 0) based on position
    - Three monitors: ("left", 0), ("center", 2), ("right", 1) based on position

    The labels are dynamic and based on the actual Windows monitor arrangement.
    """

    with mss.mss() as sct:
        # Monitor 0 is the virtual screen encompassing all monitors, fuck it
        monitors = sct.monitors[1:]
        indexed_monitors = [(i, mon) for i, mon in enumerate(monitors)]
        sorted_monitors = sorted(indexed_monitors, key=lambda x: x[1]["left"])

        if len(monitors) == 0:
            return []
        if len(sorted_monitors) == 1:
            return [
                ("main", sorted_monitors[0][0]),
            ]
        if len(sorted_monitors) == 2:
            return [
                ("left", sorted_monitors[0][0]),
                ("right", sorted_monitors[1][0]),
            ]
        if len(sorted_monitors) == 3:
            return [
                ("left", sorted_monitors[0][0]),
                ("center", sorted_monitors[1][0]),
                ("right", sorted_monitors[2][0]),
            ]

        # Duuude, who the fuck has more than 3 monitors?!
        result = []
        for i, (idx, _) in enumerate(sorted_monitors):
            if i == 0:
                result.append(("left", idx))
            elif i == len(sorted_monitors) - 1:
                result.append(("right", idx))
            else:
                result.append((f"center-{i}", idx))
        return result


if __name__ == "__main__":
    print(list_monitors())
