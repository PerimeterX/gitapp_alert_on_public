import requests
from datetime import datetime
import json
import os
import logging
import threading
import sys
import pymongo
import config

headers = {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': 'Bearer {token}'
}
MINIMUM_DAYS = 7

def get_outside_collabs(organization):
    baseurl ="https://api.github.com/orgs/{}/outside_collaborators".format(organization)
    users = []
    i = 1
    while True:
        r = requests.get("{}?per_page=100&page={}".format(baseurl, i), headers=headers)
        if (r.status_code != 200):
            raise Exception(r.text)
        data = json.loads(r.text)
        for user in data:
            users.append(user)
        if len(data) == 0:
            break
        i += 1
    return users
    
def get_user_list(organization):
    baseurl ="https://api.github.com/orgs/{}/members".format(organization)
    users = []
    i = 1
    while True:
        r = requests.get("{}?per_page=100&page={}".format(baseurl, i), headers=headers)
        if (r.status_code != 200):
            raise Exception(r.text)
        data = json.loads(r.text)
        for user in data:
            users.append(user)
        if len(data) == 0:
            break
        i += 1
    return users

def run_gquery(query):
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

def get_git_org_members_emails(organization):      
    query1 = """{{
        organization(login: "{org}") {{
            name
            url
            membersWithRole(first: 100) {{
                nodes {{
                    login
                    organizationVerifiedDomainEmails(login: "{org}")
                }}
                pageInfo {{
                    hasNextPage
                    endCursor
                }}
            }}
        }}
    }}
    """
    query2 = """{{
        organization(login: "{org}") {{
            name
            url
            membersWithRole(first: 100, after: "{cursor}") {{
                nodes {{
                    login
                    organizationVerifiedDomainEmails(login: "{org}")
                }}
                pageInfo {{
                    hasNextPage
                    endCursor
                }}
            }}
        }}
    }}
    """

    cursor = ""
    members = []
    while True:
        if (cursor == ""):
            # First run
            result = run_gquery(query1.format(org=organization))
        else:    
            result = run_gquery(query2.format(org=organization, cursor=cursor))
        cursor = result['data']['organization']['membersWithRole']['pageInfo']['endCursor']
        for member in result['data']['organization']['membersWithRole']['nodes']:
            try:
                email = member['organizationVerifiedDomainEmails'][0]
            except:
                email = ""
            members.append(
                {
                    "name": member['login'],
                    "email": email
                }
            )
        if (False == result['data']['organization']['membersWithRole']['pageInfo']['hasNextPage']):
            break
    
    return members

def scan_repos_for_user(user_data):
    results = []
    for repo in user_data:
        # if forked, we don't care
        if (True == repo['fork']):
            continue
        # if over 14 days old, we don't care
        created_at = datetime.strptime(repo['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        delta = datetime.now()-created_at
        if (delta.days <= MINIMUM_DAYS):
            finding = { 
                'name': repo['owner']['login'],
                'repo_url': repo['html_url'],
                'days_old': delta.days
            }
            results.append(finding)
    return results

def scan_users_directory(organization):
    results = []
    directory = 'temp/{}/users'.format(organization)
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isfile(f):
            with open(f, 'r') as file:
                data = json.loads(file.read())
            if (len(data) > 0):
                results += scan_repos_for_user(data)
    return results

def download_users_list(organization, users):
    threads = list()
    total = len(users)
    index = 0
    for user in users:
        file = "temp/{}/users/{}.json".format(organization, user['login'])
        x = threading.Thread(target=thread_download_user, args=(file, user['repos_url'],index,total,))
        threads.append(x)
        x.start()
        index += 1

    for file, thread in enumerate(threads):
        thread.join()

maxthreads = 5
sema = threading.Semaphore(value=maxthreads)

def thread_download_user(filepath, repos_url, index, total):
    sema.acquire()
    r = requests.get(repos_url, headers=headers)
    if (r.status_code != 200):
        raise Exception(r.text)
    f = open(filepath, "w")
    f.write(json.dumps(json.loads(r.text), indent=4))
    f.close
    sema.release()

def send_notifications_to_slack(notifications, webhookurl):
    for item in notifications:
        repo_name = item['repo_url'].rsplit('/', 1)[-1]
        payload = {
            "blocks": [{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "New public repo found on git user *{}* <{}|{}> ({} days old)".format(item['name'], item['repo_url'], repo_name, item['days_old'])
                }}]
            }
        r = requests.post(webhookurl, data=json.dumps(payload))
        if (r.status_code != 200):
            raise Exception("Error while sending slack notification: {}".format(r.text))

def add_notifications_to_db(organization, notifications):
    myclient = pymongo.MongoClient(config.get_mongo_connection_string())
    mydb = myclient[config.get_mongo_db()]
    mycol = mydb["notifications"]

    for item in notifications:
        # check if item already exists:
        myquery = { "gitorg": organization, "gitusername": item['name'], "repo_url": item['repo_url'] }
        x = mycol.find_one(myquery)
        if x is not None:
            continue

        # doesn't exist, add as new
        mydict = {
            "gitorg": organization, 
            "gitusername": item['name'],
            "repo_url": item['repo_url'],
            "days_old": item['days_old'],
            "acknowledged": False,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        x = mycol.insert_one(mydict)


def run(organization, auth_token, slackwebhook):
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    headers['Authorization'] = headers['Authorization'].format(token=auth_token)

    dirs = "temp/{}/users/".format(organization)
    
    isExist = os.path.exists(dirs)
    if not isExist:
        os.makedirs("temp/")
        os.makedirs("temp/{}".format(organization))
        os.makedirs("temp/{}/users/".format(organization))
    
    users = get_user_list(organization)
    logging.info("Downloading {} users".format(len(users)))
    download_users_list(organization, users)
    notifications = (scan_users_directory(organization))
    logging.info("Found {} notifications".format(len(notifications)))
    if (len(notifications) == 0):
        return
        
    if slackwebhook is not None:
        logging.info("Sending to slack webhook")
        send_notifications_to_slack(notifications, slackwebhook)
    if config.get_mongo_state():
        logging.info("Sending to mongo collection")
        add_notifications_to_db(organization, notifications)
    
def main(argv):
    run(argv[1], argv[2], argv[3])

#TODO: send slack / email to user via his personal info
#print(get_git_org_members_emails())

if __name__ == "__main__":
    main(sys.argv)
