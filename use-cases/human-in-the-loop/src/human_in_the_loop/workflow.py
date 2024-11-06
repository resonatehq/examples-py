from resonate.storage.resonate_server import RemoteServer
from resonate.commands import CreateDurablePromiseReq
from resonate.scheduler import Scheduler
from resonate.context import Context


resonate = Scheduler(
    RemoteServer(url="http://localhost:8001"), logic_group="workflow-service"
)


def step3(ctx: Context, email: str):
    print(f"Next step for user {email} started.")


def workflow(ctx: Context, email: str):
    print(f"Workflow for user {email} started.")

    # Step 1 - send email with a link to confirm
    yield ctx.rfc(
        CreateDurablePromiseReq(
            promise_id=f"send-confirmation-email-{email}",
            data={"func": "send_email", "args": [email], "kwargs": {}},
            headers=None,
            tags={"resonate:invoke": "poll://email-service"},
        )
    )
    print(f"Email sent to {email}")

    # Step 2 - wait on human input
    confirmation = yield ctx.rfc(
        CreateDurablePromiseReq(
            promise_id=f"email-confirmed-{email}",
        )
    )
    print(f"Email address {email} confirmed: {confirmation}")

    # Step 3
    yield ctx.lfc(step3, email)

    # Add as many steps as needed

    return


resonate.register(name="workflow", func=workflow)


def main() -> None:
    print(f"Workflow service running")
    resonate.wait_forever()


if __name__ == "__main__":
    main()
