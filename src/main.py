import sys


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
# LINEAR-SPACE MYERS
#
# Returns a minimal edit script.
#
# Unlike the normal Myers implementation, this does NOT keep
# every V array for traceback.
#
# Working memory: O(min(N, M))
# ============================================================

def myers_middle(a, b):
    n = len(a)
    m = len(b)

    if n == 0:
        return [(INSERT, x) for x in b]

    if m == 0:
        return [(DELETE, x) for x in a]

    # --------------------------------------------------------
    # Common prefix
    # --------------------------------------------------------

    prefix = 0
    limit = min(n, m)

    while prefix < limit and a[prefix] == b[prefix]:
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

    result = []

    for i in range(prefix):
        result.append((KEEP, a[i]))

    middle_a = a[prefix:n - suffix]
    middle_b = b[prefix:m - suffix]

    if middle_a or middle_b:
        result.extend(_linear_myers(middle_a, middle_b))

    for i in range(n - suffix, n):
        result.append((KEEP, a[i]))

    return result


def _linear_myers(a, b):
    n = len(a)
    m = len(b)

    if n == 0:
        return [(INSERT, x) for x in b]

    if m == 0:
        return [(DELETE, x) for x in a]

    # Very small cases avoid allocating Myers frontiers.
    if n == 1:
        item = a[0]

        for j, value in enumerate(b):
            if item == value:
                return (
                    [(INSERT, x) for x in b[:j]]
                    + [(KEEP, item)]
                    + [(INSERT, x) for x in b[j + 1:]]
                )

        return (
            [(DELETE, item)]
            + [(INSERT, x) for x in b]
        )

    if m == 1:
        item = b[0]

        for i, value in enumerate(a):
            if item == value:
                return (
                    [(DELETE, x) for x in a[:i]]
                    + [(KEEP, item)]
                    + [(DELETE, x) for x in a[i + 1:]]
                )

        return (
            [(DELETE, x) for x in a]
            + [(INSERT, item)]
        )

    # --------------------------------------------------------
    # Myers middle split
    # --------------------------------------------------------

    total = n + m
    max_d = (total + 1) // 2
    delta = n - m

    size = 2 * max_d + 3
    offset = max_d + 1

    forward = [0] * size
    reverse = [n] * size

    odd = delta & 1

    for d in range(max_d + 1):

        # ====================================================
        # Forward search
        # ====================================================

        for k in range(-d, d + 1, 2):
            idx = k + offset

            if k == -d:
                x = forward[idx + 1]

            elif k == d:
                x = forward[idx - 1] + 1

            elif forward[idx - 1] < forward[idx + 1]:
                x = forward[idx + 1]

            else:
                x = forward[idx - 1] + 1

            y = x - k

            while (
                x < n
                and y < m
                and a[x] == b[y]
            ):
                x += 1
                y += 1

            forward[idx] = x

            # Forward and reverse paths overlap.
            if odd:
                reverse_k = delta - k

                if (
                    -(d - 1) <= reverse_k <= d - 1
                    and x >= reverse[reverse_k + offset]
                ):
                    split_x = x
                    split_y = y

                    return _split(
                        a,
                        b,
                        split_x,
                        split_y
                    )

        # ====================================================
        # Reverse search
        # ====================================================

        for k in range(-d, d + 1, 2):
            idx = k + offset

            if k == -d:
                x = reverse[idx + 1] - 1

            elif k == d:
                x = reverse[idx - 1]

            elif reverse[idx - 1] > reverse[idx + 1]:
                x = reverse[idx - 1]

            else:
                x = reverse[idx + 1] - 1

            y = x - (delta - k)

            while (
                x > 0
                and y > 0
                and a[x - 1] == b[y - 1]
            ):
                x -= 1
                y -= 1

            reverse[idx] = x

            if not odd:
                forward_k = delta - k

                if (
                    -d <= forward_k <= d
                    and forward[forward_k + offset] >= x
                ):
                    split_x = x
                    split_y = y

                    return _split(
                        a,
                        b,
                        split_x,
                        split_y
                    )

    # Defensive fallback.
    return (
        [(DELETE, x) for x in a]
        + [(INSERT, x) for x in b]
    )


def _split(a, b, x, y):
    left = _linear_myers(
        a[:x],
        b[:y]
    )

    right = _linear_myers(
        a[x:],
        b[y:]
    )

    left.extend(right)

    return left


# ============================================================
# TOP LEVEL DIFF
# ============================================================

def myers_diff(a, b):
    edits = myers_middle(a, b)
    return reorder_change_blocks(edits)


# ============================================================
# ORDERING
#
# Inside every change block:
#
# DELETE DELETE ...
# INSERT INSERT ...
#
# This guarantees that applying KEEP + INSERT reconstructs B.
# ============================================================

def reorder_change_blocks(edits):
    result = []

    i = 0
    length = len(edits)

    while i < length:
        op, item = edits[i]

        if op == KEEP:
            result.append((KEEP, item))
            i += 1
            continue

        deletes = []
        inserts = []

        while i < length and edits[i][0] != KEEP:
            op, item = edits[i]

            if op == DELETE:
                deletes.append(item)
            else:
                inserts.append(item)

            i += 1

        result.extend((DELETE, x) for x in deletes)
        result.extend((INSERT, x) for x in inserts)

    return result


# ============================================================
# OUTPUT
# ============================================================

def write_prefixed(prefix, line):
    sys.stdout.buffer.write(prefix)
    sys.stdout.buffer.write(line)
    sys.stdout.buffer.write(b"\n")


def run_lines(a_lines, b_lines):
    edits = myers_diff(a_lines, b_lines)

    for op, line in edits:
        if op == KEEP:
            write_prefixed(b" ", line)

        elif op == DELETE:
            write_prefixed(b"-", line)

        else:
            write_prefixed(b"+", line)


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
                str(start) + "-" + str(end)
            )
            start = pos
            end = pos + 1

    ranges.append(
        str(start) + "-" + str(end)
    )

    return ",".join(ranges)


# ============================================================
# CHARACTER-LEVEL DIFF
# ============================================================

def changed_ranges(old_line, new_line):
    old_chars = list(old_line.decode("utf-8"))
    new_chars = list(new_line.decode("utf-8"))

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
            old_positions.append(old_index)
            old_index += 1

        else:
            new_positions.append(new_index)
            new_index += 1

    return (
        to_ranges(old_positions),
        to_ranges(new_positions)
    )


# ============================================================
# HIGHLIGHT
# ============================================================

def write_change_block(deletes, inserts):
    pair_count = min(
        len(deletes),
        len(inserts)
    )

    for line in deletes:
        write_prefixed(b"-", line)

    for i, line in enumerate(inserts):
        write_prefixed(b"+", line)

        if i < pair_count:
            old_ranges, new_ranges = changed_ranges(
                deletes[i],
                line
            )

            marker = (
                "? "
                + old_ranges
                + " | "
                + new_ranges
                + "\n"
            ).encode("ascii")

            sys.stdout.buffer.write(marker)


def run_highlight(a_lines, b_lines):
    edits = myers_diff(
        a_lines,
        b_lines
    )

    i = 0
    length = len(edits)

    while i < length:
        op, line = edits[i]

        if op == KEEP:
            write_prefixed(b" ", line)
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
        or argv[1] not in ("lines", "highlight")
    ):
        print(
            "usage: main.py lines|highlight A B",
            file=sys.stderr
        )
        return 2

    command = argv[1]

    try:
        a_lines = read_lines(argv[2])
        b_lines = read_lines(argv[3])

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
    sys.exit(main(sys.argv))