from __future__ import absolute_import, division, print_function

__metaclass__ = type

"""Bootstrap a self-hosted Healthchecks instance for CI testing.

Creates a superuser and project with read-write API key.
Writes the raw API key to --api-key-output.

Usage:
    docker compose -f tests/docker/docker-compose.yml up -d
    python3 tests/docker/bootstrap.py --api-key-output /tmp/api_key.txt
    docker compose -f tests/docker/docker-compose.yml down -v
"""

import argparse
import os
import subprocess
import sys
import time


def wait_for_healthy(hc_url, timeout=180):
    """Block until the Healthchecks instance responds."""
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            result = subprocess.run(
                ["curl", "-fsS", hc_url + "/api/v3/status/"],
                capture_output=True,
                text=False,
                check=False,
                timeout=5,
            )
            if result.returncode == 0:
                return
        except Exception:
            pass
        time.sleep(5)
    raise RuntimeError(
        "Healthchecks not healthy at {0} after {1}s".format(hc_url, timeout)
    )


def run_command(*args, **kwargs):
    input_data = kwargs.get("input_data")
    return subprocess.run(
        list(args),
        input=input_data,
        capture_output=True,
        text=False,
        check=False,
    )


def main():
    parser = argparse.ArgumentParser(description="Bootstrap Healthchecks for CI")
    parser.add_argument(
        "--project-name",
        default="tests-docker",
        help="docker-compose project name (default: tests-docker)",
    )
    parser.add_argument(
        "--api-key-output",
        required=True,
        help="Path to write the raw API key to",
    )
    parser.add_argument(
        "--service-name",
        default="web",
        help="Name of the web service in docker-compose (default: web)",
    )
    args = parser.parse_args()

    superuser_email = os.environ.get("HC_SUPERUSER_EMAIL", "ci@example.com")
    superuser_password = os.environ.get("HC_SUPERUSER_PASSWORD", "ci-password")

    hc_url = os.environ.get("HC_BASE_URL", "http://localhost:8000")
    wait_for_healthy(hc_url)
    print("Healthchecks is healthy at {0}".format(hc_url), file=sys.stderr)

    result = subprocess.run(
        [
            "docker",
            "ps",
            "--filter",
            "name={0}_{1}".format(args.project_name, args.service_name),
            "--format",
            "{{.Names}}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    container_names = [name for name in result.stdout.strip().split("\n") if name]
    if not container_names:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                "name={0}".format(args.service_name),
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        container_names = [name for name in result.stdout.strip().split("\n") if name]

    if not container_names:
        print("Error: could not find running Healthchecks container", file=sys.stderr)
        sys.exit(1)

    container = container_names[0]
    print("Using container: {0}".format(container), file=sys.stderr)

    result = run_command(
        "docker",
        "exec",
        "-i",
        container,
        "python",
        "manage.py",
        "createsuperuser",
        "--noinput",
        "--email={0}".format(superuser_email),
        input_data=superuser_password.encode(),
    )
    if (
        result.returncode != 0
        and b"already exists" not in result.stderr.lower()
        and b"duplicate" not in result.stderr.lower()
    ):
        print(
            "Warning: createsuperuser: {0}".format(result.stderr.decode()),
            file=sys.stderr,
        )
    else:
        print("Superuser {0} ready".format(superuser_email), file=sys.stderr)

    setup_script = (
        "import os\n"
        "import uuid\n"
        "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hc.settings')\n"
        "import django\n"
        "django.setup()\n"
        "from hc.accounts.models import Project\n"
        "from django.contrib.auth import get_user_model\n"
        "User = get_user_model()\n"
        + "email = '{0}'\n".format(superuser_email)
        + "user, _ = User.objects.get_or_create(\n"
        + "    email=email, defaults={'username': email.split('@')[0]}\n"
        + ")\n"
        + "project = Project.objects.create(owner=user, name='CI Test Project')\n"
        + "if hasattr(project, 'badge_key') and not project.badge_key:\n"
        + "    project.badge_key = uuid.uuid4().hex[:12]\n"
        + "raw_key = project.set_api_key()\n"
        + "project.save()\n"
        + "print(raw_key)\n"
    )

    result = run_command(
        "docker",
        "exec",
        "-i",
        container,
        "python",
        "manage.py",
        "shell",
        "-c",
        setup_script,
    )
    if result.returncode != 0:
        print(
            "Error creating API key: {0}".format(result.stderr.decode()),
            file=sys.stderr,
        )
        sys.exit(1)

    api_key = result.stdout.strip().split(b"\n")[-1].decode().strip()
    if not api_key:
        print(
            "Error: empty API key. stdout: {0}".format(result.stdout),
            file=sys.stderr,
        )
        sys.exit(1)

    with open(args.api_key_output, "w", encoding="utf-8") as file_obj:
        file_obj.write(api_key + "\n")

    print(
        "Bootstrap complete. API key written to {0}".format(args.api_key_output),
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
