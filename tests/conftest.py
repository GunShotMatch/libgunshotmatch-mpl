# stdlib
import sys

# 3rd party
import pytest
from libgunshotmatch.project import Project


@pytest.fixture(scope="session")
def hymax_project():
	return Project.from_file("tests/Eley Hymax.gsmp")


pytest_plugins = ("coincidence", )
