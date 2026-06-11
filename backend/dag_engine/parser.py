import importlib.util
from pathlib import Path

from backend.dag_engine.core.context import DAG_REGISTRY


class DAGParser:

    def __init__(
        self,
        dag_folder="backend/dags",
    ):
        self.dag_folder = Path(dag_folder)

    def load_file(self, file_path):

        module_name = file_path.stem

        spec = importlib.util.spec_from_file_location(
            module_name,
            file_path,
        )

        module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)

    def parse(self):

        DAG_REGISTRY.clear()

        for dag_file in self.dag_folder.glob("*.py"):
            self.load_file(dag_file)

        return DAG_REGISTRY
