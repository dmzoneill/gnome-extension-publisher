"""
Helpers for GNOME extension publishing.
This module provides functions to:
- Create a zip file of the extension directory.
- Compile GSettings schemas.
- Verify the extension directory and archive.
- Load metadata from metadata.json.
- Upload the extension to extensions.gnome.org.
- Handle errors and logging.
- Use environment variables for credentials.
"""

import json
import logging
import os
import subprocess
import zipfile
from shutil import which
from typing import Optional

import requests

logger = logging.getLogger(__name__)


def create_zip_file(file_path: str, target_dir: str):
    """
    Create a zip file of the extension directory, excluding common ignored folders.
    """
    ignore_dirs = {".git", ".github", "dist"}
    with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        rootlen = len(target_dir) + 1
        for base, _, files in os.walk(target_dir):
            if any(ignored in base for ignored in ignore_dirs):
                logger.debug("Skipping ignored directory: %s", base)
                continue
            for file in files:
                full_path = os.path.join(base, file)
                arcname = full_path[rootlen:]
                zipf.write(full_path, arcname)
                logger.debug("Added to zip: %s", arcname)
    logger.info("Created zip file at: %s", file_path)


def glib_compile_schemas(directory: str):
    """
    Compile GSettings schemas inside the extension directory if present.
    """
    schemas_dir = os.path.join(directory, "schemas")

    if not which("glib-compile-schemas"):
        logger.error("glib-compile-schemas not found in PATH.")
        return False

    if not os.path.isdir(schemas_dir):
        logger.error("Schemas directory not found: %s", schemas_dir)
        return False

    logger.info("Compiling schemas in: %s", schemas_dir)
    result = subprocess.run(
        ["glib-compile-schemas", schemas_dir],
        capture_output=True,
        text=True,
        check=True,
    )

    if result.returncode != 0:
        logger.error("Schema compilation failed:\n%s", result.stderr)
        return False

    logger.debug("Schema compilation output:\n%s", result.stdout)
    return True


def verify_extension_directory(path: str) -> bool:
    """
    Verify that the extension directory contains required files.
    """
    required_files = ["extension.js", "metadata.json"]
    missing = [f for f in required_files if not os.path.isfile(os.path.join(path, f))]

    if missing:
        logger.warning("Missing files in extension directory: %s", missing)
        return False

    return True


def verify_extension_archive(path: str) -> bool:
    """
    Verify that the zip archive contains required extension files.
    """
    try:
        with zipfile.ZipFile(path) as zf:
            contents = set(zf.namelist())
            if {"extension.js", "metadata.json"}.issubset(contents):
                return True
            logger.warning("Archive missing required files. Contents: %s", contents)
    except zipfile.BadZipFile:
        logger.error("Invalid zip file: %s", path)
    return False


def get_extension_metadata(path: str) -> dict:
    """
    Parse metadata.json from the extension directory.
    """
    metadata_file = os.path.join(path, "metadata.json")
    if not os.path.exists(metadata_file):
        raise FileNotFoundError(f"metadata.json not found in: {path}")
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    logger.debug("Loaded metadata: %s", metadata)
    return metadata


def upload(username: Optional[str], password: Optional[str], zipfile_path: str) -> bool:
    """
    Upload the extension zip to extensions.gnome.org using the provided credentials.
    """
    logger.info("Starting upload to extensions.gnome.org...")

    if not os.path.isfile(zipfile_path):
        logger.error("Zip file does not exist: %s", zipfile_path)
        return False

    session = requests.Session()
    session.headers.update({"referer": "https://extensions.gnome.org/accounts/login/"})

    # Step 1: Get CSRF token
    response = session.get("https://extensions.gnome.org/accounts/login/")
    logger.debug("GET /accounts/login/ -> %s", response.status_code)

    csrftoken = session.cookies.get("csrftoken")
    if not csrftoken:
        logger.error("CSRF token not found in login response cookies.")
        return False
    logger.debug("Retrieved CSRF token: %s", csrftoken)

    # Step 2: Login
    login_response = session.post(
        "https://extensions.gnome.org/accounts/login/",
        data={
            "csrfmiddlewaretoken": csrftoken,
            "username": username,
            "password": password,
            "next": "/",
        },
    )
    logger.debug("POST /accounts/login/ -> %s", login_response.status_code)

    if "Please enter a correct username and password" in login_response.text:
        logger.error("Invalid credentials.")
        return False

    # Step 3: Refresh CSRF token from upload page
    response = session.get("https://extensions.gnome.org/upload/")
    logger.debug("GET /upload/ -> %s", response.status_code)

    csrftoken = session.cookies.get("csrftoken")
    if not csrftoken:
        logger.error("CSRF token not found after upload page GET.")
        return False
    logger.debug("New CSRF token: %s", csrftoken)

    # Step 4: Upload the file
    with open(zipfile_path, "rb") as f:
        upload_response = session.post(
            "https://extensions.gnome.org/upload/",
            files={"source": f},
            data={
                "tos_compliant": True,
                "gplv2_compliant": True,
                "csrfmiddlewaretoken": csrftoken,
            },
        )

    logger.debug("POST /upload/ -> %s", upload_response.status_code)

    if upload_response.status_code == 200:
        logger.info("Upload succeeded.")
        return True

    logger.error("Upload failed. Status: %s", upload_response.status_code)
    logger.debug("Response:\n%s", upload_response.text)
    return False
