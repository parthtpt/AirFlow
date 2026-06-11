from backend.dag_engine.parser import DAGParser
from backend.dag_engine.validator import DAGValidator

parser = DAGParser()

dags = parser.parse()

validator = DAGValidator()

for dag in dags.values():
    validator.validate(dag)

print("All DAGs valid")
