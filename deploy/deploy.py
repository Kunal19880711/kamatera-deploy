#!/usr/bin/env python3

import os
import subprocess

repo_url = "https://github.com/Kunal19880711/scalarchatterbox.git"
repo_dir = "scalarchatterbox"
dhparam_dir = "dhparam"
dhparam_file = os.path.join(dhparam_dir, "dhparam-2048.pem")

def generate_dhparam():
    if not os.path.exists(dhparam_file):
        os.makedirs(dhparam_dir, exist_ok=True)
        subprocess.run(["openssl", "dhparam", "-out", dhparam_file, "2048"], check=True)

def clone_or_pull_repo():
    if not os.path.exists(repo_dir):
        subprocess.run(["git", "clone", repo_url], check=True)
    else:
        subprocess.run(["git", "pull"], cwd=repo_dir, check=True)

def restart_docker_compose():
    subprocess.run(["docker", "compose", "rm", "-fsv"], check=True)
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
    
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

def main():
    generate_dhparam()
    clone_or_pull_repo()
    restart_docker_compose()

if __name__ == "__main__":
    ensure_correct_dir()
    main()