"""Operators: the building blocks a DAG author uses to make a task *do* work.

    from backend.dag_engine.operators import (
        BashOperator, PythonOperator, SSHOperator, RsyncOperator,
    )
"""

from .base import BaseOperator
from .bash import BashOperator
from .python import PythonOperator
from .rsync import RsyncOperator
from .ssh import SSHOperator

__all__ = [
    "BaseOperator",
    "BashOperator",
    "PythonOperator",
    "SSHOperator",
    "RsyncOperator",
]
