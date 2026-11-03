def fibonacci(n):
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)
