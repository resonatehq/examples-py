from resonate.scheduler import Scheduler
from resonate.context import Context
from resonate.storage.resonate_server import RemoteServer

resonate = Scheduler(
    RemoteServer(url="http://localhost:8001"), logic_group="email-service"
)


def send_email(ctx: Context, email: str):
    print(f"Email sent to {email}")
    return


resonate.register(name="send_email", func=send_email)


def main():
    print("Email service started")
    resonate.wait_forever()


if __name__ == "__main__":
    main()
