External subtrees
=================

This directory contains external repositories managed via `git subtree`.

To update an external subtree, run the following command:

```bash
git subtree pull --prefix <path> <remote> <branch> --squash
```

You must first add the remote for each external repository.

## List of external repositories

| Remote       | Path             | Url                                          | Branch |
| ------------ | ---------------- | -------------------------------------------- | ------ |
| `hugr-mlir`  | `ext/hugr-mlir`  | `git@github.com:CQCL/hugr-mlir.git`          | `main` |
| `qir-runner` | `ext/qir-runner` | `git@github.com:qir-alliance/qir-runner.git` | `main` |

Add these remotes with the following commands:

```bash
git remote add <remote> <url>
```