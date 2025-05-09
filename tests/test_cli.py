# test_cli.py

import os
import tempfile
import unittest
from unittest.mock import patch

# isort: off
from gnome_extension_publisher import cli
from typer.testing import CliRunner

# isort: on

runner = CliRunner()


class TestGnomeExtensionPublisherCLI(unittest.TestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "testpass"

    @patch("gnome_extension_publisher.cli.upload", return_value=True)
    @patch("gnome_extension_publisher.cli.verify_extension_archive", return_value=True)
    def test_publisharchive_success(self, mock_verify, mock_upload):
        with tempfile.NamedTemporaryFile(suffix=".zip") as f:
            result = runner.invoke(
                cli.app,
                [
                    "publisharchive",
                    "--file",
                    f.name,
                    "--username",
                    self.username,
                    "--password",
                    self.password,
                ],
            )
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Uploaded successfully", result.stdout)

    @patch("gnome_extension_publisher.cli.verify_extension_archive", return_value=False)
    def test_publisharchive_invalid(self, _):
        with tempfile.NamedTemporaryFile(suffix=".zip") as f:
            result = runner.invoke(
                cli.app,
                [
                    "publisharchive",
                    "--file",
                    f.name,
                    "--username",
                    self.username,
                    "--password",
                    self.password,
                ],
            )
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("Not a valid extension archive", result.stdout)

    @patch("gnome_extension_publisher.cli.upload", return_value=False)
    @patch("gnome_extension_publisher.cli.verify_extension_archive", return_value=True)
    def test_publisharchive_upload_fail(self, *_):
        with tempfile.NamedTemporaryFile(suffix=".zip") as f:
            result = runner.invoke(
                cli.app,
                [
                    "publisharchive",
                    "--file",
                    f.name,
                    "--username",
                    self.username,
                    "--password",
                    self.password,
                ],
            )
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("Upload failed", result.stdout)

    @patch(
        "gnome_extension_publisher.cli.verify_extension_directory", return_value=False
    )
    def test_publish_invalid_directory(self, _):
        result = runner.invoke(
            cli.app,
            [
                "publish",
                "--directory",
                "/fake/path",
                "--username",
                self.username,
                "--password",
                self.password,
            ],
        )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Not a valid extension directory", result.stdout)

    @patch(
        "gnome_extension_publisher.cli.get_extension_metadata",
        return_value={"uuid": "ext", "version": "1.0"},
    )
    @patch(
        "gnome_extension_publisher.cli.verify_extension_directory", return_value=True
    )
    @patch("gnome_extension_publisher.cli.upload", return_value=True)
    @patch("gnome_extension_publisher.cli.build")
    def test_publish_success(self, *_):
        with tempfile.TemporaryDirectory() as tmpdir:
            dist = os.path.join(tmpdir, "dist")
            os.makedirs(dist)
            zipfile = os.path.join(dist, "ext_v1.0.zip")
            with open(zipfile, "w") as f:
                f.write("data")

            result = runner.invoke(
                cli.app,
                [
                    "publish",
                    "--directory",
                    tmpdir,
                    "--username",
                    self.username,
                    "--password",
                    self.password,
                ],
            )
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Uploaded successfully", result.stdout)

    @patch(
        "gnome_extension_publisher.cli.verify_extension_directory", return_value=True
    )
    @patch(
        "gnome_extension_publisher.cli.get_extension_metadata",
        return_value={"uuid": "ext", "version": "1.0"},
    )
    def test_build_creates_zip(self, mock_meta, mock_verify):
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["extension.js", "metadata.json"]:
                with open(os.path.join(tmpdir, name), "w") as f:
                    f.write("content")

            result = runner.invoke(cli.app, ["build", "--directory", tmpdir])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Created extension zip file", result.stdout)


if __name__ == "__main__":
    unittest.main()
