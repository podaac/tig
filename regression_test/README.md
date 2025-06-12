# Regression Testing for TIG Collections

This repository provides regression tests for the Forge-py package across all supported collections.

## Setup Instructions

1. **Clone the Repository**

   ```bash
   git clone https://github.com/podaac/tig
   cd forge-py
   ```

2. **Install Dependencies**

   This project uses [Poetry](https://python-poetry.org/) for dependency management.

   ```bash
   poetry install
   ```

3. **Activate the Poetry Shell**

   ```bash
   poetry shell

   or

   poetry env activate
   ```

4. **Set Earthdata Login Credentials**

   The tests require NASA Earthdata Login credentials. Set your username and password as environment variables:

   ```bash
   export CMR_USER="your_earthdata_username"
   export CMR_PASS="your_earthdata_password"
   ```

   > **Note:** These credentials are required for token authentication with NASA CMR.

5. **Run Regression Tests**

   Execute the regression test suite with:

   ```bash
   pytest -s -v regression.py
   ```

   This will:
   - Download all relevant configuration files from the configuration GitHub repo.
   - Dowonload palettes
   - For each collection, download a sample granule.
   - Generate images using TIG.
   - Output images into folder with granule and configs.
