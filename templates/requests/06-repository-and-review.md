# Request: a repository and review rules for walk-through specs

**To:** <engineering or platform team>

## What we need

1. A repository (`<org>/<repo>`) for the specs, with read access for <teams> and write access for <authors>.
2. Branch protection on the main branch:
   - changes only through pull requests;
   - the automatic checks must pass: `demoshark check` on every spec, the test suite, and a captions-only recording;
   - **one approval from the owner of the process** that a spec describes, in addition to the author.
3. A CODEOWNERS file that maps each folder of specs to its process owner.

## Why

The spec is the single source of the video, the deck and the guide. Reviewing a one-line change to a spec reviews all three outputs at once, and the history records who changed what, when and why.
