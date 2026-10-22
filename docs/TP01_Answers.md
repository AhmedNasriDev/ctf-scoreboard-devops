# Lab 1 Sheet : answers

**Team :** Nasri ahmed, Ferg Mohamed El'Amine, Bouziane Chakib, Abdi Ahmed Raed

## Exercise 1:

- **(a).** The two hidden files are `.gitignore` and `.env`.

- **(b).** The `*` wildcard does not copy hidden files whose names begin with a
dot. As a result, files such as `.gitignore` and `.env` would be left
out. Using `cp -r .../ctf-scoreboard/. .` copies the contents of the
directory, including hidden files.

- **(c).** Adding `.env` to `.gitignore` does not stop Git from tracking it because
the file has already been committed. `.gitignore` only prevents matching
untracked files from being added automatically. To stop tracking it, we
must remove it from Git's index and commit that change. If it contains a
real secret, we must also revoke or rotate the secret because it remains
in the repository history.

## Exercise 2:

- **(a).** Both branches changed the points for the same challenge,
`the-long-game`, but one changed the value to 450 and the other to 600.
Git cannot know which value we intended to keep, so we must resolve the
conflict manually.

- **(b).** If the changes are on separate lines and do not overlap, Git can usually
merge them automatically. A conflict happens when both changes affect
the same or overlapping parts of the file.

- **(c).** We can run the check in a Git pre-commit hook or in a CI workflow such
as GitHub Actions when a push or pull request is opened. A required CI
status check can prevent merging until the check passes.

## Exercise 3:

- **(a).** In my run, Git tested several intermediate commits and identified
`57651a0` (`refactor(scoring): simplify the point total`) as the first
bad commit. The output showed five intermediate test commits before Git
reported the bad commit.

- **(b).** log`2`(31) ≈ 5, because (2\^4 = 16) and
(2\^5 = 32). This means binary search needs about five steps to narrow
down 31 possible commits in the worst case and that's what happened with us. 
The actual number of test runs depends on the commits included between the good and bad endpoints.

- **(c).** If `check.sh` is inside the repository, checking out an older commit
during bisect could change the script or make it disappear if that
commit does not contain it. Keeping the script in `/tmp/check.sh` means
the same test script is used while Git checks different commits.

- **(c).** If the 31 commits are squashed into one commit, the individual commits
disappear from the history. Git bisect can no longer identify which
original commit introduced the bug; it can only identify the squashed
commit as bad

## Exercise 4:

- **(a).** Exit Codes:
	-   `gitleaks dir .`: exit code **0**, because no leak was found in the
    current working tree.
	-   `gitleaks git -v .`: exit code **1**, because Gitleaks found the
    fake key in Git history.

- **(b).** The rule was `aws-access-token`.

- **(c).** Each commit points to its parent commit. The second commit removes the
key from the latest version of the file, but the earlier commit that
added the key still exists in Git history. Therefore, Gitleaks can still
find it when scanning the history.

- **(d).** First, we revoke or rotate the exposed key immediately so it cannot be
used by someone else. Second, we remove the secret from the repository
and clean up the history where possible. Revoking the key comes first
because deleting it from the latest version does not make the exposed
credential invalid.

## Exercise 5:

- **(a).** Branch protection requires changes to go through pull requests and receive approval before they are merged into `main`. This makes it harder for someone to add unreviewed or malicious code directly to the main branch. Blocking force pushes and deletion also helps protect the repository history.

- **(b).** It makes unauthorized code injection and attempts to bypass code review harder.

- **(c).** The lab requires a public repository because the branch-protection features used in this exercise are available for public repositories on GitHub Free under the lab's stated conditions. A public repository also allows the instructor and team members to access and review the work.

