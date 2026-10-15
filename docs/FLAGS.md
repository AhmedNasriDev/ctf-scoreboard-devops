# Flags for the demonstration competition

These are the flags, in clear text, behind the hashes in
`data/challenges.yaml`. You use them to test the service while you work. Also,
`tools/smoke.sh` needs a flag to submit.

| Challenge | Category | Base points | Flag |
|---|---|---|---|
| `warmup-banner` | misc | 100 | `UEM9{read_the_banner}` |
| `rot-thirteen` | crypto | 200 | `UEM9{caesar_salad_with_13_croutons}` |
| `leaky-headers` | web | 300 | `UEM9{x_powered_by_too_much}` |
| `stack-the-deck` | pwn | 400 | `UEM9{off_by_one_off_by_all}` |
| `carved-out` | forensics | 350 | `UEM9{the_filesystem_remembers}` |
| `the-long-game` | crypto | 500 | `UEM9{patience_is_a_side_channel}` |

## Why these flags are public, and what you can learn from this

A real competition does not publish this file. Here, the flags are public
because this application is for teaching. There is nothing to win, and you
need input that works.

But look at how the application protects the flags. It stores only
`sha256(flag)`, never the flag itself. Imagine that an attacker gets a copy of
the database. For example: a backup that everybody can read, an admin endpoint
with a wrong configuration, or an SQL injection. The attacker then gets the
hashes, not the flags.

This protection is weaker than it looks. You must be able to explain why:

- the flags are short and follow a pattern: they all start with `UEM9{`;
- they are lower-case words joined by underscores;
- the title of the challenge gives a hint about the content.

So an attacker can guess them. A SHA-256 hash without salt of such a text
breaks with a dictionary attack in a few seconds. Here, the hash makes a copy
of the database a little more difficult to use, instead of free. It is not a
safe place for secrets.

A correct solution uses a slow function with salt that needs a lot of memory,
like Argon2id or bcrypt. You use these functions for passwords. For a flag,
this is too much, for this reason: a password protects an account for an
unlimited time. A flag protects a result only during one competition. After
the competition, the answers are published anyway.

To add your own challenges, edit `data/challenges.yaml`. While you test, use
`flag:` with the flag in clear text. When the file is in Git, use
`flag_sha256:` instead:

```bash
printf '%s' 'UEM9{your_flag_here}' | sha256sum
```
