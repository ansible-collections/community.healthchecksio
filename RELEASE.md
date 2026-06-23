# Releasing `community.healthchecksio`

This collection follows the [Ansible community release process for collections without release branches](https://docs.ansible.com/ansible/latest/community/collection_contributors/collection_release_without_branches.html).

## Backfill missing Galaxy versions (issue #52)

Versions **1.3.2**, **1.4.0**, **1.5.0**, and **1.5.1** exist as GitHub tags and releases but were **never published to Ansible Galaxy** because they were tagged with a `v` prefix (`v1.3.2`, …). Zuul only publishes plain **`X.Y.Z`** tags for `community.*` collections.

**Do not** try to backfill with `ansible-galaxy collection publish` or a GitHub Actions workflow. Manual Galaxy publish requires **`community` namespace owner** permissions. Collection maintainers do not have that access ([issue #52](https://github.com/ansible-collections/community.healthchecksio/issues/52)).

The fix is to delete the `v`-prefixed tags, recreate them as plain semver tags at the **same commits**, push, and let Zuul publish.

### Procedure (run oldest to newest)

For each missing version, repeat these steps. Example uses **1.3.2**; substitute the version for 1.4.0, 1.5.0, and 1.5.1.

1. **Record the commit** the existing tag points to (before deleting anything):

   ```bash
   git fetch origin --tags
   COMMIT=$(git rev-parse v1.3.2^{commit})
   echo "${COMMIT}"
   ```

2. **Delete the `v`-prefixed tag** locally and on GitHub:

   ```bash
   git tag -d v1.3.2
   git push origin :refs/tags/v1.3.2
   ```

3. **Delete the GitHub Release** for `v1.3.2` (Releases → delete). Zuul does not need the release; recreating it prematurely confuses users when Galaxy still lacks the version.

4. **Create and push a plain tag** at the same commit:

   ```bash
   git tag -a 1.3.2 "${COMMIT}" -m "community.healthchecksio: 1.3.2"
   git push origin 1.3.2
   ```

5. **Watch Zuul** until the release job succeeds:

   - [Ansible Content CI dashboard](https://ansible.softwarefactory-project.io/zuul/status) — filter for `community.healthchecksio`.

6. **Verify Galaxy** lists the version:

   ```bash
   curl -sS 'https://galaxy.ansible.com/api/v3/plugin/ansible/content/published/collections/index/community/healthchecksio/versions/' \
     | python3 -c "import sys,json; print([v['version'] for v in json.load(sys.stdin)['data']])"
   ```

   Or install it:

   ```bash
   ansible-galaxy collection install 'community.healthchecksio:==1.3.2'
   ```

7. **Recreate the GitHub Release** only after Galaxy confirms the version (tag `1.3.2`, title `1.3.2`, body pointing at [CHANGELOG.rst](CHANGELOG.rst)).

8. Proceed to the next version (**1.4.0** → **1.5.0** → **1.5.1**).

### If Zuul fails three times

Delete the plain tag and push it again at the same commit (Zuul retry guidance from Ansible community infra):

```bash
git push origin :refs/tags/1.3.2
git tag -a 1.3.2 "${COMMIT}" -m "community.healthchecksio: 1.3.2"
git push origin 1.3.2
```

If failures persist, ask in Matrix `#community` (for example `@gundalow` or `@felixfontein`).

## Tag format (required)

Official `community.*` collections are published to Galaxy **only** by **Zuul** when a tag is pushed to the upstream repository.

| Tag format | Zuul publishes to Galaxy? |
|------------|---------------------------|
| `X.Y.Z` (for example `1.5.2`) | Yes |
| `vX.Y.Z` (for example `v1.5.2`) | **No** |

Use annotated tags (`git tag -a`). See [upstream docs](https://docs.ansible.com/ansible/latest/community/collection_contributors/collection_release_without_branches.html#publish-the-collection).

Older releases in this repo mixed both styles (`1.3.1` vs `v1.4.0`). All **new** releases must use plain semver.

## Why manual publish and GitHub Actions do not work here

- **`ansible-galaxy collection publish`** for `community.healthchecksio` requires a Galaxy API token whose owner has **`galaxy.collection_namespace_owner_namespace`** on the shared [`community` namespace](https://galaxy.ansible.com/ui/namespaces/community/). Repository maintainers are not automatically namespace owners.
- **Repository GitHub Actions** cannot substitute for Zuul unless someone with namespace-owner credentials adds a `GALAXY_API_KEY` secret — that is infrastructure-owned, not a maintainer self-service path.

Coordinate with Ansible community infrastructure in `#community` if Zuul itself is broken; do not add collection-local publish workflows that imply maintainers can publish directly.

## Standard release checklist

For each **new** release after backfill is complete:

1. Announce the release in the collection pinboard / Matrix `#community` channel.
2. Bump `galaxy.yml` `version` and generate the changelog (`uv run antsibull-changelog release --version X.Y.Z`).
3. Merge the release PR to `main`.
4. Tag the release commit as **`X.Y.Z`** (no `v` prefix) and push to `origin` (`ansible-collections/community.healthchecksio`).
5. Watch [Zuul](https://ansible.softwarefactory-project.io/zuul/status) and confirm the version appears on [Ansible Galaxy](https://galaxy.ansible.com/ui/repo/published/community/healthchecksio/).
6. Create a GitHub Release from the tag (title = version, body links to [CHANGELOG.rst](CHANGELOG.rst)).
7. Bump `galaxy.yml` on `main` to the next development version.

## After publishing

- Confirm install works: `ansible-galaxy collection install 'community.healthchecksio:==X.Y.Z'`
- Announce in `#social` on Matrix (mention `@newsbot` for the Bullhorn newsletter).
