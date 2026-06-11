class DAGValidationError(Exception):
    pass


class DAGValidator:

    def validate(self, dag):

        visited = set()
        stack = set()

        def dfs(task):

            if task.task_id in stack:
                raise DAGValidationError(
                    f"Cycle detected at {task.task_id}"
                )

            if task.task_id in visited:
                return

            stack.add(task.task_id)

            for child in task.downstream:
                dfs(child)

            stack.remove(task.task_id)
            visited.add(task.task_id)

        for task in dag.tasks.values():
            dfs(task)
