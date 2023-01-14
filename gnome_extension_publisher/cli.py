import os
from shutil import rmtree, which
from typing import List, Optional

import requests
import typer

from gnome_extension_publisher.utils import (create_zip_file, get_extension_metadata, glib_compile_schemas,
                                             verifiy_extension_directory, verify_extension_archive, upload)

app = typer.Typer()


@app.command()
def publisharchive(
    file: str = os.getcwd(),
    username: Optional[str] = os.environ.get("GEP_USERNAME", None),
    password: Optional[str] = os.environ.get("GEP_PASSWORD", None),
):
    directory = os.path.abspath(directory)

    if not verify_extension_archive(file):
        typer.echo("Not a valid extension archive.")
        return

    if upload(username, password, file):
        typer.echo("Uploaded.")


@app.command()
def publish(
    directory: str = os.getcwd(),
    compile_schemas: bool = False,
    ignore_directories: Optional[List[str]] = [],
    username: Optional[str] = os.environ.get("GEP_USERNAME", None),
    password: Optional[str] = os.environ.get("GEP_PASSWORD", None),
):
    if not verifiy_extension_directory(directory):
        typer.echo("Not a valid extension directory.")
        return

    metadata = get_extension_metadata(directory)

    build(
        compile_schemas=compile_schemas,
        directory=directory,
        ignore_directories=ignore_directories,
    )

    dist_directory = os.path.join(directory, "dist")

    full_zip_path = os.path.join(
        dist_directory, f"{metadata['uuid']}_v{metadata['version']}.zip"
    )

    if upload(username, password, full_zip_path):
        typer.echo("Uploaded.")


@app.command()
def build(
    compile_schemas: bool = False,
    directory: str = os.getcwd(),
    ignore_directories: Optional[List[str]] = [],
):
    directory = os.path.abspath(directory)

    if not verifiy_extension_directory(directory):
        typer.echo("Not a valid extension directory.")
        return

    metadata = get_extension_metadata(directory)
    if compile_schemas:
        glib_compile_schemas(directory=directory)

    dist_directory = os.path.join(directory, "dist")

    if os.path.isdir(dist_directory):
        rmtree(dist_directory)

    os.mkdir(dist_directory)

    full_zip_path = os.path.join(
        dist_directory, f"{metadata['uuid']}_v{metadata['version']}.zip"
    )
    create_zip_file(full_zip_path, directory,
                    ignore_directories=ignore_directories)
    typer.echo(f"Created extension zip file: {full_zip_path}")
