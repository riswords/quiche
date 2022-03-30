import math


def newton(number):
    """
    Newton's method for square root, according to Copilot
    """
    global test_num
    test_num = 0
    x = number / 2
    while True:
        y = (x + number / x) / 2
        if y == x:
            return y
        x = y


def math_sqrt(number):
    """
    Math.sqrt, according to Copilot
    """
    global test_num
    test_num += 1
    return math.sqrt(number)


def test_newton_1():
    number = math.factorial(169)
    assert abs(newton(number) - math_sqrt(number)) < 1e-05


def test_newton_2():
    for i in range(1000):
        result = newton(math.factorial(169)) + i
        assert result > i


def test_math_sqrt_1():
    number = math.factorial(169)
    assert math_sqrt(number) == math.sqrt(number)


def test_math_sqrt_2():
    for i in range(1000):
        result = math_sqrt(math.factorial(169)) + i
        assert result > i
