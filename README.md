# seeq-add-on-spc-accelerator

## Development

### Updating Documentation
Documentation is written in markdown, built using Sphinx, and hosted on GitHub Pages. 

To update the documentation, make changes to the markdown files in the `docs/source` directory. When a PR is merged into the `main` branch, the documentation will be automatically built and deployed to GitHub Pages.

### Building Documentation Locally
#### Pre-requisites
Sphinx, Sphinx-rtd-theme, and myst_parser are required to build the documentation locally. Install them using pip:
```bash
pip install sphinx sphinx-rtd-theme myst_parser
```
#### Building
To build the documentation locally, navigate to the `docs` directory and run the following command:
```bash
make html
```

Test
