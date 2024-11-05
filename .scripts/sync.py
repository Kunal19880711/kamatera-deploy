#!/usr/bin/env python3

import os
import subprocess

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
    excludes = ["--exclude=kamatera-deploy.code-workspace", "--exclude=.scripts", "--exclude=dhparam"]
    rsync(source, destination, excludes)
    
def ensure_correct_dir():
    """
    Changes the current working directory to the parent directory
    of the script's location. This ensures that the script is
    executed with the correct working directory context.
    """
    os.chdir(
        os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), 
                ".."
            )
        )
    )

if __name__ == "__main__":
    ensure_correct_dir()
    sync_deployment()

