from backend.dag_engine.parser import DAGParser


def main():
    parser = DAGParser()

    dags = parser.parse()

    print(f"Loaded {len(dags)} DAG(s)")

    for dag_id, dag in dags.items():

        print(f"\nDAG: {dag_id}")
        print(f"Schedule: {dag.schedule}")
        print(f"Tasks: {len(dag.tasks)}")

        for task in dag.tasks.values():
            print(f"  - {task.task_id}")


if __name__ == "__main__":
    main()
