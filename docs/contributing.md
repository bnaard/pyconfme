# Contributing

We'd be happy to get your contribution to this project!

## Issues

Questions, feature requests and bug reports are all welcome as [discussions or issues](https://github.com/bnaard/pycmdlineapp-groundwork/issues).

## Security Policy

Please refer to our [Security Policy](https://github.com/bnaard/pycmdlineapp-groundwork/security/policy).

## Pull Requests

It's simple to get started and create a Pull Request. *pycmdlineapp_groundwork* has few dependencies, doesn't require compiling and tests don't need access to databases, etc.

*pycmdlineapp_groundwork* is released regularly so you should see your improvements release in a matter of weeks.

!!! note
    Unless your change is trivial (typo, docs tweak etc.), please create an issue to discuss the change before
    creating a pull request.

If you're looking for immediate possibilities to contribute, look out for the label ["help wanted"](https://github.com/github.com/bnaard/pycmdlineapp-groundwork/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22) in [issues]((https://github.com/bnaard/pycmdlineapp-groundwork/issues)).

### Prerequsites

- Mandatory: **python 3.8** or later installed
- Mandatory: [python-poetry](https://python-poetry.org/) installed
- Mandatory: **git** installed
- Optionally: You can work with [VS Code](https://code.visualstudio.com/) and [development containers](https://github.com/microsoft/vscode-dev-containers). See [Optional VS Code Setup description](#optional-vs-code-setup).

### Development setup

Please follow these steps to contribute:

Clone your fork and cd into the repo directory

```bash
git clone git clone https://github.com/bnaard/pycmdlineapp-groundwork.git
cd pycmdlineapp-groundwork
```

Set up a virtualenv and install dependencies:

```bash
poetry install
```

Checkout a new branch and make your changes:

```bash
git checkout -b my-new-feature-branch
```

Fix formatting and imports:

_planned_ : using black to enforce formatting and isort to fix imports
(https://github.com/ambv/black, https://github.com/timothycrosley/isort)


Run linting

_planned_ using flake8 as linter


Run tests and coverage

```bash
pytest --cov=pycmdlineapp-groundwork
```

Build and preview documentation

```bash
mike deploy
mike serve
```

... commit, push, and create your pull request

## Optional VS Code setup

tbd
