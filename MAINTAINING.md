# Maintaining this collection

Refer to the [Maintainer guidelines](https://github.com/ansible/community-docs/blob/main/maintaining.rst).

## Changelog

With [uv](https://docs.astral.sh/uv/) installed, run `uv sync --group dev` once, then use `uv run antsibull-changelog …` (for example `uv run antsibull-changelog release --version X.Y.Z`).

## Releases and Ansible Galaxy

See **[RELEASE.md](RELEASE.md)** for the full release checklist, the Zuul re-tag backfill procedure for missing Galaxy versions, tag format rules, and troubleshooting.

Summary:

- **`community.*` collections publish to Galaxy only via Zuul** when a plain **`X.Y.Z`** tag (no `v` prefix) is pushed to upstream.
- Watch the [Ansible Content CI dashboard](https://ansible.softwarefactory-project.io/zuul/status) after pushing a tag.
- **Maintainers cannot publish manually** with `ansible-galaxy collection publish` or a repository workflow unless a `community` namespace owner provides infrastructure — that is not available to typical collection maintainers.
- Missing Galaxy versions caused by `v`-prefixed tags: follow the backfill steps in **RELEASE.md** (delete `v` tag, re-tag as `X.Y.Z`, verify Zuul/Galaxy, then recreate the GitHub release).
