#!/opt/certbot/bin/python

import os
import subprocess
import time
import datetime
import socket
import traceback
from urllib.parse import urlparse
import yaml
from jinja2 import Template

sleep_in_secs = 60


def check_if_cert_exists(domain):
    """
    Checks if the SSL certificate and private key files exist for the specified domain.

    The function retrieves the domain from the environment variables and constructs
    the paths to the certificate and key files in the Let's Encrypt directory.
    It returns True if both files exist, indicating that the certificate is present,
    otherwise it returns False.
    """
    cert_file_path = os.path.join("/etc/letsencrypt/live", domain,
                                  "fullchain.pem")
    cert_key_file_path = os.path.join("/etc/letsencrypt/live", domain,
                                      "privkey.pem")
    return os.path.exists(cert_file_path) and os.path.exists(
        cert_key_file_path)


def check_if_dhparam_available():
    """
    Checks if the dhparam file exists in the /etc/ssl/certs directory.
    """
    dhparam_file_path = "/etc/ssl/certs/dhparam-2048.pem"
    return os.path.exists(dhparam_file_path)


def check_server_active(url):
    """
    Checks if the server is active by attempting to resolve the hostname
    specified in the URL to an IP address. If the hostname is resolvable, it
    indicates that the server is active and running. If the hostname is not
    resolvable, it indicates that the server is not running.

    Returns:
        bool: True if the server is active, False otherwise.
    """
    parsed_url = urlparse(url)
    host, port = parsed_url.netloc.split(":")
    port = int(port)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)  # set a timeout of 1 second
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Exception occurred while checking if server is active: {e}")
        return False


def check_nginx_conf_change(file_path, new_conf):
    """
    Reads the contents of the nginx.conf file.
    """
    if not os.path.exists(file_path):
        return True

    with open(file_path) as nginx_conf_file:
        old_conf = nginx_conf_file.read()

    return old_conf != new_conf


def set_nginx(config):
    """
    Configures the nginx server to use the SSL certificate for the specified domain
    or disable HTTPS if the certificate is not present.

    The function takes a boolean parameter indicating the presence of the SSL certificate
    and key files for the specified domain. It sets up the nginx server to use the
    certificate and key files or disable HTTPS if the certificate is not present.

    It renders the nginx configuration template from the nginx-tmpl directory with
    the domain and enable_https data, and writes the rendered template to the
    /etc/nginx/conf.d/nginx.conf file. Finally, it reloads the nginx server configuration.
    """
    tmpl_file_path = os.path.join("nginx-tmpl", "nginx.conf.jinja")
    nginx_conf_path = os.path.abspath("/etc/nginx/conf.d/nginx.conf")
    is_dhparam_available = check_if_dhparam_available()

    for domain_config in config["domains"]:
        domain_config["is_server_active"] = check_server_active(
            domain_config["server"])

    data = {
        "is_dhparam_available": is_dhparam_available,
        "domains": config["domains"]
    }
    print(data)

    with open(tmpl_file_path) as tmpl_file:
        template = Template(tmpl_file.read())

    new_conf = template.render(data)

    if check_nginx_conf_change(nginx_conf_path, new_conf):
        with open(nginx_conf_path, "w") as nginx_conf_file:
            nginx_conf_file.write(new_conf)
        subprocess.run(["nginx", "-s", "reload"], check=True)


def check_certificate_validity():
    """
    Check if the current certificate is valid using Certbot.
    """
    try:
        # Run Certbot command to check certificate validity
        output = subprocess.check_output(["certbot", "certificates"])
        # Parse output to get certificate expiration date
        for line in output.decode("utf-8").splitlines():
            if "Expires" in line:
                expiration_date = line.split(":")[1].strip()
                # Check if certificate is valid (i.e., not expired)
                expiration_date = datetime.datetime.strptime(
                    expiration_date, "%Y-%m-%d %H:%M:%S%z")
                if expiration_date > datetime.datetime.now():
                    return True

        return False
    except subprocess.CalledProcessError as e:
        print(f"Error checking certificate validity: {e}")
        return False


def renew_cert(email):
    """
    Renews the SSL certificate for the domains that need certificate renewal using Certbot.

    The --non-interactive flag is used to prevent Certbot from asking user
    questions. The --agree-tos flag is used to agree to the terms of service.
    The --email flag is used to specify the contact email address for the
    certificate.

    The function runs the Certbot renew command with the given flags and
    checks the return code of the command. If the command fails, the function
    raises a CalledProcessError exception.
    """
    subprocess.run(
        [
            "certbot",
            "renew",
            "-n",
            "--agree-tos",
            "--email",
            email,
        ],
        check=True,
    )


def obtain_cert(email, domains):
    """
    Obtains the SSL certificate for the domains needed certificate using Certbot.

    The --nginx flag is used to configure the Nginx web server.
    The --non-interactive flag is used to prevent Certbot from asking user
    questions. The --agree-tos flag is used to agree to the terms of service.
    The --email flag is used to specify the contact email address for the
    certificate.

    The function runs the Certbot certonly command with the given flags and
    checks the return code of the command. If the command fails, the function
    raises a CalledProcessError exception.
    """
    args = [
        "certbot",
        "certonly",
        "--nginx",
        "--email",
        email,
        "--agree-tos",
        "-n",
        "--no-eff-email",
    ]
    for domain in domains:
        args.extend([
            "-d",
            domain,
            "-d",
            "www." + domain,
        ])
    subprocess.run(
        args=args,
        check=True,
    )


def setup_certs(config):
    """
    Sets up the SSL certificates for the specified domains.

    This function checks if the SSL certificates and key files exist for each domain.
    If the certificates and key files exist, it sets up the Nginx server to use them.
    If the certificates and key files do not exist, it runs the Certbot certonly command to
    obtain the certificates and sets up the Nginx server to use them.

    It also checks the validity of the certificates and renews them if they are not valid.
    """
    domains_need_cert = []
    for domain_config in config["domains"]:
        domain_config["is_cert_exists"] = check_if_cert_exists(
            domain_config["domain"])
        if not domain_config["is_cert_exists"]:
            domains_need_cert.append(domain_config["domain"])

    set_nginx(config)

    if not check_certificate_validity():
        renew_cert(config["email"])

    if not domains_need_cert:
        return

    obtain_cert(email=config["email"], domains=domains_need_cert)
    for domain_config in config["domains"]:
        domain = domain_config["domain"]
        domain_config["is_cert_exists"] = check_if_cert_exists(domain)
        if domain_config["is_cert_exists"]:
            print(
                f"Certificates are generated successfully for domain [{domain}]."
            )
        else:
            print(f"failed to generate certificates for domain [{domain}].")

    set_nginx(config)


def ensure_correct_dir():
    """
    Changes the current working directory to the parent directory
    of the script's location. This ensures that the script is
    executed with the correct working directory context.
    """
    os.chdir(
        os.path.abspath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")))


def load_yaml_config(file_path):
    """
    Loads a YAML configuration file and returns its contents as a dictionary.

    Parameters:
        file_path (str): The path to the YAML configuration file.

    Returns:
        dict: The contents of the YAML file as a dictionary.
    """
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def main():
    """
    Ensures the correct directory context and sets up the SSL certificates.
    """
    ensure_correct_dir()
    config = load_yaml_config(
        os.path.abspath(os.path.join(os.getcwd(), "config.yaml")))
    while True:
        setup_certs(dict(config))
        time.sleep(sleep_in_secs)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
