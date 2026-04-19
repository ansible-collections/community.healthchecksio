from __future__ import absolute_import, division, print_function

"""Render tests/integration/integration_config.yml for self-hosted CI."""

import os
from io import open


def main():
    with open("/tmp/hc_ci_key.txt", encoding="utf-8") as file_obj:
        api_key = file_obj.read().strip()
    host = os.environ.get("HC_TEST_HOST", "127.0.0.1").strip()
    with open("tests/integration/integration_config.yml.template", encoding="utf-8") as file_obj:
        content = file_obj.read()
    content = content.replace(
        "${MANAGEMENT_API_TOKEN:-$HEALTHCHECKSIO_API_TOKEN}", api_key
    )
    content = content.replace(
        '${MANAGEMENT_API_BASE_URL:-"https://healthchecks.io/api/v1"}',
        "http://{0}:8000/api/v1".format(host),
    )
    content = content.replace(
        '${PING_API_BASE_URL:-"https://hc-ping.com"}',
        "http://{0}:8000/ping".format(host),
    )
    content = content.replace('${PING_API_TOKEN:-""}', "")
    with open("tests/integration/integration_config.yml", "w", encoding="utf-8") as file_obj:
        file_obj.write(content)


if __name__ == "__main__":
    main()
