import time

from backend.dag_engine.parser import DAGParser
from backend.database.repositories.dag_repository import DAGRepository


class Scheduler:

    def __init__(self):

        self.parser = DAGParser()
        self.repo = DAGRepository()

    def sync_dags(self):

        dags = self.parser.parse()

        for dag in dags.values():

            self.repo.upsert(
                dag_id=dag.dag_id,
                schedule=dag.schedule,
            )

        print(
            f"Synced {len(dags)} DAG(s)"
        )

    def run(self):

        while True:

            self.sync_dags()

            time.sleep(10)


if __name__ == "__main__":

    Scheduler().run()
