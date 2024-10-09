from django.http import JsonResponse
from resonate.scheduler import Scheduler
from resonate.context import Context
from resonate.storage import LocalPromiseStore


resonate = Scheduler(LocalPromiseStore())


def baz(ctx: Context):
    return 1


def bar(ctx: Context):
    v = yield ctx.lfc(baz)
    return v + 1


def foo(ctx: Context):
    v = yield ctx.lfc(bar)
    return v + 1


resonate.register(foo)


def read_root(request):
    v = resonate.run("foo", foo).result()
    return JsonResponse({"value": v})
