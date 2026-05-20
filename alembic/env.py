import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

# project root path so to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.api.models import Base  # import all models via Base

# importing Base is enough - SQLAlchemy already knows all models
# that inherit from it (Tenant, User, Document, Chunk, Feedback)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# target_metadata tells Alembic: compare the current DB scema
# Against what's defined in our models, and generate the diff

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    Run migrations without a live DB connection (generates SQL only).

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    Run migrations against a live DB connection.

    """

    # Read DATABASE_URL from environment (K8s Secret) if available
    # Fall back to alembic.ini for local dev
    import os

    db_url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    # Alembic uses sync driver - replace asyncpg with psycopg2
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # NullPool: don't reuse connections during migrations
        # Migrations are one-shot - pooling adds no benefit here
    )
    """

    connectable = create_engine(db_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
