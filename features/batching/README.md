# Batching
## Still sequential looking code, simple, but faster and cheaper.
Resonate transparent batching enables you to take the most out of bulk operation againts other services. Saving money and time (by making a single http call) while running code that looks sequential. 

```py
# With batching

conn = Connection("benchmark.db", check_same_thread=False)

resonate = Scheduler(LocalPromiseStore(), processor_threads=1)

@dataclass
class InsertValue(Command):
    conn: Connection
    value: int


def _batch_handler(cmds: list[InsertValue]):
    first_value = cmds[0].value
    last_value = None
    for cmd in cmds:
        conn.execute("INSERT INTO benchmark (value) VALUES (?)", (cmd.value,))
        last_value = cmd.value
    conn.commit()
    print(f"Values from {first_value} to {last_value} have been inserted to database.")


def create_user_batching(ctx: Context, v: int):
    p = yield ctx.lfi(InsertValue(conn, v))
    yield p

# register top level function.
resonate.register(create_user_batching, retry_policy=never())

# register batch handler
resonate.register_command_handler(InsertValue, _batch_handler, retry_policy=never())

```

```bash
rye run batching --batch --values 1_000
# Inserting 1,000 values took 0.070747 seconds with batching=True
rye run batching --batch --values 10_000
# Inserting 10,000 values took 0.854411 seconds with batching=True
rye run batching --batch --values 100_000
# Inserting 100,000 values took 10.883661 seconds with batching=True
```

```py
# Without batching

conn = Connection("benchmark.db", check_same_thread=False)

resonate = Scheduler(LocalPromiseStore(), processor_threads=1)

def _create_user(ctx: Context, value: int):
    conn.execute("INSERT INTO benchmark (value) VALUES (?)", (value,))
    conn.commit()
    print(f"Value {value} has been inserted to database")


def create_user_sequentially(ctx: Context, v: int):
    p = yield ctx.lfi(_create_user, v).with_options(retry_policy=never())
    yield p

# register top level function.
resonate.register(create_user_sequentially, retry_policy=never())

```

```bash
rye run batching --no-batch --values 1_000
# Inserting 1,000 values took 0.273321 seconds with batching=False
rye run batching --no-batch --values 10_000
# Inserting 10,000 values took 9.444141 seconds with batching=False
rye run batching --no-batch --values 100_000
# Inserting 100,000 values took 33.263223 seconds with batching=False
```