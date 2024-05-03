# Seeq SPC Accelerator
![Deploy & Test](https://github.com/seeq12/seeq-add-on-spc-accelerator/actions/workflows/ci.yml/badge.svg)
![Nightly Tests](https://github.com/seeq12/seeq-add-on-spc-accelerator/actions/workflows/nightly.yml/badge.svg)

## Development

### Requirements

The following base requirements are needed to build and deploy:

* Python 3: https://www.python.org/downloads/
* A running Seeq server with an admin credentials


### Bootstrap

Launch a new terminal (e.g. in VS Code)
Execute the following command in a Bash (or Bash-like) terminal to setup your environment. If you're on Windows, I highly suggest at least downloading [Git Bash](https://git-scm.com/downloads) and using that to execute.
```
bash ao bootstrap --url http://your.running.seeq.server --username your.username@seeq.com --password your.password [--python custom_python]
```
The `username` and `password` are the credentials of an admin user on your Seeq server. The `url` is the url of your Seeq server.
The optional `python` argument is a place to provide an alternative python to use for bootstrapping if `python` is not on your path

The bootstrap step only needs to be done once. It will create a `.bootstrap.json` file in the parent of the repo.
It will create a Python virtual environment for the build system as well as the back-end and install the required Python packages.


***
### Deploy
Run the following command in a terminal from the root of the repository to deploy the add-on to your Seeq server. It requires that Add-on Manager be installed on your Seeq server.
```
bash ao deploy [--clean]
```
The optional `--clean` argument tries to uninstall the add-on from your Seeq server before reinstalling it.
The optional `--suffix` argument will apply a suffix to all add-on identifiers when deploying. This is useful for deploying multiple versions of the same add-on to the same server.

***
### Package
Run the following command in a terminal from the root of the repository to package the add-on to create a `.addon` file.
```
bash ao package
```
This command will issue a build of the add-on and then package the Add-on Manager.
The version is read from the `addon.json` file.


***
### Watch

Although deploying with the `--clean` option is reliable and works well for testing code changes during development, it can be faster and easier to use watch.
Run the following command in a terminal from the root of the repository to watch for changes and deploy them to your Seeq server.
```
bash ao watch
```
If you want to watch only a portion of the add-on, you can use the `--dir` argument with the value of the path to the add-on element you want to watch:
```
python ao.py watch --dir add-on-tool
```
The `watch` command will not exit until you press `Ctrl+C` in the terminal.

The `watch` command also accepts optional `--url`, `--username` and `--password`  arguments to specify the Seeq server to deploy to and the credentials to use.
```
python ao.py watch --url http://your.running.seeq.server --username your.username@seeq --password your.password
```

The watch command assumes that the add-on has been deployed to your Seeq server before.
Make sure that it's been deployed before using watch.

***
### Test
Run the following command in a terminal from the root of the repository to run the Add-on Manager tests.
```
bash ao test
```

## Documentation

### Updating Documentation
Documentation is written in markdown, built using Sphinx, and hosted on GitHub Pages. 

To update the documentation, make changes to the markdown files in the `docs/source` directory. When a PR is merged into the `main` branch, the documentation will be automatically built and deployed to GitHub Pages.

To add a new page to the documentation, add a new markdown file to the `docs/source` directory and include it in the `index.rst` file.

To add a new image to the documentation, add the image to the `docs/source/_static` directory and reference it in the markdown file.

To add this functionality to a new project:
- Copy the `docs` directory from this project to the new project and update the `conf.py` file to include the new project name.
- Copy the .github/workflows/pages.yml file to the new project to enable the GitHub Pages deployment. 
- Follow [these instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site#publishing-with-a-custom-github-actions-workflow) to enable publishing to GitHub Pages via a workflow. You don't have to setup the workflow, just select 'GitHub Action's as the source.

### Building Documentation Locally

If you want to test changes to the documentation before merging a PR, you can build the documentation locally.

Sphinx, Sphinx-rtd-theme, and myst_parser are required to build the documentation locally. Install them using pip:
```bash
pip install sphinx sphinx-rtd-theme myst_parser
```

To build the documentation locally, navigate to the `docs` directory and run the following command:
```bash
make html
```
