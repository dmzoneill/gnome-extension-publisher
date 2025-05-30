# -*- coding: utf-8 -*-
from setuptools import setup

packages = ["gnome_extension_publisher"]

package_data = {"": ["*"]}

install_requires = ["requests", "typer"]

entry_points = {"console_scripts": ["gep = gnome_extension_publisher.cli:app"]}

setup_kwargs = {
    "name": "gnome-extension-publisher",
    "version": "0.4.11",
    "description": "",
    "long_description": (
        "# Gnome Extension Publisher\nFork of abandoned gnome-extension-publisher, "
        "This tool to uploads Gnome-Shell extensions to [extensions.gnome.org](https://extensions.gnome.org).\n\n"
        "## Install\n```console\npip install gnome-extension-publisher\n```\n\n## How to use\n```console\ngep build"
        " # runs glib-compile-schemas and builds the zip file\n"
        "gep publish --username <YOUR_EXTENSIONS_GNOME_ORG_USERNAME> --password <YOUR_EXTENSIONS_GNOME_ORG_PASSWORD>\n"
        "gep --help # for help :)\n```\n\nYou can also provide your username and password via environment variables"
        " (GEP_USERNAME, GEP_PASSWORD).\n\n## Support\nFeel free to submit a pull request"
    ),
    "author": "David O Neill",
    "author_email": "dmz.oneill@gmail.com",
    "maintainer": None,
    "maintainer_email": None,
    "url": "https://github.com/dmzoneill/gnome-extension-publisher",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "entry_points": entry_points,
    "python_requires": ">=3.8,<4.0",
}


setup(**setup_kwargs)
