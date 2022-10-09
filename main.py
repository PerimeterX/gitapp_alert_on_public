import schedule
import time
import track
import requests
import json
import logging
import config
from cryptography.hazmat.backends import default_backend
import jwt
import sys

def get_jwt():
    cert_str = open(config.get_config_obj()['key_file'], 'r').read()
    cert_bytes = cert_str.encode()

    private_key = default_backend().load_pem_private_key(cert_bytes, None)

    time_since_epoch_in_seconds = int(time.time())
    
    payload = {
      # issued at time
      'iat': time_since_epoch_in_seconds,
      # JWT expiration time (10 minute maximum)
      'exp': time_since_epoch_in_seconds + (10 * 60),
      # GitHub App's identifier
      'iss': config.get_config_obj()['github_app_id']
    }

    actual_jwt = jwt.encode(payload, private_key, algorithm='RS256')

    return actual_jwt

def get_installations(jwt):
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer {token}'.format(token=jwt)
    }
    baseurl ="https://api.github.com/app/installations"
    r = requests.get(baseurl, headers=headers)
    if (r.status_code != 200):
        raise Exception(r.text)
    data = json.loads(r.text)
    result = []
    for i in data:
        result.append({'org': i['account']['login'], 'access_tokens_url': i['access_tokens_url']})
    return result

def get_access_token(jwt, access_tokens_url):
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer {token}'.format(token=jwt)
    }
    r = requests.post(access_tokens_url, headers=headers)
    if (r.status_code != 201):
        raise Exception(r.text)
    return json.loads(r.text)['token']

def job():
    jwt = get_jwt()
    logging.info("Got JWT token")
    installs = get_installations(jwt)
    for install in installs:
        logging.info("Running for install {}".format(install['org']))
        install_token = get_access_token(jwt, install['access_tokens_url'])
        logging.info("Got installation access token")
        conf = config.get_info_for_org(install['org'])
        logging.info("Using config: {}, {}".format(install['org'], conf['slackwebhook']))
        track.run(install['org'], install_token, conf['slackwebhook'])

def main(argv):
    schedule = True
    if (len(argv) == 2):
        if (argv[1] == "once"):
            schedule = False

    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    job()
    if (not schedule):
        return
    
    schedule.every(30).minutes.do(job)

    while 1:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":
    main(sys.argv)
