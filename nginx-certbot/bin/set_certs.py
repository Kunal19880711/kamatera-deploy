#!/opt/certbot/bin/python

import os
import subprocess
import time
import socket
from dotenv import load_dotenv
from jinja2 import Template

sleep_in_secs = 60


def check_if_cert_exists():
    """
    Checks if the SSL certificate and private key files exist for the specified domain.

    The function retrieves the domain from the environment variables and constructs
    the paths to the certificate and key files in the Let's Encrypt directory.
    It returns True if both files exist, indicating that the certificate is present,
    otherwise it returns False.
    """
    domain = os.getenv("DOMAIN")
    cert_file_path = os.path.join("/etc/letsencrypt/live", domain, "fullchain.pem")
    cert_key_file_path = os.path.join("/etc/letsencrypt/live", domain, "privkey.pem")
    print(cert_file_path, cert_key_file_path)
    return os.path.exists(cert_file_path) and os.path.exists(cert_key_file_path)


def check_if_dhparam_available():
    """
    Checks if the dhparam file exists in the /etc/ssl/certs directory.
    """
    dpparamFilePath = "/etc/ssl/certs/dhparam-2048.pem"
    return os.path.exists(dpparamFilePath)


def check_nodejs_server_active():
    """
    Checks if the Node.js server is active by attempting to resolve the hostname
    'scalarchatterbox-node' to an IP address. If the hostname is resolvable, it
    indicates that the server is active and running. If the hostname is not
    resolvable, it indicates that the server is not running.

    Returns:
        bool: True if the Node.js server is active, False otherwise.
    """
    try:
        socket.gethostbyaddr("scalarchatterbox-node")
        return True
    except socket.herror:
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


def set_nginx(is_cert_exists):
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
    domain = os.getenv("DOMAIN")
    is_nodejs_server_active = check_nodejs_server_active()
    is_dhparam_available = check_if_dhparam_available()
    data = {
        "domain": domain,
        "enable_https": is_cert_exists,
        "is_nodejs_server_active": is_nodejs_server_active,
        "is_dhparam_available": is_dhparam_available,
    }

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
        expiration_date = None
        for line in output.decode("utf-8").splitlines():
            if "Expires" in line:
                expiration_date = line.split(":")[1].strip()
                break
        # Check if certificate is valid (i.e., not expired)
        if expiration_date:
            import datetime

            expiration_date = datetime.datetime.strptime(
                expiration_date, "%Y-%m-%d %H:%M:%S%z"
            )
            if expiration_date > datetime.datetime.now():
                return True
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error checking certificate validity: {e}")
        return False


def renew_cert(email):
    """
    Renews the SSL certificate for the specified domain using certbot.

    The --force-renewal flag is used to force the renewal of the certificate
    even if it's not due to expire yet. This is useful for testing purposes.

    The --non-interactive flag is used to prevent certbot from asking user
    questions. The --agree-tos flag is used to agree to the terms of service.
    The --email flag is used to specify the contact email address for the
    certificate.

    The function runs the certbot renew command with the given flags and
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


def obtain_cert(email, domain):
    """
    Obtains the SSL certificate for the specified domain using certbot.

    The --nginx flag is used to configure the Nginx web server.
    The --non-interactive flag is used to prevent certbot from asking user
    questions. The --agree-tos flag is used to agree to the terms of service.
    The --email flag is used to specify the contact email address for the
    certificate.

    The function runs the certbot certonly command with the given flags and
    checks the return code of the command. If the command fails, the function
    raises a CalledProcessError exception.
    """
    subprocess.run(
        [
            "certbot",
            "certonly",
            "--nginx",
            "--email",
            email,
            "--agree-tos",
            "-n",
            "--no-eff-email",
            "-d",
            domain,
            "-d",
            "www." + domain,
        ],
        check=True,
    )


def setup_certs():
    """
    Sets up the SSL certificates for the specified domain.

    This function checks if the SSL certificates and key files exist for the specified domain.
    If the certificates and key files exist, it sets up the nginx server to use them.
    If the certificates and key files do not exist, it runs the certbot certonly command to
    obtain the certificates and sets up the nginx server to use them.

    It also checks the validity of the certificates and renews them if they are not valid.
    """
    is_cert_exists = check_if_cert_exists()
    email = os.getenv("EMAIL")
    domain = os.getenv("DOMAIN")

    if is_cert_exists:
        set_nginx(is_cert_exists)
        is_cert_valid = check_certificate_validity()
        if not is_cert_valid:
            renew_cert(email)
    else:
        obtain_cert(email, domain)
        is_cert_exists = check_if_cert_exists()
        if is_cert_exists:
            print("Certificates are generated successfully.")
            set_nginx(is_cert_exists)
        else:
            print("failed to generate certificates")


def ensure_correct_dir():
    """
    Changes the current working directory to the parent directory
    of the script's location. This ensures that the script is
    executed with the correct working directory context.
    """
    os.chdir(
        os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
    )


def main():
    """
    Ensures the correct directory context, loads the environment variables from the
    .env file and sets up the SSL certificates.
    """
    ensure_correct_dir()
    load_dotenv()
    while True:
        setup_certs()
        time.sleep(sleep_in_secs)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
