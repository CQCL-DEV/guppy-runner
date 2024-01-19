from guppylang.decorator import guppy
from guppylang.prelude.quantum import Qubit, measure, h, rz

@guppy
def rx(q: Qubit, a: float) -> Qubit:
  # Implement Rx via Rz rotation
  return h(rz(h(q), a))


@guppy
def main() -> bool:
  q = Qubit()
  r = rx(q,1.5)
  return measure(r)
