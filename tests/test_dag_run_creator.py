from backend.scheduler.services.dag_run_creator import DagRunCreator

creator = DagRunCreator()

creator.create_run("sample_dag")
