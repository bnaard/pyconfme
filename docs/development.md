# Development

## Build Tool

The project's dependencies, build-chain and deployment to [PyPI](https://pypi.org/) is managed with [Python Poetry](https://python-poetry.org/).

- Main project information is manged in file `pyproject.toml`
- Dependencies to the production are added by `poetry add <pypi-package-name>` or removed by `poetry remove <pypi-package-name>`
- Dependencies only needed for development are added by `poetry add --dev <pypi-package-name>` or removed by `poetry remove --dev <pypi-package-name>`

In case of problems, it usually helps to delete the automatically generated `poetry.lock`-file and to run `poetry install` to reinstall all dependencies with recalculation of dependency tree.

## Versioning

Versioning is managed also by [Python Poetry](https://python-poetry.org/) using [SemVer](https://semver.org/lang/de/):

- Major version update: `poetry version major` (for large releases with completely new feature sets and/or breakting API)
- Minor version update: `poetry version minor` (for minor feature additions and/or non-breaking api changes)
- Patch version update: `poetry version patch` (for bugfixes, minor documentation updates)

Though versioning is managed with [Python Poetry](https://python-poetry.org/), the version definition needs manual update in the following steps and locations:

1. Major/Minor/Patch version update using one of the above `poetry version` commands
2. Manual update of `pycmdlineapp_groundwork/__init__.py:__version__`
3. Manual update of command for rebuilding the documentation (only for preview locally, production versioning is handled in Github actions). See section _Documentation_ below.

## Documentation

Documentation is build using [mkdocs](https://www.mkdocs.org/) static page generator with several plugins which allow versioning, integration of docstring comments and deploying to [Github pages](https://docs.github.com/en/github/working-with-github-pages/getting-started-with-github-pages). The advantages of this approach are greater flexibility in page setup and design, integration of docstring comments and examples and simple local preview.

The main plugins are:

- For great design, search and navigation: [mkdocs-material](https://squidfunk.github.io/mkdocs-material/getting-started/)
- For integration of docstring comments: [mkdoc-strings](https://github.com/mkdocstrings/mkdocstrings)
- For versioning: [mike](https://github.com/jimporter/mike)

The Github action described in `.github/workflows/docs.yml` is based on [GitHub Actions for GitHub Pages](https://github.com/peaceiris/actions-gh-pages), which builds and deploys mkdoc page structures and takes care that Github is serving those _as is_ instead of using Jekyll.

All productive documentation is hosted on `gh-pages`-branch of this repository. This is automatically managed and overwritten by the `mkdoc`-tools mentioned above. So, do not edit manually the `gh-pages`-branch as all your changes will be overwritten and lost on next documentation auto-build+deploy.

In the Github actions, the latest version is retrieved using [get-latest-tag](https://github.com/marketplace/actions/actions-ecosystem-action-get-latest-tag) to build the latest documentation.

While documentation updates including documentation versions on Github are automatically done based on latest tag information (see `.github/workflows/Docs.yml`), you need to run the following to locally build and serve the versioned documentation for preview on [https://localhost:8000](https://localhost:8000):

```bash
mike deploy --update-aliases 0.1.0 latest   # replace 0.1.0 manually with the current version from pycmdlineapp_groundwork/__init__.py
mike set-default latest
mike serve
```

Note that you have to run both commands to get a proper redirect to the latest documentation on [https://localhost:8000](https://localhost:8000). Refer to [mkdocs-material documentation](https://squidfunk.github.io/mkdocs-material/setup/setting-up-versioning/) and to [mike documentation](https://github.com/jimporter/mike#usage) for details.
