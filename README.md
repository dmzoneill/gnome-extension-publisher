# Gnome Extension Publisher
Tool to upload Gnome-Shell extensions to [extensions.gnome.org](https://extensions.gnome.org).

![Build Status](https://github.com/dmzoneill/gnome-extension-publisher/actions/workflows/main.yml/badge.svg)

This is a fork of 'gnome-extension-uploader' which seems to be abandoned.  
You can find this python module on [https://pypi.org/project/gnome-extension-publisher/](https://pypi.org/project/gnome-extension-publisher/)


## Install
```console
pip install gnome-extension-publisher
```

## How to use
```console
gep build # runs glib-compile-schemas and builds the zip file
gep publish --username <YOUR_EXTENSIONS_GNOME_ORG_USERNAME> --password <YOUR_EXTENSIONS_GNOME_ORG_PASSWORD>
gep --help # for help :)
```

You can also provide your username and password via environment variables (GEP_USERNAME, GEP_PASSWORD).


## Support
Feel free to submit a pull request
