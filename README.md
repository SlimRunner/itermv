# py_package_utils
Collection of python packages intended to be used as utilities in the terminal.

## Installation
Clone this repository and `cd` into the repo directory. Once inside run
```sh
pip3 install ./package_name/
```
If it's installed and you want to upgrade run
```sh
pip3 install ./package_name/ --upgrade
```

## Development
[Create and activate a virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/) and then run
```
pip3 install -r requirements-dev.txt
```
to install the required dependencies.

## Version Control
The project uses the [`bumpversion`](https://pypi.org/project/bumpversion/) packages see its documentation for more information. The projects under this repo will follow the `major.minor.patch` format.
