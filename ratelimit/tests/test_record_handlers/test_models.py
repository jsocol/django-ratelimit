from django.apps.registry import apps
from django.db import connection
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.state import ProjectState
from django.test import TestCase


class MigrationsTestCase(TestCase):
    def test_missing_migrations(self):
        executor = MigrationExecutor(connection)
        autodetector = MigrationAutodetector(
            executor.loader.project_state(), ProjectState.from_apps(apps)
        )

        changes = autodetector.changes(graph=executor.loader.graph)

        self.assertEqual({}, changes)
