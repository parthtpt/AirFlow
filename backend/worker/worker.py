"""AirFlow worker.

Skeleton process that will claim queued task runs and execute them. For now it
runs a heartbeat loop so the service has a real, restartable entrypoint that the
deployment can supervise. Fill in the polling/execution logic as the task
execution engine lands.
"""

import time


class Worker:

    POLL_INTERVAL = 5  # seconds

    def run(self):

        print("Worker started")

        while True:

            # TODO: claim queued task runs from the queue/DB and execute them.
            time.sleep(self.POLL_INTERVAL)


if __name__ == "__main__":

    Worker().run()
