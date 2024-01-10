[![DOI](https://zenodo.org/badge/656704397.svg)](https://zenodo.org/doi/10.5281/zenodo.10478973)

A simple static site generator for getting repo statistics.

# Setup

1. Fork the repo
2. Configure what data you want to harvest
   1. Generate a PAT token for your organization with read access to organization repositories and read access to repo issues and metadata
   2. Add the PAT token as a secret to your forked repo under a sensible name (e.g. `UU_BIO_PAT`)
   3. Update `.github/workflows/pages.yaml` to reference your token in the environment (find the build step and update it accordingly)
   4. Update the `config.toml` with your github organization name and the name of the pat token (in this example that would be `UU_BIO_PAT`)
3. Push the changes
4. Find your page under deployments
