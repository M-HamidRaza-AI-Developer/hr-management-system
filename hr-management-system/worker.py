"""RQ worker process — run alongside the web app to process background jobs
(emails, payroll generation). Start with: `python worker.py`."""
from redis import Redis
from rq import Worker, Queue

from app import create_app
from app.config import Config

listen = ["emails", "payroll", "default"]

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        conn = Redis.from_url(Config.REDIS_URL)
        queues = [Queue(name, connection=conn) for name in listen]
        worker = Worker(queues, connection=conn)
        worker.work()
