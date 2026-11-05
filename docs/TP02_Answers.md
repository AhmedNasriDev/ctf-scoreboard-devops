# Lab 1 Sheet : answers

**Team :** Nasri ahmed, Ferg Mohamed El'Amine, Bouziane Chakib, Abdi Ahmed Raed

## Exercise 1:

![[TP02_screenshots/part_a.png]]

![[TP02_screenshots/part_a_pipeline.png]]


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

![[TP02_screenshots/part_c3.jpg]]

![[TP02_screenshots/part_c4.jpg]]


![[TP02_screenshots/part_c2.jpg]]


![[TP02_screenshots/part_c5.jpg]]


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

## Exercise 4:

![[TP02_screenshots/part_d1.png]]

![[TP02_screenshots/part_d_failed.png]]

![[TP02_screenshots/part_d2.png]]

![[TP02_screenshots/part_d3.png]]



| Defect     | Gate that failed     | Name in the log                                              | One-line cause                                                                          |
| ---------- | -------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| Test 1     | Tests<br>(Exception) | `test_submitting_for_an_unknown_team_is_not_found`           | Missing handling for an unknown team causes an AttributeError when accessing `team.id`. |
| Test 2     | Tests<br>(Assertion) | `test_last_solve_time_is_the_most_recent_not_the_last_added` | The function returns the last inserted solve instead of the most recent timestamp.      |
| Credential | Secret scan          | 2 leaks detected<br>                                         | Gitleaks detected two potential secret exposures in the repository.                     |
| Dependency | Dependency audit     | `idna`                                                       | Vulnerable version 3.6 contains known security vulnerabilities.                         |
## Exercise 5:

![[TP02_screenshots/part_d5.png]]

![[TP02_screenshots/part_d6.png]]

![[TP02_screenshots/part_d_final.png]]
- **(a).** The vulnerable package `idna` is a **direct dependency** because it is explicitly listed in the project's `requirements.txt` file, pinned to version `3.6`. It is also required by other packages, such as `requests`, `httpx`, and `trio`.

- **(b).** I first inspected `requirements.txt` and confirmed that `idna==3.6` was explicitly declared as a project dependency. I then used `pipdeptree` to inspect the dependency relationships:

```bash
cat requirements.txt
pipdeptree -r -p idna
```

The first command confirmed that `idna` was directly declared, while the second displayed the packages that depend on it and their dependency relationships.

