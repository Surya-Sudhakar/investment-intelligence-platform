from pathlib import Path


def test_initial_migration_is_reversible() -> None:
    migration = (
        Path(__file__).parents[2]
        / "migrations"
        / "versions"
        / "20260724_0001_create_system_metadata.py"
    ).read_text(encoding="utf-8")
    assert 'op.create_table(\n        "system_metadata"' in migration
    assert 'op.drop_table("system_metadata")' in migration
