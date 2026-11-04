from records import normalize_amount


def total_amount(rows):
    return sum(normalize_amount(row) for row in rows)
