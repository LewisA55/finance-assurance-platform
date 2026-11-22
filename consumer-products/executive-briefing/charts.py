"""Static SVG charts for the executive deck.

The deck is printed, so the charts carry no hover layer; every plotted value is
also in the evidence appendix, which serves as the table view. Marks follow one
set of specs: columns at most 24px wide with a 4px rounded data end and a square
baseline, 2px lines, 8px end markers with a surface ring, hairline solid grid,
a legend for two or more series and labels on endpoints only.
"""
import html
import math
from datetime import date

S1 = "#00806b"  # cash, revenue and ARR. Validated against S2 on the slide surface.
S2 = "#b86f2e"  # debt, EBITDA, overdue receivables, churn and added outflow
TOTAL = "#5f707a"
SPARK = "#9fb0b1"
SURFACE = "#fcfbf7"


def _n(value):
    return f"{value:.1f}"


def _text(x, y, content, cls, anchor="start"):
    return (f'<text x="{_n(x)}" y="{_n(y)}" class="{cls}" text-anchor="{anchor}">'
            f"{html.escape(content)}</text>")


def _line(x1, y1, x2, y2, cls):
    return f'<line x1="{_n(x1)}" y1="{_n(y1)}" x2="{_n(x2)}" y2="{_n(y2)}" class="{cls}"/>'


def _scale(d0, d1, r0, r1):
    return lambda v: r0 + (float(v) - d0) / (d1 - d0) * (r1 - r0)


def _column(x, base, end, width, fill, radius=4):
    """A column from a square baseline to a rounded data end."""
    top, bottom = min(base, end), max(base, end)
    r = min(radius, bottom - top, width / 2)
    right = x + width
    if end <= base:
        d = (f"M{_n(x)},{_n(bottom)}V{_n(top + r)}Q{_n(x)},{_n(top)} {_n(x + r)},{_n(top)}"
             f"H{_n(right - r)}Q{_n(right)},{_n(top)} {_n(right)},{_n(top + r)}V{_n(bottom)}Z")
    else:
        d = (f"M{_n(x)},{_n(top)}V{_n(bottom - r)}Q{_n(x)},{_n(bottom)} {_n(x + r)},{_n(bottom)}"
             f"H{_n(right - r)}Q{_n(right)},{_n(bottom)} {_n(right)},{_n(bottom - r)}V{_n(top)}Z")
    return f'<path d="{d}" fill="{fill}"/>'


def _block(x, top, bottom, width, fill, radius=0):
    return (f'<rect x="{_n(x)}" y="{_n(top)}" width="{_n(width)}" height="{_n(max(bottom - top, 0))}" '
            f'rx="{radius}" fill="{fill}"/>')


def _dot(x, y, fill):
    return f'<circle cx="{_n(x)}" cy="{_n(y)}" r="4.5" fill="{fill}" stroke="{SURFACE}" stroke-width="2"/>'


def hatch(pattern_id):
    """The texture for capacity that is reported but not evidenced as drawable."""
    return (f'<pattern id="{pattern_id}" patternUnits="userSpaceOnUse" width="5" height="5" '
            f'patternTransform="rotate(45)"><rect width="5" height="5" fill="#e3ece9"/>'
            f'<rect width="1.8" height="5" fill="#8aa8a6"/></pattern>')


def _legend(x, y, items):
    parts, cursor = [], x
    for kind, fill, label in items:
        if kind == "line":
            parts.append(f'<line x1="{_n(cursor)}" y1="{_n(y - 4)}" x2="{_n(cursor + 14)}" y2="{_n(y - 4)}" '
                         f'stroke="{fill}" stroke-width="2" stroke-linecap="round"/>')
            offset = 20
        else:
            parts.append(f'<rect x="{_n(cursor)}" y="{_n(y - 9)}" width="10" height="10" rx="2" fill="{fill}"/>')
            offset = 15
        parts.append(_text(cursor + offset, y, label, "c-legend"))
        cursor += offset + 6.6 * len(label) + 24
    return "".join(parts)


def _svg(width, height, body, label, defs=""):
    defs = f"<defs>{defs}</defs>" if defs else ""
    return (f'<svg class="chart" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
            f'role="img" aria-label="{html.escape(label)}">{defs}{"".join(body)}</svg>')


def _grid(y, left, right, values, label):
    parts = []
    for value in values:
        parts.append(_line(left, y(value), right, y(value), "c-zero" if value == 0 else "c-grid"))
        parts.append(_text(left - 8, y(value) + 4, label(value), "c-tick", "end"))
    return parts


def _months(slots, x_of, y, years=True):
    parts = []
    for index, period in enumerate(slots):
        month = date(int(period[:4]), int(period[5:]), 1)
        parts.append(_text(x_of(index), y, f"{month:%b}", "c-tick", "middle"))
        if years and (index == 0 or month.month == 1):
            parts.append(_text(x_of(index), y + 15, str(month.year), "c-tick c-year", "middle"))
    return parts


def facility(quarters, limit, labels):
    """Drawn debt and undrawn capacity at each quarter-end, against the combined limits."""
    width, height, left, right, top, bottom = 760, 440, 52, 150, 40, 34
    y = _scale(0, limit, height - bottom, top)
    body = [_legend(left, 14, [("box", S2, "Drawn term loan"), ("box", "url(#hatch-facility)", "Undrawn")])]
    body += _grid(y, left, width - right, range(0, int(limit) + 1, 10), lambda v: f"£{v}m")
    slot = (width - left - right) / len(quarters)
    bar = min(20, slot - 8)
    for index, (period, drawn, _undrawn) in enumerate(quarters):
        x = left + index * slot + (slot - bar) / 2
        body.append(_block(x, y(drawn), y(0), bar, S2))
        body.append(_column(x, y(drawn) - 2, y(limit), bar, "url(#hatch-facility)"))
        if period.endswith("-03"):
            body.append(_text(x + bar / 2, height - bottom + 18, period[:4], "c-tick", "middle"))
    last_drawn = quarters[-1][1]
    label_x = width - right + 12
    body.append(_text(label_x, y(limit) + 4, labels["limit"], "c-value"))
    for row, line in enumerate(labels["limit_note"]):
        body.append(_text(label_x, y(limit) + 19 + row * 14, line, "c-note"))
    middle = (last_drawn + limit) / 2
    body.append(_text(label_x, y(middle), labels["undrawn"], "c-value"))
    body.append(_text(label_x, y(middle) + 15, "undrawn", "c-note"))
    body.append(_text(label_x, y(last_drawn / 2), labels["drawn"], "c-value"))
    body.append(_text(label_x, y(last_drawn / 2) + 15, "drawn", "c-note"))
    return _svg(width, height, body, labels["aria"], hatch("hatch-facility"))


def waterfall(steps, ceiling, label):
    """A bridge from one total to the next. Steps are (lines, kind, start, end, text)."""
    width, height, left, right, top, bottom = 760, 440, 52, 16, 26, 52
    y = _scale(0, ceiling, height - bottom, top)
    body = _grid(y, left, width - right, range(0, int(ceiling) + 1), lambda v: f"£{v}m")
    slot = (width - left - right) / len(steps)
    bar = 24
    for index, (lines, kind, start, end, text) in enumerate(steps):
        x = left + index * slot + (slot - bar) / 2
        if kind == "total":
            body.append(_column(x, y(0), y(end), bar, TOTAL))
        else:
            fill = S2 if end > start else S1
            body.append(_block(x, y(max(start, end)), y(min(start, end)), bar, fill, 2))
        body.append(_text(x + bar / 2, y(max(start, end)) - 9, text, "c-value", "middle"))
        for row, line in enumerate(lines):
            body.append(_text(x + bar / 2, height - bottom + 19 + row * 15, line, "c-label", "middle"))
        if index + 1 < len(steps):
            body.append(_line(x + bar, y(end), x + slot, y(end), "c-connector"))
    return _svg(width, height, body, label)


def diverging(months, revenue, ebitda, labels):
    """Monthly revenue above the zero line and EBITDA below it, on one axis."""
    width, height, left, right, top, bottom = 760, 440, 52, 16, 40, 40
    high = math.ceil(max(revenue) / 0.5) * 0.5
    low = math.floor(min(ebitda) / 0.5) * 0.5
    y = _scale(low, high, height - bottom, top)
    body = [_legend(left, 14, [("box", S1, "Revenue"), ("box", S2, "EBITDA")])]
    body += _grid(y, left, width - right, range(math.ceil(low), math.floor(high) + 1), _signed_millions)
    slot = (width - left - right) / len(months)
    bar = 22
    x_of = lambda i: left + i * slot + slot / 2  # noqa: E731
    for index in range(len(months)):
        x = x_of(index) - bar / 2
        body.append(_column(x, y(0) - 1, y(revenue[index]), bar, S1))
        body.append(_column(x, y(0) + 1, y(ebitda[index]), bar, S2))
    for index, key in ((0, "first"), (len(months) - 1, "last")):
        body.append(_text(x_of(index), y(revenue[index]) - 8, labels[f"revenue_{key}"], "c-value", "middle"))
        body.append(_text(x_of(index), y(ebitda[index]) + 17, labels[f"ebitda_{key}"], "c-value", "middle"))
    body += _months(months, x_of, height - bottom + 22, years=False)
    return _svg(width, height, body, labels["aria"])


def _signed_millions(value):
    return f"\u2212£{abs(value)}m" if value < 0 else f"£{value}m"


def arr(months, arr_values, churn_values, labels):
    """ARR at each month-end with monthly MRR churn beneath it on the same months."""
    width, height, left, right, top = 760, 440, 64, 104, 30
    line_bottom, churn_top, churn_bottom = 262, 320, 386
    low = math.floor(min(arr_values) * 5) / 5
    high = math.ceil(max(arr_values) * 5) / 5
    y = _scale(low, high, line_bottom, top)
    slot = (width - left - right) / len(months)
    x_of = lambda i: left + i * slot + slot / 2  # noqa: E731
    ticks = [round(low + step * 0.2, 1) for step in range(round((high - low) / 0.2) + 1)]
    body = _grid(y, left, width - right, ticks, lambda v: f"£{v:.1f}m")
    points = " ".join(f"{_n(x_of(i))},{_n(y(v))}" for i, v in enumerate(arr_values))
    body.append(f'<polyline points="{points}" fill="none" stroke="{S1}" stroke-width="2" '
                f'stroke-linejoin="round" stroke-linecap="round"/>')
    for index in (0, len(months) - 1):
        body.append(_dot(x_of(index), y(arr_values[index]), S1))
    body.append(_text(x_of(0) + 10, y(arr_values[0]) - 10, labels["arr_first"], "c-value"))
    body.append(_text(x_of(len(months) - 1) + 12, y(arr_values[-1]) + 4, labels["arr_last"], "c-value"))
    body.append(_text(x_of(len(months) - 1) + 12, y(arr_values[-1]) + 19, "ending ARR", "c-note"))

    peak = max(churn_values)
    c = _scale(0, peak, churn_bottom, churn_top)
    body.append(_text(left, churn_top - 16, "Monthly MRR churn", "c-label"))
    body.append(_line(left, churn_bottom, width - right, churn_bottom, "c-zero"))
    offset = len(months) - len(churn_values)
    for index, value in enumerate(churn_values):
        if value:
            body.append(_column(x_of(index + offset) - 9, churn_bottom, c(value), 18, S2))
    body.append(_text(x_of(len(months) - 1) + 14, c(peak) + 10, labels["churn_last"], "c-value"))
    body += _months(months, x_of, churn_bottom + 20)
    return _svg(width, height, body, labels["aria"])


def two_lines(months, first, second, labels):
    """Two GBP series at month-ends on one zero-based axis."""
    width, height, left, right, top, bottom = 760, 440, 52, 176, 40, 44
    ceiling = math.ceil(max(first + second) / 10) * 10
    y = _scale(0, ceiling, height - bottom, top)
    slot = (width - left - right) / len(months)
    x_of = lambda i: left + i * slot + slot / 2  # noqa: E731
    body = [_legend(left, 14, [("line", S1, labels["first_name"]), ("line", S2, labels["second_name"])])]
    body += _grid(y, left, width - right, range(0, ceiling + 1, 10), lambda v: f"£{v}m")
    for values, colour in ((first, S1), (second, S2)):
        points = " ".join(f"{_n(x_of(i))},{_n(y(v))}" for i, v in enumerate(values))
        body.append(f'<polyline points="{points}" fill="none" stroke="{colour}" stroke-width="2" '
                    f'stroke-linejoin="round" stroke-linecap="round"/>')
        body.append(_dot(x_of(len(months) - 1), y(values[-1]), colour))
    end = x_of(len(months) - 1) + 12
    for values, key in ((first, "first"), (second, "second")):
        body.append(_text(end, y(values[-1]) + 4, labels[f"{key}_last"], "c-value"))
        body.append(_text(end, y(values[-1]) + 19, labels[f"{key}_note"], "c-note"))
    cross = labels["cross_index"]
    body.append(_line(x_of(cross), top + 30, x_of(cross), y(0), "c-marker"))
    body.append(_text(x_of(cross) - 8, top + 42, labels["cross_text"], "c-note", "end"))
    body += _months(months, x_of, height - bottom + 20)
    return _svg(width, height, body, labels["aria"])


def sparkline(values, label, width=210, height=40):
    low, high = min(values), max(values)
    pad = 5
    y = _scale(low, high if high != low else low + 1, height - pad, pad)
    step = (width - 2 * pad) / (len(values) - 1)
    points = " ".join(f"{_n(pad + i * step)},{_n(y(v))}" for i, v in enumerate(values))
    body = [f'<polyline points="{points}" fill="none" stroke="{SPARK}" stroke-width="2" '
            f'stroke-linejoin="round" stroke-linecap="round"/>',
            _dot(pad + (len(values) - 1) * step, y(values[-1]), S1)]
    return _svg(width, height, body, label).replace('class="chart"', 'class="spark"')


def timeline(start, end, months, band, markers, label):
    """Dates from the close to the next quarter-end. Markers are (date, lines, row, kind)."""
    width, height, left, right = 1168, 236, 8, 8
    axis = 170
    x = _scale(0, (end - start).days, left, width - right)
    at = lambda day: x((day - start).days)  # noqa: E731
    body = [_line(left, axis, width - right, axis, "c-zero")]
    for day, name in months:
        body.append(_line(at(day), axis - 5, at(day), axis + 5, "c-axis-tick"))
        body.append(_text(at(day) + 6, axis + 20, name, "c-tick"))
    band_start, band_end, band_lines = band
    body.append(_block(at(band_start), axis - 3, axis + 3, at(band_end) - at(band_start), S2, 1.5))
    for row, line in enumerate(band_lines):
        body.append(_text(at(band_start) + 8, axis - 28 + row * 15, line, "c-label" if row == 0 else "c-note"))
    for day, lines, row, kind in markers:
        px = at(day)
        fill = {"close": TOTAL, "action": S1, "risk": S2}[kind]
        base = axis - 22 - row * 44 if row >= 0 else axis + 36
        body.append(_line(px, base + (8 if row >= 0 else -12), px, axis, "c-marker"))
        body.append(_dot(px, axis, fill))
        anchor = "end" if px > width - 160 else "start"
        shift = -6 if anchor == "end" else 6
        for index, line in enumerate(lines):
            body.append(_text(px + shift, base - 4 + index * 14 - (len(lines) - 1) * 14 * (row >= 0),
                              line, "c-label" if index == 0 else "c-note", anchor))
    return _svg(width, height, body, label)
