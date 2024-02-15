# seeq-add-on-spc-accelerator

## Development

### Updating Documentation
Documentation is written in markdown, built using Sphinx, and hosted on GitHub Pages. 

To update the documentation, make changes to the markdown files in the `docs/source` directory. When a PR is merged into the `main` branch, the documentation will be automatically built and deployed to GitHub Pages.

To add a new page to the documentation, add a new markdown file to the `docs/source` directory and include it in the `index.rst` file.

To add a new image to the documentation, add the image to the `docs/source/_static` directory and reference it in the markdown file.

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
