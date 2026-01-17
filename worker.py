"""RQ Worker for batch PDF extraction → Excel files."""
import sys
import os
from redis import Redis
from rq import Worker, Queue

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    redis_conn = Redis(host='localhost', port=6379, db=0)
    q = Queue(connection=redis_conn)
    worker = Worker([q], connection=redis_conn)
    worker.work()
