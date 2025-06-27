"""Database migration management for the Example Service."""

import asyncio
import logging
import os
import sys
from pathlib import Path

import click
from alembic import command, config
from alembic.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_alembic_config(database_url: str | None = None) -> Config:
    """Get Alembic configuration.
    
    Args:
        database_url: Optional database URL override
        
    Returns:
        Configured Alembic Config object
    """
    # Find the alembic.ini file in the persistence module
    current_dir = Path(__file__).parent
    root_dir = current_dir.parent.parent.parent.parent.parent.parent
    alembic_ini_path = root_dir / "{{ prefix-name }}-{{ suffix-name }}-persistence" / "alembic.ini"
    
    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"alembic.ini not found at {alembic_ini_path}")
    
    alembic_cfg = Config(str(alembic_ini_path))
    
    # Override database URL if provided
    if database_url:
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    
    return alembic_cfg


@click.group()
def cli() -> None:
    """Database migration management commands."""
    pass


@cli.command()
@click.option(
    "--database-url",
    "-d",
    envvar="DATABASE_URL",
    help="Database URL (can also be set via DATABASE_URL env var)"
)
def upgrade(database_url: str | None = None) -> None:
    """Run database migrations to upgrade to the latest version."""
    try:
        logger.info("Starting database migration upgrade...")
        alembic_cfg = get_alembic_config(database_url)
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migration upgrade completed successfully")
    except Exception as e:
        logger.error(f"Database migration upgrade failed: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--database-url",
    "-d",
    envvar="DATABASE_URL",
    help="Database URL (can also be set via DATABASE_URL env var)"
)
@click.option(
    "--revision",
    "-r",
    default="-1",
    help="Target revision for downgrade (default: -1 for one step back)"
)
def downgrade(database_url: str | None = None, revision: str = "-1") -> None:
    """Downgrade database to a previous migration."""
    try:
        logger.info(f"Starting database migration downgrade to revision: {revision}")
        alembic_cfg = get_alembic_config(database_url)
        command.downgrade(alembic_cfg, revision)
        logger.info("Database migration downgrade completed successfully")
    except Exception as e:
        logger.error(f"Database migration downgrade failed: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--database-url",
    "-d",
    envvar="DATABASE_URL",
    help="Database URL (can also be set via DATABASE_URL env var)"
)
def current(database_url: str | None = None) -> None:
    """Show current database revision."""
    try:
        alembic_cfg = get_alembic_config(database_url)
        command.current(alembic_cfg)
    except Exception as e:
        logger.error(f"Failed to get current revision: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--database-url",
    "-d",
    envvar="DATABASE_URL",
    help="Database URL (can also be set via DATABASE_URL env var)"
)
def history(database_url: str | None = None) -> None:
    """Show migration history."""
    try:
        alembic_cfg = get_alembic_config(database_url)
        command.history(alembic_cfg)
    except Exception as e:
        logger.error(f"Failed to get migration history: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--database-url",
    "-d",
    envvar="DATABASE_URL",
    help="Database URL (can also be set via DATABASE_URL env var)"
)
@click.option(
    "--message",
    "-m",
    required=True,
    help="Migration message"
)
@click.option(
    "--autogenerate/--no-autogenerate",
    default=True,
    help="Use autogenerate to detect schema changes"
)
def revision(
    database_url: str | None = None,
    message: str = "",
    autogenerate: bool = True
) -> None:
    """Create a new migration revision."""
    try:
        logger.info(f"Creating new migration: {message}")
        alembic_cfg = get_alembic_config(database_url)
        command.revision(alembic_cfg, message=message, autogenerate=autogenerate)
        logger.info("Migration revision created successfully")
    except Exception as e:
        logger.error(f"Failed to create migration revision: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--database-url",
    "-d",
    envvar="DATABASE_URL",
    help="Database URL (can also be set via DATABASE_URL env var)"
)
def stamp(database_url: str | None = None) -> None:
    """Stamp the database with the current head revision."""
    try:
        logger.info("Stamping database with head revision...")
        alembic_cfg = get_alembic_config(database_url)
        command.stamp(alembic_cfg, "head")
        logger.info("Database stamped successfully")
    except Exception as e:
        logger.error(f"Failed to stamp database: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for migration CLI."""
    cli()


if __name__ == "__main__":
    main()