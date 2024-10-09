from flask import Flask, jsonify
from resonate.scheduler import Scheduler
from resonate.context import Context
from resonate.storage import LocalPromiseStore

app = Flask(__name__)
resonate = Scheduler(LocalPromiseStore())


def baz(ctx: Context):
    return 1


def bar(ctx: Context):
    v = yield ctx.lfc(baz)
    return v + 1


def foo(ctx: Context):
    v = yield ctx.lfc(bar)
    return v + 1


@app.route("/")
def read_root():
    resonate.register(foo)
    v = resonate.run("foo", foo).result()
    return jsonify({"value": v})


def main() -> None:
    app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
