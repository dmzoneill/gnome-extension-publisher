# comment
import json
import os
import zipfile
from shutil import which
from typing import Optional

import requests
import typer


def create_zip_file(file_path, target_dir):
    directories_to_ignore = [".git", ".github", "dist"]
    zipobj = zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED)
    rootlen = len(target_dir) + 1
    for base, dirs, files in os.walk(target_dir):
        if any(ignore_directory in base for ignore_directory in directories_to_ignore):
            continue

        for file in files:
            fn = os.path.join(base, file)
            zipobj.write(fn, fn[rootlen:])


def glib_compile_schemas(directory: str):
    schemas_directory = os.path.join(directory, "schemas")

    if which("glib-compile-schemas") is None:
        typer.echo("Can't find glib-compile-schemas command.")

    if not os.path.isdir(schemas_directory):
        typer.echo("Can't find a schemas directory.")

    os.popen(f"glib-compile-schemas {schemas_directory}")


def verify_extension_directory(path: str):
    required_files = ["extension.js", "metadata.json"]
    valid = True
    for f in required_files:
        if not os.path.isfile(os.path.join(path, f)):
            valid = False
            break
    return valid


def verify_extension_archive(path: str):
    with zipfile.ZipFile(path) as zf:
        if "extension.js" in zf.namelist() and "metadata.json" in zf.namelist():
            return True
        return False


def get_extension_metadata(path: str):
    metadata_file = os.path.join(path, "metadata.json")
    return json.load(open(metadata_file))


def upload(username: Optional[str], password: Optional[str], zipfile: str):
    client = requests.Session()
    client.headers.update({"referer": "https://extensions.gnome.org/accounts/login/"})
    client.get("https://extensions.gnome.org/accounts/login/")
    csrftoken = client.cookies["csrftoken"]
    login_response = client.post(
        "https://extensions.gnome.org/accounts/login/",
        data={
            "csrfmiddlewaretoken": csrftoken,
            "username": username,
            "password": password,
            "next": "/",
        },
    )

    if (
        "Please enter a correct username and password. Note that both fields may be case-sensitive."
        in login_response.text
    ):
        typer.echo("Wrong username or password for extensions.gnome.org")
        return

    client.get("https://extensions.gnome.org/upload/")
    csrftoken = client.cookies["csrftoken"]

    upload_response = client.post(
        "https://extensions.gnome.org/upload/",
        files={"source": open(zipfile, "rb")},
        data={
            "tos_compliant": True,
            "gplv2_compliant": True,
            "csrfmiddlewaretoken": csrftoken,
        },
    )

    if upload_response.status_code == requests.codes.ok:
        return True
    else:
        typer.echo(upload_response.text)
        return False
