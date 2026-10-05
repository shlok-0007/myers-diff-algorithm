import sys
from array import array


KEEP = " "
DELETE = "-"
INSERT = "+"


# ============================================================
# FILE READING
# ============================================================

def read_lines(path):
    with open(path, "rb") as f:
        data = f.read()

    parts = data.split(b"\n")

    if parts and parts[-1] == b"":
        parts.pop()

    return parts


# ============================================================
# COMPACT MYERS DIFF
#
# Each V frontier stores only the active diagonals:
#
# d = 0 -> 1 value
# d = 1 -> 2 values
# d = 2 -> 3 values
# ...
#
# array('i') is much smaller than Python dict/list objects.
# ============================================================

def myers_middle(a, b):
    n = len(a)
    m = len(b)

    if n == 0:
        return [(INSERT, x) for x in b]

    if m == 0:
        return [(DELETE, x) for x in a]

    max_d = n + m

    # v[k + offset] -> furthest x
    offset = max_d + 1
    v = array("i", [0]) * (2 * max_d + 3)

    trace = []

    for d in range(max_d + 1):

        # Store ONLY the values belonging to this d.
        # k = -d, -d+2, ..., d
        current = array("i", [0]) * (d + 1)

        for j in range(d + 1):
            k = -d + 2 * j
            idx = k + offset

            if k == -d:
                x = v[idx + 1]

            elif k == d:
                x = v[idx - 1] + 1

            elif v[idx - 1] < v[idx + 1]:
                x = v[idx + 1]

            else:
                x = v[idx - 1] + 1

            y = x - k

            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            current[j] = x
            v[idx] = x

            if x >= n and y >= m:
                trace.append(current)
                return backtrack_compact(
                    trace,
                    a,
                    b
                )

        trace.append(current)

    return []


def backtrack_compact(trace, a, b):
    x = len(a)
    y = len(b)

    edits = []

    for d in range(len(trace) - 1, 0, -1):

        previous = trace[d - 1]

        k = x - y

        # Previous frontier has diagonals:
        #
        # -(d-1), -(d-3), ..., d-1
        #
        # Convert previous k to array index.
        if k == -d:
            previous_k = k + 1

        elif k == d:
            previous_k = k - 1

        else:
            # Compare V[k-1] and V[k+1].
            #
            # Previous array index:
            # index = (k + (d-1)) // 2
            #
            left_index = (k - 1 + (d - 1)) // 2
            right_index = (k + 1 + (d - 1)) // 2

            if previous[left_index] < previous[right_index]:
                previous_k = k + 1
            else:
                previous_k = k - 1

        previous_index = (
            previous_k + (d - 1)
        ) // 2

        previous_x = previous[previous_index]
        previous_y = previous_x - previous_k

        # Follow the diagonal.
        while x > previous_x and y > previous_y:
            x -= 1
            y -= 1

            edits.append(
                (KEEP, a[x])
            )

        # Insertion.
        if x == previous_x:
            y -= 1

            edits.append(
                (INSERT, b[y])
            )

        # Deletion.
        else:
            x -= 1

            edits.append(
                (DELETE, a[x])
            )

    # Remaining common prefix.
    while x > 0 and y > 0:
        x -= 1
        y -= 1

        edits.append(
            (KEEP, a[x])
        )

    edits.reverse()

    return edits


# ============================================================
# TOP LEVEL MYERS DIFF
# ============================================================

def myers_diff(a, b):
    n = len(a)
    m = len(b)

    # --------------------------------------------------------
    # Common prefix
    # --------------------------------------------------------

    prefix = 0
    limit = min(n, m)

    while (
        prefix < limit
        and a[prefix] == b[prefix]
    ):
        prefix += 1

    # --------------------------------------------------------
    # Common suffix
    # --------------------------------------------------------

    suffix = 0

    while (
        suffix < n - prefix
        and suffix < m - prefix
        and a[n - 1 - suffix] == b[m - 1 - suffix]
    ):
        suffix += 1

    edits = []

    # Prefix
    for i in range(prefix):
        edits.append(
            (KEEP, a[i])
        )

    a_end = n - suffix
    b_end = m - suffix

    # Middle
    if prefix < a_end or prefix < b_end:
        edits.extend(
            myers_middle(
                a[prefix:a_end],
                b[prefix:b_end]
            )
        )

    # Suffix
    for i in range(a_end, n):
        edits.append(
            (KEEP, a[i])
        )

    return reorder_change_blocks(edits)


# ============================================================
# ORDER CHANGE BLOCKS
# ============================================================

def reorder_change_blocks(edits):
    result = []

    i = 0
    length = len(edits)

    while i < length:

        op, item = edits[i]

        if op == KEEP:
            result.append(
                (KEEP, item)
            )
            i += 1
            continue

        deletes = []
        inserts = []

        while (
            i < length
            and edits[i][0] != KEEP
        ):
            op, item = edits[i]

            if op == DELETE:
                deletes.append(item)
            else:
                inserts.append(item)

            i += 1

        result.extend(
            (DELETE, item)
            for item in deletes
        )

        result.extend(
            (INSERT, item)
            for item in inserts
        )

    return result


# ============================================================
# OUTPUT
# ============================================================

def write_prefixed(prefix, line):
    sys.stdout.buffer.write(prefix)
    sys.stdout.buffer.write(line)
    sys.stdout.buffer.write(b"\n")


def run_lines(a_lines, b_lines):
    edits = myers_diff(
        a_lines,
        b_lines
    )

    for op, line in edits:

        if op == KEEP:
            write_prefixed(
                b" ",
                line
            )

        elif op == DELETE:
            write_prefixed(
                b"-",
                line
            )

        else:
            write_prefixed(
                b"+",
                line
            )


# ============================================================
# RANGES
# ============================================================

def to_ranges(positions):
    if not positions:
        return "."

    ranges = []

    start = positions[0]
    end = start + 1

    for pos in positions[1:]:

        if pos == end:
            end += 1

        else:
            ranges.append(
                str(start)
                + "-"
                + str(end)
            )

            start = pos
            end = pos + 1

    ranges.append(
        str(start)
        + "-"
        + str(end)
    )

    return ",".join(ranges)


# ============================================================
# CHARACTER CHANGES
# ============================================================

def changed_ranges(old_line, new_line):
    old_chars = list(
        old_line.decode("utf-8")
    )

    new_chars = list(
        new_line.decode("utf-8")
    )

    edits = myers_diff(
        old_chars,
        new_chars
    )

    old_positions = []
    new_positions = []

    old_index = 0
    new_index = 0

    for op, _ in edits:

        if op == KEEP:
            old_index += 1
            new_index += 1

        elif op == DELETE:
            old_positions.append(
                old_index
            )
            old_index += 1

        else:
            new_positions.append(
                new_index
            )
            new_index += 1

    return (
        to_ranges(old_positions),
        to_ranges(new_positions)
    )


# ============================================================
# HIGHLIGHT CHANGE BLOCK
# ============================================================

def write_change_block(
    deletes,
    inserts
):
    pair_count = min(
        len(deletes),
        len(inserts)
    )

    for line in deletes:
        write_prefixed(
            b"-",
            line
        )

    for i, line in enumerate(inserts):

        write_prefixed(
            b"+",
            line
        )

        if i < pair_count:

            old_ranges, new_ranges = (
                changed_ranges(
                    deletes[i],
                    line
                )
            )

            marker = (
                "? "
                + old_ranges
                + " | "
                + new_ranges
                + "\n"
            ).encode("ascii")

            sys.stdout.buffer.write(
                marker
            )


# ============================================================
# HIGHLIGHT
# ============================================================

def run_highlight(
    a_lines,
    b_lines
):
    edits = myers_diff(
        a_lines,
        b_lines
    )

    i = 0
    length = len(edits)

    while i < length:

        op, line = edits[i]

        if op == KEEP:

            write_prefixed(
                b" ",
                line
            )

            i += 1
            continue

        deletes = []
        inserts = []

        while (
            i < length
            and edits[i][0] != KEEP
        ):

            op, line = edits[i]

            if op == DELETE:
                deletes.append(line)

            else:
                inserts.append(line)

            i += 1

        write_change_block(
            deletes,
            inserts
        )


# ============================================================
# MAIN
# ============================================================

def main(argv):

    if (
        len(argv) != 4
        or argv[1]
        not in ("lines", "highlight")
    ):
        print(
            "usage: main.py lines|highlight A B",
            file=sys.stderr
        )
        return 2

    command = argv[1]

    try:
        a_lines = read_lines(
            argv[2]
        )

        b_lines = read_lines(
            argv[3]
        )

    except OSError as exc:

        print(
            str(exc),
            file=sys.stderr
        )

        return 2

    if command == "lines":

        run_lines(
            a_lines,
            b_lines
        )

    else:

        run_highlight(
            a_lines,
            b_lines
        )

    return 0


if __name__ == "__main__":
    sys.exit(
        main(sys.argv)
    )