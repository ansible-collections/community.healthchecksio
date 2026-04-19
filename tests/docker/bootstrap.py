#!/usr/bin/env python3
"""
Bootstrap a self-hosted Healthchecks instance for CI testing.

Creates a superuser and project with read-write API key.
Writes the raw API key to --api-key-output.

Usage:
    docker-compose -f tests/docker/docker-compose.yml up -d
    python3 tests/docker/bootstrap.py --api-key-output /tmp/api_key.txt
    docker-compose -f tests/docker/docker-compose.yml down -v
"""

import argparse
import os
import subprocess
import sys
import time


def wait_for_healthy(url: str, timeout: int = 120) -> None:
    """Block until the Healthchecks instance responds."""
    import urllib.request
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            req = urllib.request.Request(url + "/static/img/favicon.png")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError(f"Healthchecks not healthy at {url} after {timeout}s")


def docker_exec(service: str, *args: str, input: bytes = b"") -> bytes:
    cmd = ["docker", "exec", "-i", service] + list(args)
    result = subprocess.run(cmd, input=input, capture_output=True)
    return result.stdout + result.stderr


def main() -> None:
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
    print(f"Healthchecks is healthy at {hc_url}", file=sys.stderr)

    # Determine the actual container name
    result = subprocess.run(
        [
            "docker", "ps", "--filter", f"name={args.project_name}_{args.service_name}",
            "--format", "{{.Names}}",
        ],
        capture_output=True,
        text=True,
    )
    container_names = [n for n in result.stdout.strip().split("\n") if n]
    if not container_names:
        # Fallback: try just the service name
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={args.service_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
        )
        container_names = [n for n in result.stdout.strip().split("\n") if n]

    if not container_names:
        print("Error: could not find running Healthchecks container", file=sys.stderr)
        sys.exit(1)

    container = container_names[0]
    print(f"Using container: {container}", file=sys.stderr)

    # 1. Create superuser
    result = subprocess.run(
        ["docker", "exec", "-i", container,
         "python", "manage.py", "createsuperuser",
         "--noinput", f"--email={superuser_email}"],
        input=superuser_password.encode(),
        capture_output=True,
    )
    if result.returncode != 0 and b"already exists" not in result.stderr.lower() and b"duplicate" not in result.stderr.lower():
        print(f"Warning: createsuperuser: {result.stderr.decode()}", file=sys.stderr)
    else:
        print(f"Superuser {superuser_email} ready", file=sys.stderr)

    # 2. Create project + API key via Django shell
    setup_script = (
        f"import os\n"
        f"os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hc.settings')\n"
        f"import django\n"
        f"django.setup()\n"
        f"from hc.accounts.models import Project\n"
        f"from django.contrib.auth import get_user_model\n"
        f"User = get_user_model()\n"
        f"email = '{superuser_email}'\n"
        f"user, _ = User.objects.get_or_create(\n"
        f"    email=email, defaults={{'username': email.split('@')[0]}}\n"
        f")\n"
        f"project = Project.objects.create(owner=user, name='CI Test Project')\n"
        f"raw_key = project.set_api_key()\n"
        f"project.save()\n"
        f"print(raw_key)\n"
    )

    result = subprocess.run(
        ["docker", "exec", "-i", container, "python", "manage.py", "shell", "-c", setup_script],
        capture_output=True,
    )
    if result.returncode != 0:
        print(f"Error creating API key: {result.stderr.decode()}", file=sys.stderr)
        sys.exit(1)

    api_key = result.stdout.strip().split(b"\n")[-1].decode().strip()
    if not api_key:
        print(f"Error: empty API key. stdout: {result.stdout}", file=sys.stderr)
        sys.exit(1)

    with open(args.api_key_output, "w") as f:
        f.write(api_key + "\n")

    print(f"Bootstrap complete. API key written to {args.api_key_output}", file=sys.stderr)


if __name__ == "__main__":
    main()
