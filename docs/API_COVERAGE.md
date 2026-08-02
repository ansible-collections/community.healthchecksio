# Healthchecks.io API Coverage

Last audited: 2026-08-01

This collection targets the current [Management API v3](https://healthchecks.io/docs/api/) and [Pinging API](https://healthchecks.io/docs/http_api/). The default management base URL is `https://healthchecks.io/api/v3`; self-hosted installations can override it with `management_api_base_url`.

## Management API v3

| API operation | Collection coverage |
| --- | --- |
| List checks; filter by slug or repeated tags | `checks_info` |
| Get a check by UUID or read-only `unique_key` | `checks_info` |
| Create a simple, cron, or systemd `OnCalendar` check | `checks` with `state: present` |
| Upsert by name, slug, tags, timeout, or grace | `checks` with `unique` |
| Update a specific check | `checks` with `state: present` and `uuid` |
| Configure integrations and all documented keyword filters | `checks` |
| Pause monitoring | `checks` with `state: pause` |
| Resume monitoring | `checks` with `state: resume` |
| Delete a check | `checks` with `state: absent` |
| List logged pings | `checks_pings_info` |
| Get a logged ping body | `checks_ping_body_info` |
| List status flips by UUID or `unique_key` | `checks_flips_info` |
| Filter flips by seconds or UNIX timestamp range | `checks_flips_info` |
| List integrations | `channels_info` |
| List project badges | `badges_info` |
| Check database connectivity | `status_info` |

## Pinging API

| API operation | Collection coverage |
| --- | --- |
| Identify checks by UUID | `ping.uuid` |
| Identify checks by project ping key and slug | `ping.slug` and `ping_api_token` |
| Send success, start, failure, and log events | `ping.signal` |
| Report process exit status 0 through 255 | `ping.exit_status` |
| Associate events using a run ID | `ping.runid` |
| Store diagnostic request bodies | `ping.body` |
| Select HEAD, GET, or POST | `ping.method` |
| Automatically create a missing slug check | `ping.create` |

## Verification

Endpoint behavior is covered by unit tests, Ansible module validation, and the `api_v3` integration target against both Healthchecks.io and the repository's self-hosted Healthchecks container. When the upstream API documentation changes, update this matrix, the corresponding module documentation, and integration coverage in the same pull request.
