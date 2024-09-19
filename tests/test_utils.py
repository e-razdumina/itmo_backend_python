import pytest

from app.utils import calculate_factorial, calculate_fibonacci, calculate_mean


def test_calculate_factorial():
    assert calculate_factorial(5) == 120
    assert calculate_factorial(0) == 1
    assert calculate_factorial(1) == 1


def test_calculate_fibonacci():
    assert calculate_fibonacci(10) == 55
    assert calculate_fibonacci(0) == 0
    assert calculate_fibonacci(2) == 1
    with pytest.raises(ValueError):
        calculate_fibonacci(-1)


def test_calculate_mean():
    assert calculate_mean([1, 2, 3, 4, 5]) == 3.0
    assert calculate_mean([1.5, 2.5, 3.5]) == 2.5
    with pytest.raises(ValueError):
        calculate_mean([])
