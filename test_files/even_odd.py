from guppylang.decorator import guppy
from guppylang.module import GuppyModule

module = GuppyModule("module")


@guppy(module)
def is_even(x: int) -> bool:
    if x == 0:
        return True
    return is_odd(x - 1)


@guppy(module)
def is_odd(x: int) -> bool:
    if x == 0:
        return False
    return is_even(x - 1)

@guppy(module)
def main() -> bool:
    return is_even(4) and is_odd(5)
