=======================================
Community Healthchecks.io Release Notes
=======================================

.. contents:: Topics

v1.5.1
======

Bugfixes
--------

- badges_info, channels_info, checks_flips_info, checks_info, and checks_pings_info perform read-only GET requests in check mode instead of returning empty data (https://github.com/ansible-collections/community.healthchecksio/issues/34).

v1.5.0
======

Minor Changes
-------------

- checks_info - Add optional ``name`` filter when listing checks; values sent to the API are URL-encoded.

Bugfixes
--------

- checks - Declare ``supports_diff_mode`` in a form compatible with Ansible 2.9.
- checks - Fix idempotency when comparing ``grace`` for Cron checks if the API omits or returns ``null`` for ``grace`` while the module applies a default.
- plugins/module_utils - Add legacy metaclass boilerplate for current ``ansible-test sanity`` expectations.

v1.4.0
======

Minor Changes
-------------

- healthchecksio.checks - Add ``management_api_token`` (with ``api_key`` alias) and ``ping_api_token`` for separate management/ping token support.
- healthchecksio.checks - Add diff_mode support (returns ``before``/``after`` state on create/update).
- healthchecksio.checks - Add support for self-hosted Healthchecks.io instances via ``management_api_base_url`` and ``ping_api_base_url`` parameters.
- healthchecksio.checks - Fix idempotency comparison to include the ``tags`` field.
- healthchecksio.checks - Proper check_mode support (delete/pause report would-be changes instead of silently exiting early).

v1.3.2
======

Bugfixes
--------

- Replace deprecated ``ansible.module_utils._text`` import with ``ansible.module_utils.common.text.converters`` (https://github.com/ansible-collections/community.healthchecksio/pull/46).

v1.3.1
======

Bugfixes
--------

- checks - channel comparison result was order dependent. Fix now compares channels lists as sets (https://github.com/ansible-collections/community.healthchecksio/pull/35).

v1.3.0
======

Release Summary
---------------

Implement idempotency when unique param is used in checks.

Minor Changes
-------------

- checks - implement idempotency when unique param is used (https://github.com/ansible-collections/community.healthchecksio/issues/28)

v1.2.0
======

Release Summary
---------------

Restoring the C(grace) parameter to Cron checks and adding Ansible 2.13 to sanity and unit testing.

Minor Changes
-------------

- ci - adding stable-2.13 to sanity and unit testing (https://github.com/ansible-collections/community.healthchecksio/issues/22).

Bugfixes
--------

- checks - restore C(grace) parameter to Cron checks (https://github.com/ansible-collections/community.healthchecksio/issues/24).

v1.1.1
======

Release Summary
---------------

Adding support for Simple checks.

Breaking Changes / Porting Guide
--------------------------------

- checks - support creating Simple checks. Previously, C(schedule) and C(tz) were defaulted which made it impossible to differentiate between Simple and Cron checks when creating them. Now, either C(schedule) and C(tz) must be provided to create a Cron check, or, C(timeout) must be provided to create a Simple check (https://github.com/ansible-collections/community.healthchecksio/issues/16).

Bugfixes
--------

- Update the tests so that they only run once (https://github.com/ansible-collections/community.healthchecksio/issues/11).
- ping - remove C(default="") on required C(uuid) parameter (https://github.com/ansible-collections/community.healthchecksio/issues/19).

v0.1.1
======

Release Summary
---------------

Updating the README.md and switching the integration tests to GHAs (https://github.com/ansible-collections/community.healthchecksio/pull/9).

v0.1.0
======

New Modules
-----------

- badges_info - Get the project badges
- channels_info - Get a list of integrations
- checks - Create, delete, update, and pause checks
- checks_flips_info - Get a list of check flips
- checks_info - Get a list of checks
- checks_pings_info - Get a list of check pings
- ping - Signal success, fail, and start events
