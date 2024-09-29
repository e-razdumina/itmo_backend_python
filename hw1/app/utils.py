import math
from typing import List


def calculate_factorial(n: int) -> int:
    """
    Calculate the factorial of a number using the built-in math.factorial.

    Args:
        n (int): The number for which the factorial is calculated.

    Returns:
        int: The factorial of the number.
    """
    return math.factorial(n)


def calculate_fibonacci(n: int) -> int:
    """
    Calculate the n-th Fibonacci number using Binet's formula.

    Args:
        n (int): The position in the Fibonacci sequence to calculate.

    Returns:
        int: The n-th Fibonacci number.
    """
    if n < 0:
        raise ValueError("n should be a positive integer")

    phi = (1 + math.sqrt(5)) / 2
    psi = (1 - math.sqrt(5)) / 2
    return round((phi ** n - psi ** n) / math.sqrt(5))


def calculate_mean(numbers: List[float]) -> float:
    """
    Calculate the mean of a list of numbers.

    Args:
        numbers (List[float]): A list of numbers to calculate the mean.

    Returns:
        float: The mean of the list of numbers.
    """
    if not numbers:
        raise ValueError("The list of numbers is empty")
    return sum(numbers) / len(numbers)
