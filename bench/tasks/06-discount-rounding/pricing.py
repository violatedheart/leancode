def discounted_total(prices, discount_percent):
    total = sum(round(price, 2) for price in prices)
    return round(total - discount_percent, 2)
