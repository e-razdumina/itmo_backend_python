import sys
import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def add_project_root_to_path():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if project_root not in sys.path:
        sys.path.append(project_root)