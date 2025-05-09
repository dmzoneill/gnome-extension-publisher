#!/usr/bin/env python3
"""
Unit tests for gnome_extension_publisher.utils.

This suite verifies functionality including:
- Zip creation (excluding ignored directories)
- GSettings schema compilation
- Extension directory and archive verification
- Metadata loading from metadata.json
- Upload logic with mocked network requests
"""

import json
import logging
import os
import unittest
import zipfile
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from gnome_extension_publisher import utils

logging.basicConfig(level=logging.DEBUG)


class TestGnomeExtensionPublisherUtils(unittest.TestCase):
    """
    Test cases for the gnome_extension_publisher.utils module.
    """

    def test_create_zip_file_excludes_ignored_dirs(self):
        """
        Test that create_zip_file excludes .git and dist directories from the zip.
        """
        with TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".git"))
            os.makedirs(os.path.join(tmpdir, "dist"))
            os.makedirs(os.path.join(tmpdir, "src"))
            file_path = os.path.join(tmpdir, "src", "file.js")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("console.log('hello');")

            zip_output = os.path.join(tmpdir, "output.zip")
            utils.create_zip_file(zip_output, tmpdir)

            with zipfile.ZipFile(zip_output) as zf:
                self.assertIn("src/file.js", zf.namelist())
                self.assertNotIn(".git/", zf.namelist())

    def test_glib_compile_schemas_missing_tool(self):
        """
        Test glib_compile_schemas returns False if glib-compile-schemas is not found.
        """
        with patch("shutil.which", return_value=None):
            result = utils.glib_compile_schemas("/tmp")
            self.assertFalse(result)

    @patch(
        "gnome_extension_publisher.utils.which",
        return_value="/usr/bin/glib-compile-schemas",
    )
    @patch("gnome_extension_publisher.utils.subprocess.run")
    def test_glib_compile_schemas_success(self, mock_run, _):
        """
        Test glib_compile_schemas returns True if subprocess completes successfully.
        """
        with TemporaryDirectory() as tmp:
            schemas_dir = os.path.join(tmp, "schemas")
            os.makedirs(schemas_dir)

            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Compiled successfully"
            mock_run.return_value.stderr = ""

            result = utils.glib_compile_schemas(tmp)
            self.assertTrue(result)

    def test_verify_extension_directory_valid(self):
        """
        Test that verify_extension_directory returns True when required files are present.
        """
        with TemporaryDirectory() as tmp:
            for f in ["extension.js", "metadata.json"]:
                with open(os.path.join(tmp, f), "w", encoding="utf-8"):
                    pass
            self.assertTrue(utils.verify_extension_directory(tmp))

    def test_verify_extension_directory_invalid(self):
        """
        Test that verify_extension_directory returns False when required files are missing.
        """
        with TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "README.md"), "w", encoding="utf-8"):
                pass
            self.assertFalse(utils.verify_extension_directory(tmp))

    def test_verify_extension_archive_valid(self):
        """
        Test that verify_extension_archive returns True if archive contains required files.
        """
        with TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, "test.zip")
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("extension.js", "")
                zf.writestr("metadata.json", "")
            self.assertTrue(utils.verify_extension_archive(zip_path))

    def test_verify_extension_archive_invalid(self):
        """
        Test that verify_extension_archive returns False if archive is missing required files.
        """
        with TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, "bad.zip")
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("README.md", "")
            self.assertFalse(utils.verify_extension_archive(zip_path))

    def test_get_extension_metadata_success(self):
        """
        Test that get_extension_metadata correctly loads metadata.json.
        """
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "metadata.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"uuid": "test", "version": "1.0"}, f)
            data = utils.get_extension_metadata(tmp)
            self.assertEqual(data["uuid"], "test")

    def test_get_extension_metadata_missing(self):
        """
        Test that get_extension_metadata raises FileNotFoundError when file is missing.
        """
        with self.assertRaises(FileNotFoundError):
            utils.get_extension_metadata("/invalid/path")

    def test_upload_successful(self):
        """
        Test upload() returns True when session mock simulates successful upload.
        """
        session_mock = MagicMock()
        session_mock.cookies.get.side_effect = ["csrf1", "csrf2"]
        session_mock.get.return_value.text = "Login page"
        session_mock.post.return_value.text = "Success"
        session_mock.post.return_value.status_code = 200

        with TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, "upload.zip")
            with open(zip_path, "w", encoding="utf-8") as f:
                f.write("data")

            with patch("requests.Session", return_value=session_mock):
                result = utils.upload("user", "pass", zip_path)
                self.assertTrue(result)

    def test_upload_wrong_credentials(self):
        """
        Test upload() returns False when login response contains auth error.
        """
        session_mock = MagicMock()
        session_mock.cookies.get.side_effect = ["csrf1", "csrf2"]
        session_mock.get.return_value.text = "Login page"
        session_mock.post.return_value.text = (
            "Please enter a correct username and password"
        )
        session_mock.post.return_value.status_code = 200

        with TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, "upload.zip")
            with open(zip_path, "w", encoding="utf-8") as f:
                f.write("data")

            with patch("requests.Session", return_value=session_mock):
                result = utils.upload("baduser", "badpass", zip_path)
                self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
