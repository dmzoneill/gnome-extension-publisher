#!/usr/bin/env python3
"""
CLI tool for building and publishing GNOME Shell extensions.

This script provides commands to:
- Upload an existing extension archive
- Build and upload from a source directory
- Build a zip archive from source

Environment variables:
- GEP_USERNAME: Username for extensions.gnome.org
- GEP_PASSWORD: Password for extensions.gnome.org
"""

# pylint: disable=broad-exception-caught

import logging
import os
import sys
from shutil import rmtree
from typing import Optional

import typer

# isort: off
from gnome_extension_publisher.utils import (
    create_zip_file,
    get_extension_metadata,
    glib_compile_schemas,
    upload,
    verify_extension_archive,
    verify_extension_directory,
)

# isort: on

app = typer.Typer()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def abort(message: str, exit_code: int = 1):
    """
    Log an error and exit the CLI with the given exit code.

    Args:
        message (str): Error message to display.
        exit_code (int): Exit code to return (default is 1).
    """
    logger.error("%s", message)
    typer.echo(message)
    raise typer.Exit(code=exit_code)


@app.command()
def publisharchive(
    file: str = typer.Option(os.getcwd(), help="Path to the extension zip file."),
    username: Optional[str] = typer.Option(
        None, envvar="GEP_USERNAME", help="Username for upload."
    ),
    password: Optional[str] = typer.Option(
        None, envvar="GEP_PASSWORD", help="Password for upload."
    ),
):
    """
    Upload a pre-built GNOME extension zip archive to extensions.gnome.org.

    Args:
        file (str): Path to the extension .zip file.
        username (Optional[str]): Login username (from env or option).
        password (Optional[str]): Login password (from env or option).
    """
    file = os.path.abspath(file)
    logger.debug("Resolved archive path: %s", file)

    if not os.path.isfile(file):
        abort(f"File does not exist: {file}")

    if not verify_extension_archive(file):
        abort("Not a valid extension archive.")

    if not username or not password:
        abort("Username and password are required for upload.")

    try:
        if upload(username, password, file):
            logger.info("Uploaded successfully.")
            typer.echo("Uploaded successfully.")
        else:
            abort("Upload failed.")
    except Exception as e:
        abort(f"Upload failed: {e}")


@app.command()
def publish(
    directory: str = typer.Option(os.getcwd(), help="Path to the extension directory."),
    compile_schemas: bool = typer.Option(False, help="Whether to compile schemas."),
    username: Optional[str] = typer.Option(None, envvar="GEP_USERNAME"),
    password: Optional[str] = typer.Option(None, envvar="GEP_PASSWORD"),
):
    """
    Build a GNOME extension from source and upload it.

    This performs schema compilation (if enabled), builds a zip file, then uploads it.

    Args:
        directory (str): Path to the extension source directory.
        compile_schemas (bool): Compile GSettings schemas if true.
        username (Optional[str]): Login username (from env or option).
        password (Optional[str]): Login password (from env or option).
    """
    directory = os.path.abspath(directory)
    logger.debug("Resolved directory path: %s", directory)

    if not verify_extension_directory(directory):
        abort("Not a valid extension directory.")

    metadata = get_extension_metadata(directory)

    logger.info("Building extension...")
    build(compile_schemas=compile_schemas, directory=directory)

    dist_directory = os.path.join(directory, "dist")
    zip_name = f"{metadata['uuid']}_v{metadata['version']}.zip"
    zip_path = os.path.join(dist_directory, zip_name)

    if not os.path.isfile(zip_path):
        abort(f"Expected zip file not found at: {zip_path}")

    if not username or not password:
        abort("Username and password are required for upload.")

    try:
        if upload(username, password, zip_path):
            logger.info("Uploaded successfully.")
            typer.echo("Uploaded successfully.")
        else:
            abort("Upload failed.")
    except Exception as e:
        abort(f"Upload failed: {e}")


@app.command()
def build(
    compile_schemas: bool = typer.Option(False, help="Whether to compile schemas."),
    directory: str = typer.Option(os.getcwd(), help="Path to the extension directory."),
):
    """
    Build a zip archive for a GNOME extension from source.

    This optionally compiles GSettings schemas, removes any existing 'dist' folder,
    and creates a zip archive named using the extension UUID and version.

    Args:
        compile_schemas (bool): Compile schemas before building.
        directory (str): Path to the extension source directory.
    """
    directory = os.path.abspath(directory)
    logger.debug("Resolved directory path: %s", directory)

    if not verify_extension_directory(directory):
        abort("Not a valid extension directory.")

    metadata = get_extension_metadata(directory)

    if compile_schemas:
        logger.info("Compiling GSettings schemas...")
        glib_compile_schemas(directory=directory)

    dist_directory = os.path.join(directory, "dist")
    if os.path.exists(dist_directory):
        logger.info("Cleaning existing 'dist' directory...")
        rmtree(dist_directory)
    os.mkdir(dist_directory)

    zip_path = os.path.join(
        dist_directory, f"{metadata['uuid']}_v{metadata['version']}.zip"
    )

    try:
        create_zip_file(zip_path, directory)
        logger.info("Created extension zip file: %s", zip_path)
        typer.echo(f"Created extension zip file: {zip_path}")
    except Exception as e:
        abort(f"Failed to create zip file: {e}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    app()
