#!/usr/bin/env python3
"""Render tests/integration/integration_config.yml for self-hosted CI."""

import os
from pathlib import Path


def main() -> None:
    api_key = Path("/tmp/hc_ci_key.txt").read_text(encoding="utf-8").strip()
    host = os.environ.get("HC_TEST_HOST", "127.0.0.1").strip()
    content = Path("tests/integration/integration_config.yml.template").read_text(
        encoding="utf-8"
    )
    content = content.replace(
        "${MANAGEMENT_API_TOKEN:-$HEALTHCHECKSIO_API_TOKEN}", api_key
    )
    content = content.replace(
        '${MANAGEMENT_API_BASE_URL:-"https://healthchecks.io/api/v1"}',
        f"http://{host}:8000/api/v1",
    )
    content = content.replace(
        '${PING_API_BASE_URL:-"https://hc-ping.com"}',
        f"http://{host}:8000/ping",
    )
    content = content.replace('${PING_API_TOKEN:-""}', "")
    Path("tests/integration/integration_config.yml").write_text(
        content, encoding="utf-8"
    )


if __name__ == "__main__":
    main()
