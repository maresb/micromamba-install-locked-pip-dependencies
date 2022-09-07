# micromamba-install-locked-pip-dependencies

[![PyPI - Version](https://img.shields.io/pypi/v/micromamba-install-locked-pip-dependencies.svg)](https://pypi.org/project/micromamba-install-locked-pip-dependencies)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/micromamba-install-locked-pip-dependencies.svg)](https://pypi.org/project/micromamba-install-locked-pip-dependencies)

-----

**Table of Contents**

- [micromamba-install-locked-pip-dependencies](#micromamba-install-locked-pip-dependencies)
  - [Links](#links)
  - [Introduction](#introduction)
  - [Usage](#usage)
  - [Installation](#installation)
  - [Without installation](#without-installation)
  - [License](#license)

## Links

- [GitLab](https://gitlab.com/bmares/micromamba-install-locked-pip-dependencies)
- [GitHub](https://github.com/maresb/micromamba-install-locked-pip-dependencies)
- [PyPI](https://pypi.org/project/micromamba-install-locked-pip-dependencies)

## Introduction

Micromamba currently [ignores](https://github.com/mamba-org/mamba/issues/1900) pip dependencies in new-style lockfiles. This script parses the lockfile and installs those dependencies.

This script has no dependencies other than Python 3.6+. (It implements its own crude YAML parser.)

## Usage

To install `main`-category dependencies from `conda-lock.yml`, simply run `micromamba-install-locked-pip-dependencies`.

For more advanced usage:

```console
$ micromamba-install-locked-pip-dependencies --help
usage: micromamba-install-locked-pip-dependencies [-h] [-f LOCKFILE]
                                                  [-c CATEGORY] [--dry-run]
                                                  [--uninstall]
                                                  [--pip-location PIP_LOCATION]

Install pip dependencies from new-style lockfiles

optional arguments:
  -h, --help            show this help message and exit
  -f LOCKFILE, --lockfile LOCKFILE
                        Filename of the lockfile
  -c CATEGORY, --category CATEGORY
                        Category to install (default 'main')
  --dry-run             Do not actually install anything
  --uninstall           Do not actually install anything
  --pip-location PIP_LOCATION
                        Location of pip executable
```

## Installation

```console
pip install micromamba-install-locked-pip-dependencies
```

## Without installation

```console
curl https://raw.githubusercontent.com/maresb/micromamba-install-locked-pip-dependencies/master/micromamba_install_locked_pip_dependencies/cli.py | python - --help
```

## License

`micromamba-install-locked-pip-dependencies` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
