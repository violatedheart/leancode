from money import cents

TAX = {"US": 0.1, "CA": 0.05}

def total(lines, country, discount=0):
    subtotal = sum(lines)
    taxed = subtotal + TAX.get(country, 0) * subtotal
    return cents(taxed - discount)
