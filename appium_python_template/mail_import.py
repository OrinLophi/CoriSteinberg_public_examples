import re
import time

def retrieve_url(url, headers=None):
    if headers is None:
        headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    else:
        headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8', **headers}
    try:
        import requests
        print('Using requests.get')
        return requests.get(url, headers=headers).json()
    except ModuleNotFoundError:
        print('Using urllib3.PoolManager.request')
        import urllib3
        import json
        r = urllib3.PoolManager(num_pools=1).request('GET', url, headers=headers)
        return json.loads(r.data)

def pull_data(result_string, regEx):

    if regEx:
        var = f"{regEx}"
    else:
        print("No regex found")
        return

    regEx_results =  re.findall(var,result_string, re.IGNORECASE)

    return(regEx_results)

def url_link(driver_object, creds, recall_limit):
    email = creds['username']
    client_domain = creds['domain']
    api_token = creds['token']
    base_url = f'https://mailinator.com/api/v2/domains/{email.partition("@")[2]}/inboxes/{email.partition("@")[0]}'
    # First, we have to pull reference data for the emails
    last_5_emails = retrieve_url(f'{base_url}?limit=5&sort=descending&token={api_token}')
    print('Done request')
    # Second, we must extract a specific reference id from the newest email.
    received_id = [msg for msg in last_5_emails['msgs'] if
                   msg['subject'].endswith(("log back in!", "log in on a new device")) and client_domain in msg['origfrom']][0]['id']
    # Third, we use the reference id to pull the message data
    message_data = retrieve_url(
        f'https://mailinator.com/api/v2/domains/private/messages/{received_id}/?token={api_token}')
    time_in_seconds = message_data["seconds_ago"]
    print(f"Time since message was received {time_in_seconds}")
    links = retrieve_url(
        f'https://mailinator.com/api/v2/domains/private/messages/{received_id}/links?token={api_token}')
    # Fourth, from the message data we isolate the message body.
    return_link = ""
    for link in links["links"]:
        if len(link) > len(return_link):
            return_link = link

    seconds_ago = message_data["seconds_ago"]
    driver_object.log_event("nowsecure", f"Latest message in seconds: {seconds_ago}")
    print(f"Latest message in seconds: {seconds_ago}")
    if seconds_ago > 300 and recall_limit < 10:
        time.sleep(8)
        return_link = url_link(driver_object, creds, recall_limit + 1)
    return return_link