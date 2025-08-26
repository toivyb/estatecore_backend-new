Alembic Safe Drops Patch (PowerShell)
=====================================

This patch makes your Alembic migrations tolerant of missing/renamed foreign-key
constraints and already-dropped tables. It replaces raw `op.drop_constraint(...)`
and `op.drop_table(...)` calls with helper functions that use `IF EXISTS` and `CASCADE`.

What it does
------------
- Adds helpers in migration files:
    def safe_drop_constraint(table: str, name: str):
        op.execute(f'ALTER TABLE "{table}" DROP CONSTRAINT IF EXISTS "{name}"')

    def safe_drop_table(name: str):
        op.execute(f'DROP TABLE IF EXISTS "{name}" CASCADE')

- Rewrites constraint drops like:
    op.drop_constraint('tenant_unit_id_fkey', 'tenant', type_='foreignkey')
  into:
    safe_drop_constraint('tenant', 'tenant_unit_id_fkey')

- Rewrites table drops like:
    op.drop_table('maintenance_request')
  into:
    safe_drop_table('maintenance_request')

How to use
----------
1) Extract this ZIP in the ROOT of your project (where the `migrations` folder lives).
2) Open PowerShell **in your project root** and run:

   Set-ExecutionPolicy -Scope Process Bypass -Force
   .\run_patches.ps1

   - The script will backup each modified migration as `<name>.bak` (once per run).
   - It only edits files in `migrations\versions` that contain drop-constraints or drop-tables.

3) Run your migration again:
   flask db upgrade

If you still hit a new FK name error
------------------------------------
Just re-run the patch script; it has a generic replacement that handles any
`op.drop_constraint(..., type_='foreignkey', ...)` pattern.
