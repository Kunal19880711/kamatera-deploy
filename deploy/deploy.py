#!/usr/bin/env python3

import os
import subprocess

dhparam_dir = "dhparam"
dhparam_file = os.path.join(dhparam_dir, "dhparam-2048.pem")
repos = [{
    "url": "https://github.com/Kunal19880711/scalarchatterbox.git",
    "dir": "scalarchatterbox"
}, {
    "url": "https://github.com/Kunal19880711/whisperhub.git",
    "dir": "whisperhub"
}]


def generate_dhparam():
    """
    Generates a 2048-bit Diffie-Hellman parameter file in the
    'dhparam' directory if it does not already exist.

    The file is used to configure the SSL/TLS server to use a
    secure Diffie-Hellman group.
    """
    if not os.path.exists(dhparam_file):
        os.makedirs(dhparam_dir, exist_ok=True)
        subprocess.run(["openssl", "dhparam", "-out", dhparam_file, "2048"],
                       check=True)


def clone_or_pull_repos():
    """
    Clones or pulls the latest version of the repositories from
    the given config.

    If the repository has already been cloned, it will be
    pulled instead.
    """
    for repo_config in repos:
        if not os.path.exists(repo_config["dir"]):
            subprocess.run(["git", "clone", repo_config["url"]], check=True)
        else:
            subprocess.run(["git", "pull"], cwd=repo_config["dir"], check=True)


def create_letsencrypt_dir():
    """
    Creates a 'letsencrypt' directory in the current working
    directory if it does not already exist.

    This is used to store Let's Encrypt related files.
    """
    letsencrypt_dir = os.path.join(os.getcwd(), "letsencrypt")
    if not os.path.exists(letsencrypt_dir):
        os.makedirs(letsencrypt_dir, exist_ok=True)


def restart_docker_compose():
    """
    Restarts the Docker Compose services.

    This function removes all existing Docker Compose services
    and starts them again in detached mode. This is useful for
    re-deploying the application after making changes to the
    Docker Compose configuration file.
    """
    subprocess.run(["docker", "compose", "rm", "-fsv"], check=True)
    subprocess.run(["docker", "compose", "up", "-d"], check=True)


def prune_docker_system():
    """
    Removes unused Docker images, volumes, networks and build cache.

    This function uses the Docker "system prune" command to remove
    unused Docker resources. The "-af" flags are used to remove all
    unused resources (not just those that are dangling) and to force
    the deletion without prompting the user for confirmation.
    """
    subprocess.run(["docker", "system", "prune", "-af"], check=True)


def ensure_correct_dir():
    """
    Changes the current working directory to the parent directory
    of the script's location. This ensures that the script is
    executed with the correct working directory context.
    """
    os.chdir(
        os.path.abspath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")))


def main():
    """
    Deploys the application in a Docker container using Docker Compose.

    This involves generating a Diffie-Hellman parameter file, cloning the
    repository, creating the 'letsencrypt' directory, restarting the
    Docker Compose service, and pruning the Docker system.
    """
    generate_dhparam()
    clone_or_pull_repos()
    create_letsencrypt_dir()
    restart_docker_compose()
    prune_docker_system()


if __name__ == "__main__":
    ensure_correct_dir()
    main()
