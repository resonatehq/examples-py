# Detecting Race Conditions

Transitioning from synchronous to asynchronous systems introduces concurrency—and concurrency introduces the possibility of race conditions. A system contains a race condition if the concurrent execution of its processes contains at least one execution order that is considered incorrect. This example explores how Resonate's Determinisitic Simulation Testing capabilities enable you to detect and address concurrency issues such as race conditions.

## Deterministic Simulation Testing

Deterministic Simulation Testing repeatedly executes an application in a simulated environment under changing initial conditions, monitoring that the correctness constraints are maintained across executions. In practice the changing initial conditions are determined by the seed for a pseudo random number generator that the simulator uses to drive the system forward.

**With this you can reproduce an entire execution by restarting the system with the same random seed. No more Heisenbugs. No more flakey tests.**

![Deterministic Simulation Testing](./doc/img/dst.png)

> [!NOTE]
> Learn more about [Deterministic Simulation Testing](https://blog.resonatehq.io/deterministic-simulation-testing)


## Race Conditions

A system contains a race condition if the concurrent composition of its processes, contains at least one execution order that is considered incorrect. The canonical example for a race condition is a Money Transfer: A transfer moves an amount from a source account to a target account while guaranteeing that the source account maintains a non-negative balance. 

Consider the following code:

```py
def transfer(ctx: Context, source: int, target: int, amount: int) -> Generator[Yieldable, Any, None]:
    
    source_balance: int = yield ctx.call(current_balance, account_id=source)

    if source_balance - amount < 0:
        raise NotEnoughFundsError(account_id=source)

    yield ctx.call(
        update_balance,
        account_id=source,
        amount=amount * -1,
    )

    yield ctx.call(
        update_balance,
        account_id=target,
        amount=amount,
    )
```

> [!NOTE]
> transfer does not run in the context of a database transaction; instead, every call to current_balance and update_balance runs in the context of an individual database transaction.

This code contains a race condition! If two transfers read the balance before any one of them updates the balance, both proceed based on the same balance, leading to incorrect results. For example, if `Account` and `Account2` both start with a balance of `100`, the following execution order violates our correctness constraint.

| `transfer(Account1, Account2, 100)` | `transfer(Account1, Account2, 100)` |
| ----------------------------------- | ----------------------------------- |
| `current_balance(Account1) = 100`   |                                     |
|                                     | `current_balance(Account1) =  100`  |
| `update_balance(Account1, -100)`    |                                     |
|                                     | `update_balance(Account1, -100)`    |
| `update_balance(Account2, +100)`    |                                     |
|                                     | `update_balance(Account2, +100)`    |

### Using Resonate DST to Detect Race Conditions

Resonate natively implements Deterministic Simulation Testing and integrates into your prefered testing framework like pytest. Here's an example of how to use Resonate DST to test for race conditions:

```py
@pytest.mark.parametrize("scheduler", resonate.testing.dst([range(5)]))
def test_race_condition(
    scheduler: DSTScheduler, setup_and_teardown: sqlite3.Connection
) -> None:
    conn = setup_and_teardown

    new_accounts = range(1, 4)
    balance_at_creation = 100
    for i in new_accounts:
        conn.execute("INSERT INTO accounts VALUES (?, ?)", (i, balance_at_creation))
    conn.commit()

    scheduler.deps.set("conn", conn)

    scheduler.run(
        [
            partial(
                race_condition.transaction,
                source=scheduler.random.choice(new_accounts),
                target=scheduler.random.choice(new_accounts),
                amount=scheduler.random.randint(0, 200),
            )
            for _ in range(1000)
        ]
    )

    accounts_in_negative: int = conn.execute(
        "SELECT COUNT(*) FROM accounts WHERE balance < 0"
    ).fetchone()[0]

    assert accounts_in_negative == 0, f"Seed {scheduler.seed} causes a failure"
```

### Benefits of Using Resonate DST
- Simplified Concurrent Testing: Resonate DST simplifies the process of testing concurrent executions, making it more accessible and routine for cloud application testing.
- Deterministic Simulation Testing: By randomizing the possible combinations of concurrent executions deterministically, Resonate DST helps identify race conditions that might otherwise be missed, ensuring the robustness of your application.


## How to run

### Using [rye](https://rye.astral.sh) (Recommended)

1. Setup project's virtual environment and install dependencies
```zsh
rye sync
```

2. Run tests
```zsh
rye test
```

### Using pip

1. Install dependencies
```zsh
pip install -r requirements-dev.lock
```

4. Run tests
```zsh
pytest
```

### Result

When you run this test, you will get the following result

```
FAILED tests/test_race_condition.py::test_race_condition[scheduler2] - AssertionError: Seed 2 causes a failure
FAILED tests/test_race_condition.py::test_race_condition[scheduler3] - AssertionError: Seed 3 causes a failure
FAILED tests/test_race_condition.py::test_race_condition[scheduler4] - AssertionError: Seed 4 causes a failure
```