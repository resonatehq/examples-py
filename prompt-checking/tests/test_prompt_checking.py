import time

import prompt_checking
import resonate


def test_query() -> None:
    for s in resonate.testing.dst(seeds=[range(1)]):
        s.add(prompt_checking.generate_a_joke, seed=s.seed)
        p = s.run()[0]
        assert p.success(), f"seed {s.seed} causes an invalid response."
        time.sleep(10)
