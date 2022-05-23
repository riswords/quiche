def test_const_1():
    return 1


def test_const_2():
    return 2


def test_plus_1():
    return 1 + 2


def test_plus_2():
    return test_const_1() + test_const_2()


def test_plus_3():
    return (1 + 2) + 3


def test_plus_4():
    return 1 + (2 + 3)


def test_plus_5():
    return 1 + 2 + 3 + 2


def test_plus_6(x: int):
    return x + 1 + 2


def test_plus_7(x: int):
    return 1 + 2 + x


def test_plus_8(x: int):
    return 1 + x + 2


def test_string_1():
    return 'a' + 'b'


def test_list_1():
    return [1, 2] + [3, 4]


def test_assign_1():
    y = 5 - 2
    return y


def test_assign_2():
    y = (5 - 4) - 3
    return y


def test_assign_3():
    y = 5 - (4 - 3)
    return y


def test_assign_4(x: int):
    y = x - 3 - 2
    return y


def test_assign_5(x: int):
    y = x - (3 - 2)
    return y
