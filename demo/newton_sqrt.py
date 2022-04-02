def newton(number):
    """
    Newton's method for square root
    """
    x = number / 2
    while True:
        y = (x + number / x) / 2
        if y == x:
            return y
        x = y
