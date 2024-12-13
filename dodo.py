# dodo.py

import subprocess

container_name = "webserver1"


def rsync(source, destination, excludes):
    """
    Synchronizes the contents of the source directory to the destination
    directory, preserving symlinks and permissions, using the rsync
    command-line tool.

    source: The source directory to be synchronized.
    destination: The destination directory to be synchronized to.
    excludes: A list of strings, each of which starts with "--exclude=".
              These are passed directly to the rsync command-line tool.
    """
    args = ["rsync", "-avz", "--delete"]
    args.extend(excludes)
    args.extend([source, destination])
    subprocess.run(args)


def sync_deployment():
    """
    Synchronizes the current directory with the remote directory at
    83-229-3-134.cloud-xip.com:/home/ubuntu/apps/kamatera-deploy using
    rsync. This script is for deploying to the Kamatera Docker environment.

    The following files and directories are excluded from synchronization:
    - .doit.db.*
    - .git
    - .gitignore
    - dodo.py
    - dhparam
    - kamatera-deploy.code-workspace
    - letsencrypt
    - __pycache__
    - README.md
    - scalarchatterbox
    - whisperhub
    """
    source = "."
    destination = "83-229-3-134.cloud-xip.com:/home/ubuntu/apps/kamatera-deploy"
    excluded = [
        "dhparam",
        "dodo.py",
        ".doit.db.*",
        ".git",
        ".gitignore",
        "kamatera-deploy.code-workspace",
        "letsencrypt",
        "__pycache__",
        "README.md",
        "scalarchatterbox",
        "whisperhub",
    ]
    excludes = [f"--exclude={item}" for item in excluded]
    rsync(source, destination, excludes)


def task_build_nginx():
    """Task to build the Docker image."""
    return {
        "actions": [
            "docker build -t nginx-certbot nginx-certbot",
            lambda: True,  # Ensures the task always runs
        ],
        "file_dep": ["nginx-certbot/Dockerfile"],
        "uptodate": [False],  # Forces the task to always run
    }


def task_cleanup():
    """Task to stop and remove the webserver1 container."""
    return {
        "actions":
        ["docker stop %s" % container_name,
         "docker rm %s" % container_name]
    }


def task_run_nginx():
    """Task to run the nginx-certbot Docker container."""
    task = " ".join([
        "docker run -d --name %s -p 80:80 -p 443:443",
        "-v ./letsencrypt/:/etc/letsencrypt -v ./dhparam/:/etc/ssl/certs",
        "-v ./config.yaml:/opt/nginx-certbot/config.yaml",
        "-v ./nginx-certbot/bin:/opt/nginx-certbot/bin",
        "--restart unless-stopped",
        "--entrypoint /bin/sh -- nginx-certbot -c 'tail -f /dev/null'"
    ]) % container_name
    return {
        "actions": [task],
        "file_dep": ["nginx-certbot/Dockerfile"],
        "uptodate": [False],  # Ensures the task always runs
    }


def task_sync():
    """Task to run the sync_deployment function."""
    return {
        "actions": [sync_deployment],
    }
