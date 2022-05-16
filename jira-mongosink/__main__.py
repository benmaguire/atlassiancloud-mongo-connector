import os,sys
import traceback
import requests
from requests.auth import HTTPBasicAuth
import time
import logging
import pymongo
from apscheduler.schedulers.background import BackgroundScheduler


root = logging.getLogger()
ch = logging.StreamHandler(sys.stdout)

if 'LOGLEVEL' in os.environ:
    if os.environ['LOGLEVEL'] == "INFO":
        root.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)
    elif os.environ['LOGLEVEL'] == "DEBUG":
        root.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)
    else:
        root.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)
else:
    root.setLevel(logging.INFO)
    ch.setLevel(logging.INFO)


formatter = logging.Formatter('%(asctime)s - AtlassianCloud MongoDB Connector - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)



jirahost = os.environ["JIRA_HOST"]
jirauser = os.environ["JIRA_USER"]
jiratoken = os.environ["JIRA_TOKEN"]
mongouri = os.environ['MONGO_URI']
mongocol = os.environ['MONGO_COLLECTION']

mongoclient = pymongo.MongoClient(mongouri, connect=False)
mdb = mongoclient[mongocol]

sched = BackgroundScheduler()




@sched.scheduled_job('cron', hour="*")
def runDataIssues():

    # Get Issues
    headers = {
        "Accept": "application/json"
    }

    startAt = 0
    maxResults = 50
    counter = 0
    limit = 20000
    limitcounter = 0

    while True:
        url = jirahost + "/rest/api/3/search?startAt="+str(startAt)+"&maxResults="+str(maxResults)
        r = requests.get(url, auth=HTTPBasicAuth(jirauser, jiratoken) ,headers=headers)
        response_body = r.json()

        total = response_body['total']

        for i in response_body['issues']:
            newdict = i
            mdb['issues'].update_one({"id": i['id']}, {'$set': newdict}, upsert=True)
            counter+=1

        if startAt > total:
            break
        startAt += maxResults-1

        if limitcounter > limit:
            logging.error("Soft limit reached - Issues")
            break
        limitcounter+=1

    logging.info("JIRA Issues Processed " + str(counter))


@sched.scheduled_job('cron', hour="21")
def runDataProjects():

    # Get Issues
    headers = {
        "Accept": "application/json"
    }
    url = jirahost + "/rest/api/2/project"
    r = requests.get(url, auth=HTTPBasicAuth(jirauser, jiratoken), headers=headers)
    response_body = r.json()
    counter = 0

    for i in response_body:
        newdict = i
        mdb['projects'].update_one({"id": i['id']}, {'$set': newdict}, upsert=True)
        counter+=1

    logging.info("JIRA Projects Processed " + str(counter))




@sched.scheduled_job('cron', hour="*")
def runDataConfluence():

    # Get Issues
    headers = {
        "Accept": "application/json"
    }
    url = jirahost + "/wiki/rest/api/content?expand=body.storage"
    r = requests.get(url, auth=HTTPBasicAuth(jirauser, jiratoken), headers=headers)
    response_body = r.json()
    counter = 0

    for i in response_body['results']:
        newdict = i
        
        mdb['confluence_content'].update_one({"id": i['id']}, {'$set': newdict}, upsert=True)
        counter+=1

    logging.info("Confluence Pages Processed " + str(counter))







if __name__ == "__main__":
    #
    # Start Scheduler
    #
    logging.info("Starting AtlassianCloud Mongo Connector")
    
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    except:
        tracemsg = traceback.format_exc()
        logging.error("Unable to start Scheduler")
    
    try:
        runDataIssues()
    except:
        logging.error(traceback.format_exc())

    try:
        runDataProjects()
    except:
        logging.error(traceback.format_exc())

    try:
        runDataConfluence()
    except:
        logging.error(traceback.format_exc())
    

    while True:
        time.sleep(60)

