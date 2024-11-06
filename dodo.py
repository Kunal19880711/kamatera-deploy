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
    83-229-3-134.cloud-xip.com:/home/ubuntu/apps/kamatera-deploy, using
    rsync.  This is the deployment script for the Kamatera Docker
    environment.

    The following files and directories are excluded from the
    synchronization:
    - .scripts
    - dhparam
    - kamatera-deploy.code-workspace
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
        "actions": ["docker stop %s" % container_name, "docker rm %s" % container_name]
    }


def task_sync():
    """Task to run the sync_deployment function."""
    return {
        "actions": [sync_deployment],
    }
