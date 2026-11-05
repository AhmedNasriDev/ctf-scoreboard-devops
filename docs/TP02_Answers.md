# Lab 1 Sheet : answers

**Team :** Nasri ahmed, Ferg Mohamed El'Amine, Bouziane Chakib, Abdi Ahmed Raed

## Exercise 1:

- **(a).** The `pull_request` event triggers the pipeline before changes are merged into the `main` branch. This allows developers to verify that their proposed changes pass all CI checks and identify problems before integrating them into the main codebase.

- **(b).** Linting runs before tests because it is a fast and inexpensive check that detects code style issues and potential errors early. Running it first avoids wasting time executing tests on code that already has basic quality issues.

- **(c).** For a test suite that takes 20 minutes, this order becomes more important because linting can identify problems in a few seconds. This prevents unnecessary execution of long-running tests when the code already fails basic checks, saving CI resources and development time.

## Exercise 2:

- **(a).** The command used to skip Git pre-commit hooks is:
```bash
git -c core.hooksPath=/dev/null commit
```
Alternatively, when supported by the hook framework:

```bash
SKIP=gitleaks git commit
```

- **(b).** A repository administrator or someone with sufficient permissions to bypass branch protection can still merge changes containing a secret. Additionally, someone with permission to modify repository rules may weaken or disable the required status checks.

## Exercise 3:

- **(a).** The error line from the GitHub Actions log is:

```text
ModuleNotFoundError: No module named 'scoreboard'
```

- **(b).** The project uses a `src` layout, meaning the `scoreboard` package is located inside the `src/` directory rather than directly in the repository root. Without installing the project using `pip install -e .`, Python does not automatically recognize the package as an importable module. Consequently, the tests cannot import `scoreboard.app`.


- **(c).** The command that runs the installation automatically is:

```bash
pip install -e .
```

It is executed by the `install` step in the GitHub Actions workflow. The `-e` option installs the project in editable mode, making the package importable without copying its source files.
