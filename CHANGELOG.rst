=======================================
Community Healthchecks.io Release Notes
=======================================

.. contents:: Topics

### [Unreleased]

### Added

- Support for using a private instance of Healthchecks.io

v1.2.0
======

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
