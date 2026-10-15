# Student guide: every lab sheet, step by step

This guide is for you if the terminal, Linux, Git or software installation
is new to you. It tells you **exactly what to type and what to click**, in
order. It covers every part of lab sheets 1 to 6. It starts with the download
of the application. It does not give you the answers to the exercises. It
tells you where to look for them.

Keep the lab sheet open next to this guide. The guide follows the same parts
(Part A, Part B, …) and the same exercise numbers.

**Contents**

0. [How to read this guide](#0-how-to-read-this-guide)
1. [The terminal in ten minutes](#1-the-terminal-in-ten-minutes)
2. [One-time setup (before lab sheet 1)](#2-one-time-setup-before-lab-sheet-1)
3. [Get the application](#3-get-the-application)
4. [How to hand in your answers](#4-how-to-hand-in-your-answers)
5. [Lab sheet 1: Source control](#lab-sheet-1-source-control)
6. [Lab sheet 2: Continuous integration](#lab-sheet-2-continuous-integration)
7. [Lab sheet 3: Containers](#lab-sheet-3-containers)
8. [Lab sheet 4: Kubernetes](#lab-sheet-4-kubernetes)
9. [Lab sheet 5: GitOps, error budgets and a canary](#lab-sheet-5-gitops-error-budgets-and-a-canary)
10. [Lab sheet 6: Supply chain and measurement](#lab-sheet-6-supply-chain-and-measurement)
11. [When something goes wrong](#when-something-goes-wrong)
12. [Cheat sheet](#cheat-sheet)

---

## 0. How to read this guide

- A grey box is something you **type in the terminal**. Type (or copy) one
  line, press **Enter**, wait until it finishes, then the next line.
- Some boxes are **one block**. Copy and paste the whole block at once.
  This is true in two cases:
  - a command that continues on the next line (the line ends with `\`);
  - a block between `<<'EOF'` and `EOF`.
- Text between `<` and `>` must be **replaced** by your own value, *without*
  the `<` `>`. Example: `cd <folder>` becomes `cd devops-project`.
- A line that starts with `#` is a **comment**. The terminal ignores it. It
  is only there to explain. You can copy it or not.
- "Expected" means: what you should see. If you see something else, go to
  [When something goes wrong](#when-something-goes-wrong).
- Work as a team. One person types on one computer (the "driver"). The
  others read the guide and check. Change the driver at each part.

---

## 1. The terminal in ten minutes

**Open a terminal.** On Ubuntu press **Ctrl + Alt + T**. A window opens with a
line ending in `$`. That line is the *prompt*: the terminal waits for you.

**Copy and paste in the terminal** is different from other programs:

| Action | Keys |
|---|---|
| Paste into the terminal | **Ctrl + Shift + V** (or right click → Paste) |
| Copy from the terminal | select with the mouse, then **Ctrl + Shift + C** |
| Stop the running command | **Ctrl + C** |
| Repeat an earlier command | **↑** (up arrow), then Enter |
| Complete a file or folder name | type the start, press **Tab** |
| Clear the screen | type `clear` |

**Where am I, what is here, go somewhere:**

```bash
pwd                 # print the folder you are in
ls                  # list what is in it
ls -a               # list everything, including hidden files (names starting with .)
cd devops-project   # go into a folder
cd ..               # go up one folder
cd ~                # go to your home folder (~ means home)
mkdir notes         # create a folder
cat README.md       # print a file on the screen
```

**Edit a file with `nano`** (a simple editor inside the terminal):

```bash
nano docs/TP1_answers.md
```

- Type normally. Move with the arrow keys.
- **Ctrl + O** then **Enter**: save. **Ctrl + X**: quit.
- **Ctrl + W**: search for a word. **Ctrl + K**: cut (delete) the whole line.
- To paste text into nano: **Ctrl + Shift + V**.
- The bottom two lines of nano list the shortcuts (`^` means Ctrl).

**Passwords.** Commands starting with `sudo` install or change system things
and ask for **your computer password**. While you type it, **nothing appears
on the screen**. This is normal. Type it and press Enter.

**Exit codes.** Many commands in the lab sheets end with
`; echo "exit=$?"`. It prints the *exit code* of the command before it.
`exit=0` means success, or "nothing found". Any other number means failure,
or "something found". The lab sheets ask you to write down these numbers.

**A screen full of text with `:` at the bottom** (after `git log`, for
example) is a *pager*. Use the arrows to move up and down. Press **q** to
leave.

---

## 2. One-time setup (before lab sheet 1)

Do this once, at home or at the start of the first session. It takes about
20 minutes. All the commands below are for **Ubuntu 24.04** (the lab
computers).

> **Windows?** Install Ubuntu inside Windows: open *PowerShell as
> administrator*, run `wsl --install -d Ubuntu-24.04`, restart, open the
> *Ubuntu* app, and follow this guide in that window.
> **Mac?** Most commands work in the *Terminal* app, but the installation
> commands are different. Use the lab computers, or ask your instructor.

### 2.1 Basic tools

```bash
sudo apt update
sudo apt install -y git make curl unzip jq python3 python3-venv python3-pip
python3 --version          # Expected: Python 3.12.x (3.11 or later is fine)
git --version              # Expected: git version 2.43 or later
```

### 2.2 A folder for programs you install yourself

Some tools are one single file that you download. They go in
`~/.local/bin`. Tell the terminal to look there:

```bash
mkdir -p ~/.local/bin
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 2.3 gitleaks (secret scanner, lab sheets 1 and 2)

```bash
cd /tmp
curl -sSL -o gitleaks.tar.gz \
  https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz
tar -xzf gitleaks.tar.gz gitleaks
mv gitleaks ~/.local/bin/
cd ~
gitleaks version           # Expected: 8.30.1
```

### 2.4 GitHub CLI `gh` (logging in to GitHub, lab sheets 1 to 6)

```bash
cd /tmp
curl -sSL -o gh.tar.gz \
  https://github.com/cli/cli/releases/download/v2.102.0/gh_2.102.0_linux_amd64.tar.gz
tar -xzf gh.tar.gz
mv gh_2.102.0_linux_amd64/bin/gh ~/.local/bin/
cd ~
gh --version               # Expected: gh version 2.102.0
```

### 2.5 Git identity and GitHub login

Create a free account on <https://github.com> if you do not have one. Then:

```bash
git config --global user.name  "Firstname Lastname"
git config --global user.email "you@univ-oran.dz"      # the email of your GitHub account is best
git config --global init.defaultBranch main
git config --global core.editor nano
gh auth login
```

`gh auth login` asks questions. Answer with the arrow keys and Enter:
**GitHub.com** → **HTTPS** → **Yes** (authenticate Git) → **Login with a web
browser**. It shows a code like `ABCD-1234`. Press Enter. A browser opens.
Paste the code and click *Authorize*. Then, in the terminal:

```bash
gh auth setup-git          # git push will now use this login (no password)
gh auth status             # Expected: "Logged in to github.com account <you>"
```

### 2.6 Check list

```bash
python3 --version; git --version; gitleaks version; gh --version | head -1; make --version | head -1
```

Expected: five versions, and no "command not found". If one fails, do its
section again. You install Docker, kind, kubectl, syft and grype later, in the
first lab sheet that needs them.

---

## 3. Get the application

Your instructor gives you a file `ctf-scoreboard.zip` (on the course page,
or on a USB key). Save it in your **Downloads** folder. Then run:

```bash
cd ~/Downloads
unzip ctf-scoreboard.zip
ls -a ctf-scoreboard
```

Expected: `.env.example`, `.gitignore`, `Makefile`, `README.md`, `data`,
`docs`, `src`, `tests`, `tools`, … The application is now in
`~/Downloads/ctf-scoreboard`. **Do not work in this folder.** In lab
sheet 1, you copy it into your project folder, `~/devops-project`.

Maybe `unzip` created a folder with a different name. Then use that name
everywhere this guide says `~/Downloads/ctf-scoreboard`.

---

## 4. How to hand in your answers

Each lab sheet asks for a file `docs/TP<n>_answers.md` in your repository.
After lab sheet 1, Part E, **nobody can push directly to `main`**, because
`main` is protected. Every change follows these steps: *branch → push → pull
request → a teammate approves → merge*. This is how you hand in your
answers:

```bash
cd ~/devops-project
git switch main
git pull
git switch -c answers/tp1                 # use tp2, tp3, … for later sheets
nano docs/TP1_answers.md                  # write the answers, save, quit
git add docs/TP1_answers.md
git commit -m "docs: answers to lab sheet 1"
git push -u origin answers/tp1
gh pr create --fill                       # opens a pull request; prints its link
```

A teammate opens the link → **Files changed** → **Review changes** →
**Approve** → **Submit review**. Then anyone in the team clicks **Merge pull
request** → **Confirm merge**. Finally, everyone updates their copy:

```bash
git switch main && git pull
```

A simple layout for the answers file:

```markdown
# Lab sheet 1: answers
Team: <names>

## Exercise 1
(a) <your answer>
(b) <your answer>

## Exercise 2
(a) <your answer>
```

> Does your team work on several computers? Then only the people who
> **cloned** the repository from GitHub (Part E of lab sheet 1) can push.
> Everyone runs `git pull` at the start of each session.

---

## Lab sheet 1: Source control

Do Parts A to D on **one** computer: the computer of the driver. Part E
needs everybody.

### Part A: Identity and import

1. Open a terminal. If you did section 2.5, the three `git config` lines are
   already done. You can run them again: this does no harm.
2. Create the project folder and copy the application into it:

   ```bash
   mkdir -p ~/devops-project && cd ~/devops-project
   git init
   cp -r ~/Downloads/ctf-scoreboard/. .
   ls -a
   git check-ignore -v .env data/scoreboard.db src/scoreboard/app.py
   git add . && git commit -m "chore: import the CTF scoreboard application"
   ```

   - `cp -r ~/Downloads/ctf-scoreboard/. .`: be careful. There is a **dot
     after the slash**, a space, and **another dot**. The last dot means
     "here".
   - Expected after `git check-ignore`: two lines, one for `.env` and one for
     `data/scoreboard.db`. Nothing for `app.py` (it is *not* ignored).
   - Expected after `git commit`: a summary like `… files changed`.

**Exercise 1.** (a) Look at the output of `ls -a`. (b) To see which names
the `*` of the shell matches, compare `echo ~/Downloads/ctf-scoreboard/*`
with `ls -a ~/Downloads/ctf-scoreboard`. Read `.gitignore` with
`cat .gitignore`. (c) Think about what Git already stored in the commit.

### Part B: A conflict on purpose

1. Copy and run, one line at a time:

   ```bash
   git switch -c tune/lower
   sed -i 's/    points: 500/    points: 450/' data/challenges.yaml
   git commit -am "balance(challenges): lower the-long-game to 450"
   git switch main
   sed -i 's/    points: 500/    points: 600/' data/challenges.yaml
   git commit -am "balance(challenges): raise the-long-game to 600"
   git merge tune/lower
   ```

   Expected: `CONFLICT (content): Merge conflict in data/challenges.yaml`.
   This is the result that you want.

2. Run `git status` and read it. It lists the file as "both modified".
3. Open the file and fix it:

   ```bash
   nano data/challenges.yaml
   ```

   Press **Ctrl + W**, type `<<<<`, Enter. You see:

   ```
   <<<<<<< HEAD
       points: 600
   =======
       points: 450
   >>>>>>> tune/lower
   ```

   Keep **one** of the two `points:` lines. Your team decides which one.
   Delete the other one. Also delete the three marker lines: `<<<<<<<`,
   `=======` and `>>>>>>>`. To delete a line, put the cursor on it and press
   **Ctrl + K**. Keep the four spaces in front of `points:`. Save
   (**Ctrl + O**, Enter) and quit (**Ctrl + X**).

4. Check and finish the merge:

   ```bash
   grep -c '<<<<<<<\|>>>>>>>' data/challenges.yaml
   git add data/challenges.yaml && git commit --no-edit
   git log --graph --oneline --all | head
   ```

   Expected: `0` after `grep`, and a small drawing of two branches that join.
   If `grep` prints more than `0`, open the file again: a marker is still
   there.

**Exercise 2.** (a) and (b) Git compares files *line by line*. Which line did
each branch change? (c) The lab sheet and lecture 2 talk about checks that run
automatically: before a commit, and on a server.

### Part C: Find a bad commit with bisect

Use **the same terminal** for the whole part. This terminal remembers
`GOOD`.

1. Create 31 commits. One of them is broken. Copy the whole block and paste
   it at once:

   ```bash
   GOOD=$(git rev-parse HEAD)
   for i in $(seq 1 20); do echo "entry $i" >> docs/changelog.md
     git add docs/changelog.md && git commit -qm "docs: changelog entry $i"; done
   OLD='    return sum(s.points for s in solves)'
   NEW='    return sum(s.points for s in solves[1:])'
   sed -i "s/$OLD/$NEW/" src/scoreboard/scoring.py
   git commit -qam "refactor(scoring): simplify the point total"
   for i in $(seq 21 30); do echo "entry $i" >> docs/changelog.md
     git add docs/changelog.md && git commit -qm "docs: changelog entry $i"; done
   ```

   Check: `git log --oneline | head -3` shows `docs: changelog entry 30` on
   top.

2. Create the test script. Copy **from `cat` to the last `EOF`** (include
   this `EOF`). Paste it all at once:

   ```bash
   cat > /tmp/check.sh <<'EOF'
   #!/bin/sh
   PYTHONPATH=src python3 -c "
   from datetime import datetime, timezone
   from scoreboard.scoring import SolveRecord, total_points
   t = datetime(2026, 3, 1, tzinfo=timezone.utc)
   mk = lambda p: SolveRecord(team='a', challenge='c', points=p, at=t)
   assert total_points([mk(100), mk(250)]) == 350
   "
   EOF
   chmod +x /tmp/check.sh
   cat /tmp/check.sh
   ```

   Expected: `cat` prints the script back, ending with the line `"`.

3. Let Git search:

   ```bash
   git bisect start HEAD "$GOOD"
   git bisect run /tmp/check.sh
   ```

   Expected: several blocks of text. Near the end, there is a line
   `<long hash> is the first bad commit`. After it comes the commit message
   `refactor(scoring): simplify the point total`. Select the hash and copy it
   (**Ctrl + Shift + C**). To count the steps, count the lines that start
   with `running`.

4. Finish and repair. Paste your hash in place of `<the-bad-commit>`:

   ```bash
   git bisect reset
   git revert --no-edit <the-bad-commit>
   /tmp/check.sh && echo repaired
   ```

   Expected: `repaired`.

> Did you close the terminal and lose `GOOD`? Run `git log --oneline` and
> find the line `Merge branch 'tune/lower'`. Its hash (first column) is the
> good commit. Use it in place of `"$GOOD"`.

**Exercise 3.** (a) The number of steps is the number of `running` lines.
(b) For ⌈log₂ 31⌉: 2⁴ = 16 and 2⁵ = 32. (c) During bisect, Git *changes the
files in the folder* to each old version. (d) Think about what is inside that
one commit.

### Part D: A secret that stays in the history

```bash
git switch -c scratch/secret
echo 'BACKUP_ACCESS_KEY = "AKIAZ4XQ7RT2LMPB6WKD"' >> src/scoreboard/config.py   # gitleaks:allow
git commit -qam "chore: add backup configuration"
git checkout HEAD~1 -- src/scoreboard/config.py
git commit -qam "refactor: read the key from the environment"
gitleaks dir . ; echo "working tree: exit=$?"
gitleaks git -v . ; echo "history: exit=$?"
git switch main && git branch -D scratch/secret
```

- `gitleaks dir` looks at the files as they are now. `gitleaks git` looks at
  every commit.
- Expected: `working tree: exit=0`, then a report with `RuleID: …` and
  `history: exit=1`. Write down both exit codes and the `RuleID`.
- The key is fake. You delete this branch at the end, and you **never push
  it**.
- Why the comment `# gitleaks:allow` at the end of the `echo` line? Without
  it, your pipeline in lab sheet 2 reports *this guide* as a leak. You can
  type it or not. It is a comment, so it does not go into `config.py`. So
  gitleaks still finds the key there.

**Exercise 4.** (c) Run `git cat-file -p HEAD` once. The line `parent`
contains the hash of the previous commit. (d) and (e) Lecture 1 has a slide
"What you must do".

### Part E: One shared, protected repository

**The repository owner (one person):**

1. On <https://github.com>: click **+** (top right) → **New repository**.
   Name: `devops-project`. Choose **Public**. Do **not** tick "Add a README",
   ".gitignore" or "license". Click **Create repository**.
2. In the terminal (replace `<user>` with your GitHub user name):

   ```bash
   cd ~/devops-project
   git remote add origin https://github.com/<user>/devops-project.git
   git push -u origin main
   ```

   Expected: lines that end with `main -> main`. Reload the GitHub page: your
   files are there.
3. Add your teammates: **Settings** → **Collaborators** → **Add people** →
   their GitHub names. Each teammate accepts the invitation (by email, or on
   <https://github.com/notifications>).
4. Protect `main`: **Settings** → **Branches** → **Add classic branch
   protection rule**.
   - Branch name pattern: `main`
   - Tick **Require a pull request before merging**, and under it
     **Require approvals** = `1`.
   - Leave **Allow force pushes** and **Allow deletions** unticked.
   - Click **Create** (scroll down).

   > Does GitHub only show **Add branch ruleset**? Then:
   > - name it `main`;
   > - set *Enforcement status* to Active;
   > - *Target branches* → Add target → Include default branch;
   > - tick *Restrict deletions*, *Require a pull request before merging*
   >   (1 approval) and *Block force pushes*;
   > - click **Create**.

**Every team member (the owner too):**

1. Get your own copy. (Only the teammates do this. The owner already has a
   copy.)

   ```bash
   cd ~
   git clone https://github.com/<owner>/devops-project.git
   cd devops-project
   ```

2. Make a small change on your own branch, for example a challenge title:

   ```bash
   git switch -c docs/<your-name>
   nano data/challenges.yaml          # change the text after one "title:"
   git commit -am "docs: clearer title for one challenge"
   git push -u origin docs/<your-name>
   gh pr create --fill
   ```

3. Review the pull request of a teammate on GitHub:
   - open it → **Files changed**;
   - move the mouse over a line, click the blue **+**, write a real comment;
   - **Start a review** → **Review changes** → **Approve** → **Submit
     review**.
4. When your pull request is approved: **Merge pull request** →
   **Confirm merge**. Then, everybody:

   ```bash
   git switch main && git pull
   ```

   > Two pull requests that change the same line make a conflict. Merge one.
   > Then, in the other branch, run `git pull origin main`. Fix the file as in
   > Part B, commit and push.

**Exercise 5.** (a) and (b) An attacker steals the password of *one*
developer. Without the rule, what can this attacker do? (c) Read the box at
the top of `README.md`.

**Hand in** `docs/TP1_answers.md` as described in [section 4](#4-how-to-hand-in-your-answers).

---

## Lab sheet 2: Continuous integration

### Before you start

```bash
cd ~/devops-project
git switch main && git pull
make install            # creates .venv and installs everything: 2-5 minutes
make test               # Expected: "73 passed"
make lint               # Expected: nothing printed at all (silent = good)
```

Does `make install` say *No Python 3.11+ found* or *venv failed*? Then run
`sudo apt install -y python3-venv` and try again.

### Part A: The pipeline

1. Create a branch and the workflow file:

   ```bash
   git switch -c ci/pipeline
   mkdir -p .github/workflows
   nano .github/workflows/ci.yml
   ```

2. Copy the whole YAML block from the lab sheet: from `name: ci` to the last
   line `run: pip-audit -r requirements.txt`. Paste it into nano
   (**Ctrl + Shift + V**). Save and quit.
   - In YAML, **spaces are important**. Do not add or remove spaces at the
     start of lines. Never use the Tab key.
   - Check: `cat .github/workflows/ci.yml` must look exactly like the sheet.
3. Commit, push and open the pull request:

   ```bash
   git add .github && git commit -m "ci: add the verification pipeline"
   git push -u origin ci/pipeline
   gh pr create --fill
   ```

4. Open the link of the pull request. At the bottom, a check **ci / verify**
   appears with a yellow dot: it is running. Click **Details** to watch it.
   After 2–3 minutes, it should become **green ✓**.
5. A teammate approves, then **Merge pull request**. Then
   `git switch main && git pull`.

Is it red with **Invalid workflow file**? Then the spaces at the start of
some lines are wrong. Compare your file with the sheet, line by line. Fix it
on the same branch. Then run
`git commit -am "ci: fix indentation" && git push`.

**Exercise 1.** (a) `push` runs after the change is on `main`.
`pull_request` runs before. (b) and (c) Lecture 2 has a slide "Fail fast".

### Part B: Nobody can skip the pipeline

On GitHub:
1. **Settings** → **Branches**. Next to the `main` rule, click **Edit**.
2. Tick **Require status checks to pass before merging**.
3. In the search box, type `verify` and click it.
4. Click **Save changes** (at the bottom).

> `verify` appears in the search only after the pipeline ran at least once
> (Part A). Do you have a ruleset, not a rule? Then edit the ruleset → tick
> *Require status checks to pass* → **Add checks** → `verify`.

**Exercise 2.** (a) The command that skips local hooks is an option of
`git commit`. Look at `git commit --help`. To search, type `/no-verify` and
press Enter. To quit, press `q`.

### Part C: Why the install step is important

```bash
git switch -c scratch/no-install
nano .github/workflows/ci.yml          # delete the line "pip install -e ." (Ctrl+K)
git commit -am "test: remove the editable install"
git push -u origin scratch/no-install
gh pr create --fill
```

Wait until the check is **red ✗**. Click **Details**, then click the step
**tests**. Find the line that starts with `E   ModuleNotFoundError`. Copy
it.

Then clean up. On the page of the pull request, click **Close pull
request**. Then run:

```bash
git switch main
git branch -D scratch/no-install
git push origin --delete scratch/no-install
```

**Exercise 3.** (b) Look at the folders: `ls src`. The code is not at the
top of the repository. (c) Open the `Makefile` and read the `install:`
target.

### Part D: Four defects you did not write

1. Add the defects. Use **exactly the same team name** as your teammates:

   ```bash
   git switch main && git pull
   git switch -c chaos/tp2
   python3 tools/seed.py --team "<your team name>" --commit
   git push -u origin chaos/tp2
   gh pr create --fill
   ```

   Expected after `seed.py`: `planting four defects`, four lines, then
   `Done.`

   Maybe GitHub **refuses** `git push` with a message about a secret
   (*push protection*). Then open the link that it prints. Choose: the secret
   is *used in tests*. Confirm, and run `git push` again.

2. Wait until the run finishes (red). **Do not look at the code changes
   yet.** On the pull request, click **Details**. Open each red step:
   - **tests**: the lines that start with `FAILED tests/…` give the test
     names. Look just above, in the *FAILURES* section. Each test shows one
     of two things:
     - an `assert …` line: this is an **assertion**;
     - an error name, for example `AttributeError`, `KeyError`,
       `FileNotFoundError`: this is an **exception**.
   - **secret scan**: the lines `RuleID:`, `File:` and `Line:`.
   - **dependency audit**: a table with `Name`, `Version`, `ID`,
     `Fix Versions`.
3. Write the diagnosis **before fixing anything**:

   ```bash
   nano docs/TP2_diagnosis.md
   ```

   Example layout (fill in from the log):

   ```markdown
   # Lab sheet 2: diagnosis from the pipeline log

   | Defect | Gate that failed | Name in the log | Assertion or exception | One-line cause |
   |---|---|---|---|---|
   | Test 1 | | | | |
   | Test 2 | | | | |
   | Credential | | | — | |
   | Dependency | | | — | |
   ```

   ```bash
   git add docs/TP2_diagnosis.md && git commit -m "docs: diagnosis from the pipeline log"
   git push
   ```

**Exercise 5: the fixes.**

1. Now look at the changes: on the pull request, open the tab **Files
   changed**. The tab **Commits** lists each commit of the seed script.
2. Undo each defect **by editing the files** with nano. Do not edit the
   tests.
   - Put the original code back.
   - Remove the line with the fake credential.
   - Put `requirements.txt` back as it was on `main`. To compare, use
     `git diff main -- requirements.txt`.
3. Check locally, then push:

   ```bash
   make install             # requirements.txt changed: reinstall
   make test                # Expected: 73 passed
   make lint                # Expected: silent
   git commit -am "fix: repair the seeded defects"
   git push
   ```

   Several small commits are even better than one: one for each defect, with
   clear messages.
4. The run should become **green**. Leave the pull request **open** for your
   instructor. Do not merge it.

Then answer (a) and (b). A *direct* dependency is listed in
`requirements.txt` on `main`. To see which package needs another package, use
`.venv/bin/pip show <package>` and read the `Required-by` line.

**Hand in** `docs/TP2_answers.md` ([section 4](#4-how-to-hand-in-your-answers)).

---

## Lab sheet 3: Containers

### Before you start: install Docker (once)

```bash
sudo apt install -y docker.io docker-buildx
sudo usermod -aG docker $USER
```

Now **log out of your session and log in again** (or restart the computer).
The group change works only in new sessions. Then:

```bash
docker info | head -5          # no "permission denied"
docker run --rm hello-world    # Expected: "Hello from Docker!"
docker pull python:3.12-slim   # slow the first time
cd ~/devops-project && git switch main && git pull
git switch -c feat/container
```

### Part A: A multi-stage image

1. Create the two files with nano. Paste the two blocks from the sheet:

   ```bash
   nano .dockerignore      # paste the list (.git, .venv, … tests/), save, quit
   nano Dockerfile         # paste the whole Dockerfile, save, quit
   ```

   The file is called exactly `Dockerfile` (capital D, no extension).

2. Build, and compare sizes:

   ```bash
   docker build -t scoreboard:local .
   docker images --format "{{.Repository}}:{{.Tag}}\t{{.Size}}" | grep -E "scoreboard|python"
   ```

   The first build takes a few minutes. Expected at the end:
   `naming to docker.io/library/scoreboard:local` (or `Successfully tagged`).

3. Change one byte of code and build again. Which steps say `CACHED`?

   ```bash
   echo "# $(date +%s)" >> src/scoreboard/app.py
   docker build -t scoreboard:local .
   git checkout src/scoreboard/app.py
   ```

   In the output of the second build, each step is a line like
   `=> CACHED [build 4/8] COPY requirements.txt .`. Write down which steps are
   `CACHED` and which steps ran again.

**Exercise 1.** (a) The sizes are in the output of `docker images`.
(b) and (c) Read the two `FROM … AS …` parts of the Dockerfile. Only what
`COPY --from=build` copies goes into the final image. (d) Use the `CACHED`
lines.

### Part B: Run it with the minimum it needs

```bash
docker run -d --name sb -p 8000:8000 -e ADMIN_TOKEN=dev \
  --read-only --tmpfs /tmp \
  --cap-drop ALL --security-opt no-new-privileges \
  --memory 256m --cpus 0.5 \
  -v sbdata:/app/data \
  scoreboard:local
sleep 5 && ./tools/smoke.sh localhost:8000
docker exec sb id
docker exec sb sh -c 'touch /app/x || echo "root filesystem is read-only"'
```

- Expected after the smoke test: a list of `ok` lines and `all good`.
- Expected after `id`: `uid=10001(scoreboard)`.
- Does the smoke test say `FAIL liveness`? Wait 10 seconds and run
  `./tools/smoke.sh localhost:8000` again. Does it still fail? Run
  `docker logs sb`.

**Exercise 2.** (a) and (b) The mounts are the options `--tmpfs` and `-v`.
(c) Lecture 3 has the table "Six controls, and what each prevents".

### Part C: Who receives SIGTERM?

```bash
time docker stop sb
docker run -d --name sb2 --entrypoint sh scoreboard:local \
  -c 'python -m scoreboard; echo exited'
sleep 5 && docker exec sb2 cat /proc/1/cmdline; echo
time docker stop sb2
docker rm sb sb2
```

`time` prints three lines. Use the line `real`. Expected: less than one
second for the first container, about 10 seconds for the second.

**Exercise 3.** (b) `cat /proc/1/cmdline` shows which program is PID 1 in
`sb2`. Lecture 3, slide "A container is a process", explains PID 1.

### Part D: Scan the image

```bash
docker save scoreboard:local -o /tmp/scoreboard.tar
docker run --rm -v /tmp/scoreboard.tar:/img.tar:ro aquasec/trivy:0.75.0 \
  image --input /img.tar --severity HIGH,CRITICAL --ignore-unfixed
```

The first run downloads the scanner and its database (1–3 minutes).
Expected: one or more tables. Each table starts with a line like
`Total: 3 (HIGH: 2, CRITICAL: 1)`. The columns are *Library*,
*Vulnerability* and *Severity*. `Total: 0` is also a correct result.

**Exercise 4.** (a) and (b) Look at the *Library* column. Are these Python
packages, or system packages (names like `libc6`, `openssl`)? (c) Read again
the paragraph above the commands in the sheet.

### Part E: Build and publish from the pipeline

1. Add the `image` job at the **end** of the workflow file:

   ```bash
   nano .github/workflows/ci.yml
   ```

   Go to the very end of the file (**Ctrl + End**, or press ↓ many times).
   Press Enter to add an empty line. Then paste the job from the sheet. The
   line `  image:` must start with **exactly two spaces**, like `  verify:`
   near the top. The end of your file looks like this:

   ```yaml
         - name: dependency audit
           if: ${{ !cancelled() }}
           run: pip-audit -r requirements.txt

     image:
       needs: verify
       if: github.event_name == 'push'
   ```

2. Commit everything from this lab sheet and open a pull request:

   ```bash
   git add Dockerfile .dockerignore .github/workflows/ci.yml
   git commit -m "feat: container image built and published by the pipeline"
   git push -u origin feat/container
   gh pr create --fill
   ```

   On the pull request, only `verify` runs. (The `image` job runs only on
   `main`.) When it is green and approved, click **Merge pull request**.
3. On GitHub, open the tab **Actions**. A new run starts on `main`, with two
   jobs. Wait until **image** is green (2–4 minutes).
4. Make the image public:
   - go to your GitHub profile (or to the main page of the repository, right
     column **Packages**);
   - click the package `devops-project` → **Package settings** (on the
     right);
   - **Danger Zone** → **Change visibility** → **Public**;
   - type the name to confirm.
5. Run the published image:

   ```bash
   git switch main && git pull
   IMG=ghcr.io/<owner>/devops-project:$(git rev-parse HEAD)
   IMG=$(echo "$IMG" | tr 'A-Z' 'a-z')      # image names must be lower case
   echo "$IMG"                              # keep this: you need it in lab sheets 4 and 6
   docker run -d --name pub -p 8000:8000 "$IMG"
   sleep 5 && curl -s localhost:8000/version; echo
   docker rm -f pub
   ```

   Expected: `{"version":"1.0.0","commit":"<the same long hash>",…}`. Copy the
   `IMG` value into your notes.

   > Does `docker run` say *not found* or *denied*? Then one of these is
   > true: the run on `main` is not finished, the package is still private,
   > or `<owner>` is wrong.

**Exercise 5.** (a) Follow the commit hash: Git → the workflow
(`github.sha`) → `build-args` → `ARG`/`ENV BUILD_SHA` in the Dockerfile →
`/version` of the application. (b) Imagine two versions, both called
`latest`.

**Hand in** `docs/TP3_answers.md` ([section 4](#4-how-to-hand-in-your-answers)).

---

## Lab sheet 4: Kubernetes

### Before you start: install kind and kubectl (once)

```bash
cd /tmp
curl -Lo kind https://github.com/kubernetes-sigs/kind/releases/download/v0.33.0/kind-linux-amd64
install -m 0755 kind ~/.local/bin/kind
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
install -m 0755 kubectl ~/.local/bin/kubectl
cd ~/devops-project
kind version                   # Expected: kind v0.33.0 …
kubectl version --client       # Expected: Client Version: v1.…
git switch main && git pull
git switch -c feat/k8s
echo "$IMG"                    # empty? set it again, as in lab sheet 3, Part E, step 5
```

You need about 4 GB of free memory. Close other big programs.

### Part A: A cluster

```bash
mkdir -p cluster
nano cluster/kind.yaml         # paste the kind configuration from the sheet
kind create cluster --name scoreboard --config cluster/kind.yaml
kubectl get nodes
kubectl get pods -A
```

`kind create cluster` takes 1–3 minutes. Expected: `kubectl get nodes` shows
one node with STATUS `Ready`. If it shows `NotReady`, wait 30 seconds and run
it again.

**Exercise 1.** Use the names in the NAME column (`coredns`, `etcd`,
`kube-apiserver`, `kube-scheduler`, `kube-proxy`, …). Lecture 4, slide
"Control plane and nodes", says what each one does.

### Part B: Deploy and reach it

1. Create the three files:

   ```bash
   mkdir -p k8s
   nano k8s/namespace.yaml        # paste the Namespace block
   nano k8s/deployment.yaml       # paste the Deployment block
   nano k8s/service.yaml          # paste the Service block
   ```

2. In `k8s/deployment.yaml`, replace `ghcr.io/OWNER/REPO:SHA` with your
   image:
   - run `echo "$IMG"` and copy the result;
   - in nano, use **Ctrl + W** to find `OWNER`;
   - delete the old value (keep `image: ` and the spaces before it);
   - paste your value.
3. Create the namespace, the secret, and everything else:

   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl -n scoreboard create secret generic scoreboard-admin \
     --from-literal=token="$(openssl rand -hex 24)"
   kubectl apply -f k8s/
   kubectl -n scoreboard get pods -w
   ```

   Watch the line. Wait until `READY` shows `1/1` and `STATUS` shows
   `Running` (less than one minute). Then press **Ctrl + C**.

4. Check it works:

   ```bash
   ./tools/smoke.sh localhost:8080
   kubectl -n scoreboard get endpoints scoreboard
   ```

   Expected: `all good`, and an endpoint like `10.244.0.7:8000`.

   > Does the pod stay in `ImagePullBackOff` or `ErrImagePull`? Run
   > `kubectl -n scoreboard describe pod -l app=scoreboard | tail -20`.
   > Usually, the image name has a capital letter or a typing error, or the
   > package is still private (lab sheet 3, Part E, step 4). Fix the file and
   > run `kubectl apply -f k8s/` again.

**Exercise 2.**

```bash
nano k8s/service.yaml          # change  app: scoreboard  to  app: scoreboard-v2  (selector line only)
kubectl apply -f k8s/service.yaml
kubectl -n scoreboard get endpoints scoreboard      # look at ENDPOINTS
nano k8s/service.yaml          # change it back to  app: scoreboard
kubectl apply -f k8s/service.yaml
```

### Part C: Readiness is not liveness

1. Break the database path:

   ```bash
   kubectl -n scoreboard set env deploy/scoreboard DATABASE_URL="sqlite:////nonexistent/x.db"
   kubectl -n scoreboard get pods -w
   ```

   You see **two** pods: the old one (`1/1 Running`) and a new one that
   stays `0/1 Running`. Wait 30 seconds. Write down READY and RESTARTS for
   both. Press **Ctrl + C**. Then run:

   ```bash
   kubectl -n scoreboard get endpoints scoreboard
   kubectl -n scoreboard logs -l app=scoreboard --tail=3
   ```

   In the logs, look for `database not reachable`.

2. Make liveness check the database too. Copy the three lines at once:

   ```bash
   P=/spec/template/spec/containers/0/livenessProbe/httpGet/path
   kubectl -n scoreboard patch deploy scoreboard --type json \
     -p "[{\"op\":\"replace\",\"path\":\"$P\",\"value\":\"/readyz\"}]"
   kubectl -n scoreboard get pods -w
   ```

   Watch the RESTARTS column of the new pod for **two minutes**. It goes up
   about every 30–40 seconds. Write down the number and press **Ctrl + C**.

3. Go back to what the files say. Wait until it is finished:

   ```bash
   kubectl apply -f k8s/
   kubectl -n scoreboard rollout status deploy/scoreboard
   ```

   Expected: `successfully rolled out`.

**Exercise 3.** (c) In `k8s/deployment.yaml`, find the path that each of the
three probes reads. Lecture 4 has the slide "Three probes, three different
questions".

### Part D: A bad release, and a rollback

Use your own image name with a tag that does not exist. `${IMG%:*}` is your
`IMG` without the `:<hash>` at the end:

```bash
kubectl -n scoreboard set image deploy/scoreboard app=${IMG%:*}:does-not-exist
kubectl -n scoreboard get pods
./tools/smoke.sh localhost:8080
kubectl -n scoreboard rollout history deploy/scoreboard
kubectl -n scoreboard rollout undo deploy/scoreboard
kubectl -n scoreboard rollout status deploy/scoreboard
```

Do not type `OWNER/REPO` in capital letters. Kubernetes then rejects the name
itself (`InvalidImageName`). This is a different failure.

Expected:
- the new pod shows `ErrImagePull` or `ImagePullBackOff`;
- the smoke test still says `all good`;
- after `undo`: `successfully rolled out`.

**Exercise 4.** (a) Compare the two pods in `get pods`. (c) Compare the
cluster with the file:
`kubectl -n scoreboard get deploy scoreboard -o yaml | grep image:` and
`grep image: k8s/deployment.yaml`.

### Part E: The files are the truth

```bash
kubectl -n scoreboard scale deploy/scoreboard --replicas=2
kubectl diff -f k8s/
```

`kubectl diff` prints the differences: `-` is the cluster now, `+` is the
file. Decide as a team. Then **either** write `replicas: 2` in
`k8s/deployment.yaml`, **or** run `kubectl apply -f k8s/`. Check that
`kubectl diff -f k8s/` now prints nothing. Then commit:

```bash
git add cluster k8s
git commit -m "feat: kind cluster and kubernetes manifests"
git push -u origin feat/k8s
gh pr create --fill
```

A teammate approves it, and you merge it. Then run
`git switch main && git pull`.

**Exercise 5.** (a) Look at `git log --oneline -5`. Which of the four
commands appear there?

**Hand in** `docs/TP4_answers.md` ([section 4](#4-how-to-hand-in-your-answers)).

> **The cluster after a restart.** kind runs inside Docker. After the
> computer restarts, run `kubectl get nodes`. If it fails, run
> `docker start scoreboard-control-plane`, wait one minute, and try again.
> Is the cluster gone (`kind get clusters` prints nothing)? Then do Part A
> again, the `create secret` command, and `kubectl apply -f k8s/`.

---

## Lab sheet 5: GitOps, error budgets and a canary

### Before you start

```bash
cd ~/devops-project
kubectl get nodes                 # Ready? If not, see the box at the end of lab sheet 4
kubectl diff -f k8s/              # must print nothing; if it does: kubectl apply -f k8s/
```

Your repository must be **public** (Argo CD reads it without a password).

### Part A: Install Argo CD and give it the cluster

1. Create the branch that Argo CD follows, and install Argo CD:

   ```bash
   git switch main && git pull
   git switch -c deploy && git push -u origin deploy
   kubectl create namespace argocd
   kubectl apply -n argocd --server-side --force-conflicts -f \
     https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   kubectl -n argocd wait --for=condition=available deploy --all --timeout=300s
   ```

   The installation takes 2–4 minutes. Expected at the end: several lines
   that end with `condition met`.

2. Create the application file, with **your** repository address
   (`https://github.com/<owner>/devops-project.git`):

   ```bash
   nano cluster/argocd-app.yaml   # paste the Application block; replace OWNER/REPO
   kubectl apply -f cluster/argocd-app.yaml
   kubectl -n argocd get application scoreboard -w
   ```

   Wait until the line shows `Synced` and `Healthy` (up to 3 minutes). Then
   press **Ctrl + C**.

3. Define the small command `refresh`. It makes Argo CD look at Git now, not
   in 3 minutes. Paste both lines at once:

   ```bash
   refresh() { kubectl -n argocd annotate application scoreboard \
               argocd.argoproj.io/refresh=normal --overwrite >/dev/null; }
   ```

   > The terminal forgets `refresh` when you close it. In a new terminal,
   > paste these two lines again.

4. Save the application file on the `deploy` branch:

   ```bash
   git add cluster/argocd-app.yaml
   git commit -m "deploy: add the Argo CD application"
   git push
   ```

   > Does it stay `Unknown` or `OutOfSync`? Run
   > `kubectl -n argocd describe application scoreboard | tail -20`. Usually,
   > the `repoURL` is wrong, or the repository is private.

**Exercise 1.** (a) Who connects to whom? Does GitHub contact your laptop,
or does something in your cluster contact GitHub? Lecture 6 has the slide
"Push versus pull, and why the direction matters".

### Part B: Try to change the cluster by hand

```bash
kubectl -n scoreboard scale deploy/scoreboard --replicas=5
sleep 20; kubectl -n scoreboard get deploy scoreboard
```

**Exercise 2.** (a) Look at the READY column (for example `2/2`). (b) Find
the setting under `syncPolicy` in `cluster/argocd-app.yaml` that explains
it.

### Part C: Spend an error budget, then roll back with Git

You are on the `deploy` branch (check: `git branch --show-current`).

1. Add the line `- { name: ERROR_RATE, value: "0.2" }` to the environment of
   the container:

   ```bash
   nano k8s/deployment.yaml
   ```

   Press **Ctrl + W**, type `DATABASE_URL`, press Enter. You are on the line
   `- { name: DATABASE_URL, value: "sqlite:////data/scoreboard.db" }`. Press
   **End**, then **Enter**. Type the new line with **the same number of
   spaces** in front (12 spaces). Save and quit.

2. Commit, push, and let Argo CD apply it:

   ```bash
   git commit -am "deploy: inject 20% errors on /scoreboard"
   git push
   refresh
   kubectl -n scoreboard rollout status deploy/scoreboard
   ```

   Does `rollout status` finish immediately, without "Waiting"? Then wait
   20 seconds, run `refresh` again, then `rollout status` again.

3. Measure. Paste the whole block at once:

   ```bash
   ok=0; err=0
   for i in $(seq 200); do
     if [ "$(curl -s -o /dev/null -w '%{http_code}' localhost:8080/scoreboard)" = 200 ]
     then ok=$((ok+1)); else err=$((err+1)); fi
   done; echo "ok=$ok err=$err"
   curl -s localhost:8080/metrics | grep 'requests_total{.*/scoreboard'
   ```

   Expected: something like `ok=162 err=38`. Then two lines that end with a
   number: one with `status="2xx"` and one with `status="5xx"`. (With several
   replicas, `/metrics` shows only the counters of the pod that answered.)

4. Roll back with Git:

   ```bash
   git revert --no-edit HEAD
   git push
   refresh
   kubectl -n scoreboard rollout status deploy/scoreboard
   ```

   Run the measuring block again: `err` should now be `0`.

**Exercise 3.** (a) 30 days × 24 hours × 60 minutes, then 0.5 % of that.
(b) Error ratio = err ÷ 200. (c) Budget (in minutes) ÷ your error ratio, then
convert to hours. (d) Lecture 7, slide "Querying: the four expressions you
need", has an expression for the error ratio. Change the metric name and the
labels to the ones that `grep` showed you.

**Exercise 4.** (a) Look at `git log --oneline -3` on `deploy`.
(b) Remember which branch Argo CD follows, and what `selfHeal` does.

### Part D: A canary that you can recognise

1. Create the canary file from the stable one:

   ```bash
   cp k8s/deployment.yaml k8s/deployment-canary.yaml
   nano k8s/deployment-canary.yaml
   ```

   Change four places. Use **Ctrl + W** to find each one:
   - `name: scoreboard,` on the first `metadata` line →
     `name: scoreboard-canary,`
   - the `replicas:` line → `replicas: 1`
   - the `selector:` line → `selector: { matchLabels: { app: scoreboard, track: canary } }`
   - the template's `labels:` line → `metadata: { labels: { app: scoreboard, track: canary } }`

   Then add a line under the `DATABASE_URL` line, with the same 12 spaces:
   `- { name: SCORING_MODE, value: static }`. Save and quit.

2. In `k8s/deployment.yaml` (the stable version), write `replicas: 3`.
3. Commit and watch both versions answer:

   ```bash
   git add k8s/
   git commit -m "deploy: canary with static scoring"
   git push
   refresh; sleep 30; kubectl -n scoreboard get pods -L track
   for i in $(seq 20); do
     curl -s localhost:8080/version | python3 -c \
       "import sys,json; print(json.load(sys.stdin)['scoring_mode'])"
   done | sort | uniq -c
   ```

   Expected: four pods, one of them with `canary` in the TRACK column. Then
   two counts, for example `15 decay` and `5 static`.

4. Reject the canary:

   ```bash
   git rm k8s/deployment-canary.yaml
   git commit -m "deploy: reject the canary"
   git push
   refresh; sleep 20; kubectl -n scoreboard get pods -L track
   ```

   Expected: the canary pod is gone (or `Terminating`).

5. Bring the `deploy` branch back to `main` with a pull request:

   ```bash
   gh pr create --base main --head deploy --fill
   ```

   When it is approved, merge it. But **do not delete the `deploy` branch**:
   Argo CD still follows it. If GitHub shows *Delete branch*, ignore it.

**Exercise 5.** (a) and (b) Count the pods of each kind. (c) Count again for
10 %. (d) Think about `selfHeal` again. (e) Look again at what you measured in
Part C.

**Hand in** `docs/TP5_answers.md` ([section 4](#4-how-to-hand-in-your-answers)).

---

## Lab sheet 6: Supply chain and measurement

### Before you start: install syft and grype (once)

```bash
cd /tmp
curl -sSL https://github.com/anchore/syft/releases/download/v1.54.1/syft_1.54.1_linux_amd64.tar.gz | tar -xz syft
curl -sSL https://github.com/anchore/grype/releases/download/v0.120.1/grype_0.120.1_linux_amd64.tar.gz | tar -xz grype
mv syft grype ~/.local/bin/
cd ~/devops-project
syft version | head -3; grype version | head -3
gh auth status                # still logged in?
git switch main && git pull
IMG=ghcr.io/<owner>/devops-project:$(git rev-parse HEAD)
IMG=$(echo "$IMG" | tr 'A-Z' 'a-z'); echo "$IMG"
```

`IMG` now names the image built from the latest commit on `main`.

### Part A: What is in the image

```bash
syft scan "$IMG" -o spdx-json=sbom.spdx.json
jq '.packages | length' sbom.spdx.json
syft scan "$IMG" -o json | jq -r '.artifacts[].type' | sort | uniq -c
grep -cvE '^\s*(#|$)' requirements.txt
```

Expected:
- one number: all the packages;
- a short table with a count for each type (`deb` = operating-system
  packages, `python` = Python packages, …);
- the number of lines that you declared in `requirements.txt`.

**Exercise 1.** (a) The three numbers are the three outputs. (c) In lab
sheet 2, `pip-audit` read only `requirements.txt`.

### Part B: Scan the list

```bash
grype sbom:./sbom.spdx.json --only-fixed
grype sbom:./sbom.spdx.json --only-fixed --fail-on high; echo "exit=$?"
```

The first run downloads a vulnerability database (a few minutes). Expected:
a table with a SEVERITY column, or `No vulnerabilities found`. To count the
high and critical lines, run:
`grype sbom:./sbom.spdx.json --only-fixed | grep -cE 'High|Critical'`.

**Exercise 2.** (a) Compare with the `Total:` line of Trivy in lab sheet 3,
Part D. (b) Each scanner has its own vulnerability database.

### Part C: Prove where the image comes from

1. Edit the workflow on a new branch:

   ```bash
   git switch -c feat/attest
   nano .github/workflows/ci.yml
   ```

   - In the `image:` job, find the line
     `    permissions: { contents: read, packages: write }` (4 spaces).
     Replace it with the five `permissions:` lines from the sheet. Put
     4 spaces before `permissions:`, and 6 spaces before each of the four
     lines under it.
   - Go to the end of the file. Find the last line of the `build-push` step
     (`build-args: BUILD_SHA=…`). After it, add the step
     `- uses: actions/attest@v4` from the sheet. The spaces:
     - **6 spaces** before `- uses`;
     - 8 spaces before `with:`;
     - 10 spaces before `subject-name`, `subject-digest` and
       `push-to-registry`.

2. Commit, open a pull request, and merge it after the approval:

   ```bash
   git commit -am "ci: attest the image build"
   git push -u origin feat/attest
   gh pr create --fill
   ```

3. After the merge, wait until the run on `main` (tab **Actions**) has a
   green **image** job. Then set `IMG` to this new image, and verify it:

   ```bash
   git switch main && git pull
   IMG=ghcr.io/<owner>/devops-project:$(git rev-parse HEAD)
   IMG=$(echo "$IMG" | tr 'A-Z' 'a-z'); echo "$IMG"
   gh attestation verify "oci://$IMG" -R <owner>/devops-project; echo "exit=$?"
   gh attestation verify oci://docker.io/library/nginx:latest -R <owner>/devops-project; echo "exit=$?"
   ```

   Expected: the first command prints `✓ Verification succeeded!`, a short
   summary, then `exit=0`. The second command fails with `exit=1`.

**Exercise 3.** (a) Copy the lines of the successful output (repository,
workflow, commit, …). (b) Does it say anything about the *code* in that
commit? Is this code safe? See lecture 8, "Three artefacts, three different
claims".

### Part D: Deploy exactly this image

```bash
docker pull "$IMG"
docker inspect --format '{{index .RepoDigests 0}}' "$IMG"
```

Expected: one line like `ghcr.io/<owner>/devops-project@sha256:3f2a…`. Copy
the whole line. Then run:

```bash
git switch deploy && git pull
nano k8s/deployment.yaml      # replace everything after "image: " with the line you copied
git commit -am "deploy: pin the attested image by digest"
git push
refresh() { kubectl -n argocd annotate application scoreboard \
            argocd.argoproj.io/refresh=normal --overwrite >/dev/null; }
refresh; kubectl -n scoreboard rollout status deploy/scoreboard
curl -s localhost:8080/version; echo
```

Expected: `/version` shows the same commit hash as the end of your `IMG`.

**Exercise 4.** (a) A tag (`:<hash>`) is a name. A person with write access
to the registry can move it. A digest is calculated from the content. See
lecture 3, slide "A tag is a label; a digest is an identity".

### Part E: Measure your team

```bash
git fetch origin
git log origin/deploy --grep='^deploy:' --format='%ad' --date=short | sort | uniq -c
git log origin/deploy --format='%ad  %s' --date=iso | grep -E 'deploy:|Revert'
gh run list --workflow=ci.yml --branch=main --limit 50 \
  --json conclusion --jq '.[].conclusion' | sort | uniq -c
```

- The first command counts the deployments of each day (each `deploy:`
  commit).
- The second command lists them with their times. It also lists the reverts.
  (A revert means: a change failed, and you restored the old version.)
- The third command counts the pipeline results on `main` (`success`,
  `failure`, …).

**Exercise 5.** (a) Lecture 1 defines the four metrics. It also shows a
complete example ("Example: the calculation"). Use your own numbers in the
same way. Write down the assumption behind each number.

**Hand in** `docs/TP6_answers.md` ([section 4](#4-how-to-hand-in-your-answers)).
Put the SBOM file `sbom.spdx.json` in the same pull request:
`git add sbom.spdx.json`.

---

## When something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| `command not found` | the program is not installed, or the terminal does not know where it is | do its install step again. For tools in `~/.local/bin`, run `source ~/.bashrc` |
| `fatal: not a git repository` | you are not in your project folder | `cd ~/devops-project` |
| `git push` asks for a user name or password | Git is not using your GitHub login | `gh auth login`, then `gh auth setup-git` |
| `! [remote rejected] main -> main (protected branch hook declined)` | you tried to push to `main` | work on a branch and open a pull request ([section 4](#4-how-to-hand-in-your-answers)) |
| `! [rejected] … (fetch first)` or `(non-fast-forward)` | GitHub has commits you do not have | `git pull`, then `git push` again |
| `error: Your local changes … would be overwritten` | you have changes that are not committed | run `git status`. Commit the changes, or undo them with `git checkout <file>` |
| `CONFLICT` after `git pull` or `git merge` | two changes to the same line | fix the file as in lab sheet 1, Part B, then `git add <file>` and `git commit --no-edit` |
| a strange screen with `~` lines, and keys do not work | Git opened the *vim* editor | press **Esc**, type `:wq`, press Enter. Then run `git config --global core.editor nano` |
| a screen with `:` at the bottom | a pager | press **q** |
| `permission denied while trying to connect to the Docker daemon socket` | your user is not in the `docker` group yet | `sudo usermod -aG docker $USER`, then log out and in |
| `port is already allocated` | an old container uses the port | `docker ps`, then `docker rm -f <name>` |
| GitHub check red: **Invalid workflow file** | wrong spaces in `ci.yml` | compare with the sheet. Use spaces only, no tabs |
| `The connection to the server … was refused` (kubectl) | the cluster is not running | see the box at the end of lab sheet 4 |
| pod `ImagePullBackOff` | wrong image name, capital letters, or private package | lab sheet 4, Part B, step 4 |
| pod `CrashLoopBackOff` | the container stops again and again | `kubectl -n scoreboard logs <pod> --previous` |
| `make install`: *No Python 3.11+ found* or *venv failed* | Python or `venv` missing | `sudo apt install -y python3 python3-venv` |
| Argo CD stays `OutOfSync` | wrong `repoURL`, private repository, or a YAML mistake in `k8s/` | `kubectl -n argocd describe application scoreboard \| tail -20` |

Still blocked? Copy the **exact** error message and the command that you
ran. Show both to your instructor or to a teammate. Nobody can fix "it does
not work". An error message usually helps to fix the problem.

---

## Cheat sheet

| I want to… | Command |
|---|---|
| see where I am | `pwd` |
| go to my project | `cd ~/devops-project` |
| see the state of my files | `git status` |
| see the last commits | `git log --oneline -10` |
| see which branch I am on | `git branch --show-current` |
| get the latest `main` | `git switch main && git pull` |
| start new work | `git switch -c <type>/<short-name>` |
| save my work in Git | `git add <files>` then `git commit -m "<type>: <what>"` |
| send my branch to GitHub | `git push -u origin <branch>` (later just `git push`) |
| open a pull request | `gh pr create --fill` |
| edit a file | `nano <file>` (save Ctrl+O Enter, quit Ctrl+X) |
| run the tests | `make test` |
| run the application locally | `ADMIN_TOKEN=dev make run`, then open <http://localhost:8000/docs>. Stop with Ctrl+C |
| list running containers | `docker ps` |
| see a container's output | `docker logs <name>` |
| list pods | `kubectl -n scoreboard get pods` |
| see why a pod has a problem | `kubectl -n scoreboard describe pod <pod> \| tail -20` |
| see a pod's output | `kubectl -n scoreboard logs <pod>` |
| make Argo CD look at Git now | `refresh` (define it first, lab sheet 5, Part A, step 3) |
