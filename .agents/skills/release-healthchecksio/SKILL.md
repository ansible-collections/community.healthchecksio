---
name: release-healthchecksio
description: Merge, publish, and verify community.healthchecksio collection releases. Use in this repository when asked to merge a release-ready PR, cut or publish a release, monitor Ansible Zuul, verify Ansible Galaxy, create the GitHub release, close linked issues, or perform the post-release development-version bump.
---

# Release Healthchecks.io

Follow `RELEASE.md` as the authoritative runbook. Complete the whole lifecycle; do not stop after merging, tagging, or creating a GitHub release.

## Invariants

- Publish only from `ansible-collections/community.healthchecksio`.
- Require a clean worktree and a fully green current PR SHA before merging.
- Use a plain annotated `X.Y.Z` tag. Never prefix the tag with `v`.
- Let Ansible Zuul publish the `community` namespace artifact. Never run `ansible-galaxy collection publish` and never add a repository publication workflow.
- Generate and consume changelog fragments in a release-preparation PR before tagging.
- Create the GitHub release only after Galaxy lists and installs the version.
- Do not treat intentionally skipped duplicate `pull_request_target` jobs as failures.
- Preserve user work and use explicit force-with-lease protection if a reviewed branch must be rewritten.

## 1. Establish The Release

1. Read `RELEASE.md`, `galaxy.yml`, the pending changelog fragments, and the latest release.
2. Derive the release version from the development version unless the user supplied one. For `X.Y.Z-dev0`, release `X.Y.Z`.
3. Inspect the target PR, linked issues, mergeability, review state, head SHA, and every check.
4. Refresh the check state immediately before merge. Stop for failures, pending required checks, unresolved review feedback, or a dirty worktree.

## 2. Merge The Feature PR

1. Merge using a repository-permitted method and delete the remote feature branch. Prefer a merge commit when allowed; otherwise use squash merge and preserve one atomic commit.
2. Fetch `origin`, switch to `main`, and fast-forward to the exact remote merge commit.
3. Verify the PR is merged and the expected files, fragment, development version, and skill are present on `main`.
4. Close linked issues only when the merged work fully satisfies them and GitHub did not close them automatically.

## 3. Prepare The Release

1. Create `release/X.Y.Z` from current `origin/main`.
2. Change `galaxy.yml` from `X.Y.Z-dev0` to `X.Y.Z`.
3. Run:

   ```bash
   uv run antsibull-changelog lint
   uv run antsibull-changelog release --version X.Y.Z
   ```

4. Confirm `CHANGELOG.rst` and `changelogs/changelog.yaml` contain the release, the release date is correct, and consumed fragments are deleted.
5. Validate the release tree:

   ```bash
   git diff --check
   uv run antsibull-changelog lint
   ansible-galaxy collection build --force
   ```

6. Install the built tarball into a temporary isolated path and verify its embedded `galaxy.yml` version.
7. Commit as `chore: prepare X.Y.Z release`, push, and open a release PR with summary, changelog, validation, and post-deploy verification.
8. Wait for every required check, approve the protected integration environment when authorized, fix failures, and merge the release PR.

## 4. Tag And Publish

1. Fetch and verify `origin/main` contains the merged release PR and `galaxy.yml` says exactly `X.Y.Z`.
2. Create the tag at that exact commit:

   ```bash
   git tag -a X.Y.Z <release-commit> -m "community.healthchecksio: X.Y.Z"
   git push origin X.Y.Z
   ```

3. Monitor the Ansible Zuul release pipeline and poll the Galaxy v3 API until `X.Y.Z` appears:

   ```text
   https://galaxy.ansible.com/api/v3/plugin/ansible/content/published/collections/index/community/healthchecksio/versions/
   ```

4. If Zuul fails, follow the retry procedure in `RELEASE.md`. Recreate the same plain annotated tag at the same commit. Do not retry more than three times without escalating to Ansible community infrastructure.
5. Install `community.healthchecksio:==X.Y.Z` from Galaxy into a fresh temporary path and verify the installed metadata version.

## 5. Create The GitHub Release

1. Create a non-draft, non-prerelease GitHub release using tag and title `X.Y.Z`.
2. Summarize user-visible changes, call out breaking changes prominently, and link to the tagged `CHANGELOG.rst` section.
3. Verify the release URL, tag target, publication state, and Galaxy availability.

## 6. Restore Development State

1. Select the next patch development version, normally `X.Y.(Z+1)-dev0`.
2. Create `chore/bump-X.Y.(Z+1)-dev0` from current `origin/main`.
3. Update only `galaxy.yml`, validate YAML, exact version, and `git diff --check`.
4. Commit, push, open a PR, wait for required checks, and merge it.
5. Verify `origin/main` now reports the development version and no release tag exists for it.

## 7. Final Verification

Do not report completion until fresh evidence confirms all of the following:

- Feature PR and release PR are merged.
- The plain annotated tag points to the release merge commit.
- Galaxy lists and installs `X.Y.Z`.
- The GitHub release is published and links to the tagged changelog.
- Linked completed issues are closed.
- The post-release bump PR is merged.
- `origin/main` contains the next `-dev0` version.
- Required checks on the final main commit are green.

Report the feature PR, release PR, GitHub release, Galaxy version, post-release bump PR, final main version, and any intentionally skipped duplicate-event checks.
