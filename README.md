# Tourney Backend

Esports tournament manager backend built with Flask.

## Database Migrations

This project uses Alembic for database migrations. To set up and run migrations:

### Initial Setup

If Alembic is not already initialized (it should be), run:

```bash
alembic init migrations
```

### Creating Migrations

To create a new migration based on model changes:

```bash
alembic revision --autogenerate -m "initial"
```

Replace `"initial"` with a descriptive message for your migration.

### Applying Migrations

To apply all pending migrations to the database:

```bash
alembic upgrade head
```

### Other Useful Commands

- View current migration status: `alembic current`
- View migration history: `alembic history`
- Rollback one migration: `alembic downgrade -1`
- Rollback to a specific revision: `alembic downgrade <revision_id>`
