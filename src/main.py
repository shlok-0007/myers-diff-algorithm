import sys


KEEP = " "
DELETE = "-"
INSERT = "+"


def read_lines(path):
    with open(path, "rb") as f:
        data = f.read()
    parts = data.split(b"\n")
    if parts and parts[-1] == b"":
        parts.pop()
    return parts


def myers_middle(a, b):
    n = len(a)
    m = len(b)
    if n == 0:
        return [(INSERT, item) for item in b]
    if m == 0:
        return [(DELETE, item) for item in a]

    max_d = n + m
    v = {1: 0}
    trace = []

    for d in range(max_d + 1):
        current = {}
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
                x = v.get(k + 1, 0)
            else:
                x = v.get(k - 1, 0) + 1

            y = x - k
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            current[k] = x
            if x >= n and y >= m:
                trace.append(current)
                return backtrack(trace, a, b)

        trace.append(current)
        v = current

    return []


def backtrack(trace, a, b):
    x = len(a)
    y = len(b)
    edits = []

    for d in range(len(trace) - 1, 0, -1):
        previous = trace[d - 1]
        k = x - y

        if k == -d or (k != d and previous.get(k - 1, -1) < previous.get(k + 1, -1)):
            previous_k = k + 1
        else:
            previous_k = k - 1

        previous_x = previous[previous_k]
        previous_y = previous_x - previous_k

        while x > previous_x and y > previous_y:
            x -= 1
            y -= 1
            edits.append((KEEP, a[x]))

        if x == previous_x:
            y -= 1
            edits.append((INSERT, b[y]))
        else:
            x -= 1
            edits.append((DELETE, a[x]))

    while x > 0 and y > 0:
        x -= 1
        y -= 1
        edits.append((KEEP, a[x]))

    edits.reverse()
    return edits


def myers_diff(a, b):
    prefix = 0
    max_prefix = min(len(a), len(b))
    while prefix < max_prefix and a[prefix] == b[prefix]:
        prefix += 1

    suffix = 0
    max_suffix = min(len(a) - prefix, len(b) - prefix)
    while suffix < max_suffix and a[len(a) - 1 - suffix] == b[len(b) - 1 - suffix]:
        suffix += 1

    edits = []
    for i in range(prefix):
        edits.append((KEEP, a[i]))

    a_end = len(a) - suffix
    b_end = len(b) - suffix
    edits.extend(myers_middle(a[prefix:a_end], b[prefix:b_end]))

    if suffix:
        for i in range(len(a) - suffix, len(a)):
            edits.append((KEEP, a[i]))

    return reorder_change_blocks(edits)


def reorder_change_blocks(edits):
    ordered = []
    i = 0
    while i < len(edits):
        op, item = edits[i]
        if op == KEEP:
            ordered.append((op, item))
            i += 1
            continue

        deletes = []
        inserts = []
        while i < len(edits) and edits[i][0] != KEEP:
            op, item = edits[i]
            if op == DELETE:
                deletes.append(item)
            else:
                inserts.append(item)
            i += 1

        ordered.extend((DELETE, item) for item in deletes)
        ordered.extend((INSERT, item) for item in inserts)

    return ordered


def write_prefixed(prefix, line):
    sys.stdout.buffer.write(prefix + line + b"\n")


def run_lines(a_lines, b_lines):
    for op, line in myers_diff(a_lines, b_lines):
        if op == KEEP:
            write_prefixed(b" ", line)
        elif op == DELETE:
            write_prefixed(b"-", line)
        else:
            write_prefixed(b"+", line)


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
            ranges.append(str(start) + "-" + str(end))
            start = pos
            end = pos + 1
    ranges.append(str(start) + "-" + str(end))
    return ",".join(ranges)


def changed_ranges(old_line, new_line):
    old_chars = list(old_line.decode("utf-8"))
    new_chars = list(new_line.decode("utf-8"))
    edits = myers_diff(old_chars, new_chars)

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

    return to_ranges(old_positions), to_ranges(new_positions)


def write_change_block(deletes, inserts):
    pair_count = min(len(deletes), len(inserts))

    for line in deletes:
        write_prefixed(b"-", line)

    for i, line in enumerate(inserts):
        write_prefixed(b"+", line)
        if i < pair_count:
            old_ranges, new_ranges = changed_ranges(deletes[i], line)
            marker = ("? " + old_ranges + " | " + new_ranges + "\n").encode("ascii")
            sys.stdout.buffer.write(marker)


def run_highlight(a_lines, b_lines):
    edits = myers_diff(a_lines, b_lines)
    i = 0
    while i < len(edits):
        op, line = edits[i]
        if op == KEEP:
            write_prefixed(b" ", line)
            i += 1
            continue

        deletes = []
        inserts = []
        while i < len(edits) and edits[i][0] != KEEP:
            op, line = edits[i]
            if op == DELETE:
                deletes.append(line)
            else:
                inserts.append(line)
            i += 1

        write_change_block(deletes, inserts)


def main(argv):
    if len(argv) != 4 or argv[1] not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A B", file=sys.stderr)
        return 2

    command = argv[1]
    try:
        a_lines = read_lines(argv[2])
        b_lines = read_lines(argv[3])
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if command == "lines":
        run_lines(a_lines, b_lines)
    else:
        run_highlight(a_lines, b_lines)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
