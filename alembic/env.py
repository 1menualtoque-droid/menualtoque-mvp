import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context
from app.frameworks.settings import Settings

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Base from your models
from app.interfaces.persistence.models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """Get database URL from settings."""
    settings = Settings()
    url = settings.sync_database_url
    # Remove any query parameters
    return url.split("?")[0]


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()

    # Configure context with URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # compare_type=True,
        # include_schemas=True,
        # render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = get_url()

    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
        echo=True,
        connect_args={"options": "-c timezone=utc"},
    )

    with connectable.connect() as connection:
        # connection.execute(text("SET TIME ZONE 'UTC';"))
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # include_schemas=True,
            # compare_type=True,
            # render_as_batch=True,
            # implicit_returning=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
