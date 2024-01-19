from guppylang.decorator import guppy


@guppy
def is_even(x: int) -> bool:
    if x == 0:
        return True
    return is_odd(x - 1)


@guppy
def is_odd(x: int) -> bool:
    if x == 0:
        return False
    return is_even(x - 1)

@guppy
def main() -> bool:
    return is_even(4) and is_odd(5)
