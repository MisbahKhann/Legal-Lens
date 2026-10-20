"""
Automated migration tests for Alembic schema management.
Verifies upgrade head on clean DB, downgrade base, re-upgrade, and alembic check drift.
"""

import os
import tempfile
import pytest
from alembic.config import Config
from alembic import command


@pytest.fixture
def temp_alembic_config():
    """Provides an isolated temporary database for migration verification."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_mig.db").replace("\\", "/")
    backend_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    ini_path = os.path.join(backend_dir, "alembic.ini")

    config = Config(ini_path)
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    yield config


def test_alembic_lifecycle_upgrade_downgrade_and_drift(temp_alembic_config):
    """
    1. Upgrade head on clean DB.
    2. Alembic check to ensure models match migration schema with zero drift.
    3. Downgrade to base.
    4. Re-upgrade to head.
    """
    # 1. Upgrade to head
    command.upgrade(temp_alembic_config, "head")

    # 2. Check drift (raises CommandError if drift is detected)
    command.check(temp_alembic_config)

    # 3. Downgrade to base
    command.downgrade(temp_alembic_config, "base")

    # 4. Re-upgrade to head
    command.upgrade(temp_alembic_config, "head")
