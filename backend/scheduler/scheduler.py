import time

from backend.dag_engine.parser import DAGParser


class Scheduler:

    def __init__(self):

        self.parser = DAGParser()

    def run(self):

        while True:

            dags = self.parser.parse()

            print(
                f"Loaded {len(dags)} DAG(s)"
            )

            time.sleep(10)


if __name__ == "__main__":

    Scheduler().run()
