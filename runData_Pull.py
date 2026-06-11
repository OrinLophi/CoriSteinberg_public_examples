import requests
import os
import sys
import argparse
import json
import re
import csv
from datetime import datetime, timedelta

# Note: Bearer token defaults to the TOKEN_PRODUCTION environment variable if not passed via CLI.
# All GraphQL queries target the NowSecure API. Endpoint and token are the only required credentials.


def argeParseDef(parser):

    # Date range options — use either start/end datetime strings or a daysBack integer
    parser.add_argument("-s", "--startDateTime", required=False, help="Start date: 2026-11-01T00:00:00Z")
    parser.add_argument("-e", "--endDateTime", required=False, help="End date: 2026-12-31T00:00:00Z")
    parser.add_argument("-d", "--daysBack", type=int, required=False, help="From today, how many days back to search")

    # Output directory
    parser.add_argument("-o", "--outboundFileFolder", required=False, help="Where should the data be stored")

    # Authentication
    parser.add_argument("-b", "--bearerToken", required=False, help="Bearer token; defaults to TOKEN_PRODUCTION env variable")

    # Inbound file options for resuming or filtering a previous run
    parser.add_argument("-fc", "--fileCompleted", required=False, help="Inbound .txt file of completed advanced assessments; write 'omit' to skip")
    parser.add_argument("-ff", "--fileFailed", required=False, help="Inbound .txt file of failed advanced assessments; write 'omit' to skip")
    parser.add_argument("-fa", "--fileAppList", required=False, help="Inbound .txt file of application refs")

    # Mode flags
    parser.add_argument("-a", "--appList", action='store_true', required=False, help="Pull a complete list of apps")
    parser.add_argument("-plo", "--priorityLevelOrg", action='store_true', required=False, help="Pull priority level and org ID for assessment refs")

    return parser.parse_args()


def printBlob(json_data):
    """Pretty-print JSON data to stdout for debugging."""
    print(json.dumps(json_data, sort_keys=True, indent=2))


def dateTimeString(minusDays):
    """Return a UTC datetime string offset by minusDays from today."""
    now = datetime.now() - timedelta(days=minusDays)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def generateCSV(obff):
    """Open a new timestamped CSV file and return the writer and file handle."""
    fileName = obff + "PAM_on_" + dateTimeString(0) + ".csv"
    f = open(fileName, 'w+')
    writer = csv.writer(f)
    return [writer, f]


def pullData(result_string, regEx):
    """Extract all regex matches from a string, case-insensitive."""
    if regEx:
        var = f"{regEx}"
    else:
        print("No regex found")
        return

    regEx_results = re.findall(var, result_string, re.IGNORECASE)
    return regEx_results


def jsonPrintToFile(json_data, obff):
    """Write JSON data to a timestamped file."""
    fileName = obff + "advancedAssessmentPulled_on_" + dateTimeString(0) + ".json"
    with open(fileName, 'w+') as outFile:
        json.dump(json_data, outFile, sort_keys=True, indent=2)
    outFile.close()


def jsonTocsv(assessment_data, obff):
    """Convert a list of assessment dicts to a timestamped CSV file."""
    fileName = obff + "advancedAssessmentPulled_on_" + dateTimeString(0) + ".csv"
    data_file = open(fileName, 'w')
    csv_writer = csv.writer(data_file)
    count = 0

    for ref in assessment_data:
        if count == 0:
            header = ref.keys()
            csv_writer.writerow(header)
            count += 1
        csv_writer.writerow(ref.values())

    data_file.close()


def seperateConfigLevelType(referenceData, obff):
    """
    Split assessment refs into separate text files by config level (ADVANCED vs BASELINE).
    Returns the path to the advanced assessments file.
    """
    baselineFile = obff + "baselineAssessmentsList_on_" + dateTimeString(0) + ".txt"
    baseline = open(baselineFile, 'w')

    AdvancedFile = obff + "advancedAssessmentsList_on_" + dateTimeString(0) + ".txt"
    advanced = open(AdvancedFile, 'w')

    for x in referenceData["data"]["auto"]["assessments"]:
        if x["ref"] is not None and x["analysisConfigLevel"] == "ADVANCED":
            advanced.write(x["ref"] + "\n")
        elif x["ref"] is not None and x["analysisConfigLevel"] == "BASELINE":
            baseline.write(x["ref"] + "\n")
        else:
            print("undefined " + x["ref"])

    baseline.close()
    advanced.close()
    return AdvancedFile


def generateAppTextList(referenceData, obff):
    """Write all application refs to a text file and return the file path."""
    appListFile = obff + "applicationList_of_refs_on_" + dateTimeString(0) + ".txt"
    appList = open(appListFile, 'w')

    for x in referenceData["data"]["auto"]["applications"]:
        if x["ref"] is not None:
            appList.write(x["ref"] + "\n")

    appList.close()
    return appListFile


def pullAssessmentReferences_byDate(startDateTime, endDateTime, token, status):
    """
    Query the GraphQL API for assessment references within a date range and status.
    Returns [json_data, status_code].
    """
    headers = {
        'Accept': 'application/json',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Origin': 'https://api.nowsecure.com',
        'Authorization': "Bearer " + token
    }

    qString = (
        'query{auto{assessments(limit: 100000,scope:"*",reverse:true,status:' + status +
        ',since:"' + startDateTime + '",until: "' + endDateTime + '"){analysis{status},ref,analysisConfigLevel}}}'
    )
    print(qString)
    ql_query = {'query': qString}

    response = requests.post('https://api.nowsecure.com/graphql', headers=headers, json=ql_query)
    print("pullAssessmentReferences_byDate:\n   API return status: " + str(response.status_code))

    json_data = json.loads(response.text)
    return [json_data, response.status_code]


def pullAssessmentData(assessmentRef, token):
    """
    Pull full assessment metadata for a given ref.
    Returns response text or None on failure.
    """
    headers = {
        'Accept': 'application/json',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Origin': 'https://api.nowsecure.com',
        'Authorization': "Bearer " + token
    }

    qString = (
        'query{auto{assessments(scope:"*",reverse:true,refs:"' + assessmentRef +
        '"){taskId,createdAt,applicationRef,platformType,packageKey,isAppstoreDownload,errorCode,score,'
        'group{ref},buildVersion,packageVersion,config,analysis{isAuthenticated,task{dynamic{id}}}}}}'
    )
    ql_query = {'query': qString}

    response = requests.post('https://api.nowsecure.com/graphql', headers=headers, json=ql_query)
    print("pullAssessmentData:\n    API return status: " + str(response.status_code))
    print("      Reference number: " + assessmentRef)

    if response.status_code == 200:
        return response.text
    else:
        return None


def pullAssessmentMessage_byAssessmentReferenceID(assessmentRef, token):
    """
    Pull the event log messages for a given assessment ref.
    Returns response text or None on failure.
    """
    headers = {
        'Accept': 'application/json',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Origin': 'https://api.nowsecure.com',
        'Authorization': "Bearer " + token
    }

    qString = (
        'query{auto{assessments(scope:"*",reverse:true,refs:"' + assessmentRef +
        '"){analysis{eventLog(limit: 100000){message}}}}}'
    )
    ql_query = {'query': qString}

    response = requests.post('https://api.nowsecure.com/graphql', headers=headers, json=ql_query)
    print("\nMessage_byAssessmentReferenceID:\n    API return status: " + str(response.status_code))
    print("      Reference number: " + assessmentRef)

    if response.status_code == 200:
        return response.text
    else:
        return None


def pullAppConfigData(token, appRef):
    """
    Pull configuration data for a given application ref.
    Returns response text or None on failure.
    """
    headers = {
        'Accept': 'application/json',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Origin': 'https://api.nowsecure.com',
        'Authorization': "Bearer " + token
    }

    qString = (
        'query{auto{applications(scope:"*",reverse:true,refs:"' + appRef +
        '"){ref,platformType,packageKey,analysisConfigLevel,group{ref},'
        'analysisConfig{searchData{key,value},searchTerms{name,value},appium{runnerFilename},'
        'xctest{runnerFilename},jsScript},latestAssessment{createdAt},latestCompleteAssessment{createdAt}}}}'
    )
    ql_query = {'query': qString}

    response = requests.post('https://api.nowsecure.com/graphql', headers=headers, json=ql_query)
    print("\nPulling applications config data. API return status: " + str(response.status_code))

    if response.status_code == 200:
        return response.text
    else:
        return None


def pullAppList(token):
    """
    Pull a complete list of application refs.
    Returns [json_data, status_code].
    """
    headers = {
        'Accept': 'application/json',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Origin': 'https://api.nowsecure.com',
        'Authorization': "Bearer " + token
    }

    qString = 'query{auto{applications(scope:"*",reverse:true,limit:100000){ref}}}'
    ql_query = {'query': qString}

    response = requests.post('https://api.nowsecure.com/graphql', headers=headers, json=ql_query)
    print("\nPulling applications list. API return status: " + str(response.status_code))

    json_data = json.loads(response.text)
    return [json_data, response.status_code]


def pull_dynamicJobID_by_assessmentRef(assessmentRef, token):
    """
    Pull the dynamic job ID for a given assessment ref.
    Returns response text or None on failure.
    """
    headers = {
        'Accept': 'application/json',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Origin': 'https://api.nowsecure.com',
        'Authorization': "Bearer " + token
    }

    qString = (
        'query{auto{assessments(scope:"*",reverse:true,refs:"' + assessmentRef +
        '"){analysis{task{dynamic{id}}}}}}'
    )
    ql_query = {'query': qString}

    response = requests.post('https://api.nowsecure.com/graphql', headers=headers, json=ql_query)

    if response.status_code == 200:
        return response.text
    else:
        return None


def process_plo(referenceData, csvFile, token, status):
    """Process priority level and org ID for each assessment ref and write to CSV."""
    for z in referenceData[0]["data"]["auto"]["assessments"]:
        if z["ref"] is not None:
            element = z["ref"]
            print("Parsing " + status + " assessment: " + element)
            dynamicJobID_results = pull_dynamicJobID_by_assessmentRef(element, token)
            dynamicJobID = None
            jobPriority, orgID = [], []
            if dynamicJobID_results is not None:
                jsonData = json.loads(dynamicJobID_results)
                dynamicJobID = jsonData["data"]["auto"]["assessments"][0]["analysis"]["task"]["dynamic"]["id"]
            row = [status, z["analysisConfigLevel"], dynamicJobID, z["ref"], jobPriority, orgID]
            csvFile[0].writerow(row)


def plo(referenceDataINC, referenceData, outBoundDirectory, token):
    """Generate a CSV of priority level and org ID data across failed and completed assessments."""
    csvFile = generateCSV(outBoundDirectory)
    header = ["Status", "ConfigLevel", "DynamicJobID", "Assessment Reference", "Job Priority", "OrgID"]
    csvFile[0].writerow(header)
    if referenceDataINC is not None:
        process_plo(referenceDataINC, csvFile, token, "Failed")
    if referenceData is not None:
        process_plo(referenceData, csvFile, token, "Completed")
    csvFile[1].close()
    print("Complete")


def processData(referenceData, csvFile, token, status):
    """
    For each assessment ref, pull full metadata and event log messages.
    Extract RunData, login success, action counts, credentials, and device info via regex.
    Write all fields to the output CSV.
    """
    for x in referenceData:
        element = x.replace("\n", "")
        print("\nParsing " + status + " assessment: " + element)
        results = pullAssessmentData(element, token)

        if results is not None:
            json_data = json.loads(results)
            if json_data["data"]["auto"]["assessments"] is not None:
                messages = pullAssessmentMessage_byAssessmentReferenceID(element, token)

                if messages is not None:
                    runData = pullData(messages, 'loginSuccess(?:[^"]|"")*[\":\\s]*true|login_success(?:[^"]|"")*[\":\\s]*true')
                    appCrash = pullData(messages, "[a-z :]+ crash[a-z :]+|Automator left app[^}]*")
                    rd_presnt = pullData(messages, "rundata")
                    deviceVersion = pullData(messages, 'loginSuccess(?:[^"]|"")*[\":\\s]*false|login_success(?:[^"]|"")*[\":\\s]*false')
                    deviceType = pullData(messages, 'loginSuccess|login_success')
                    total_actions = pullData(messages, '(?<!\\s)total_actions(?:[^"]|"")*[\":\\s]*(\\d+)')
                    actions_completed = pullData(messages, '(?<!\\s)actions_completed(?:[^"]|"")*[\":\\s]*(\\d+)')
                else:
                    runData, appCrash, rd_presnt, deviceType, deviceVersion, total_actions, actions_completed = None, None, None, None, None, None, None

                email = pullData(results, "\"email\":{\"value\":\"([\\s\\S]*?)\"")
                username = pullData(results, "\"username\":{\"value\":\"([\\s\\S]*?)\"")
                deleteIt = pullData(results, "\"password\":{\"value\":\"([\\s\\S]*?)\"")
                actions = pullData(results, "actions\":{\"find[^}]*")
                automationScript = pullData(results, "automation_js_script[^{]*|xctest\":{[^}]*|archive_filename[^,]*")
                lat = pullData(results, "\"gpsLatitude\":{\"value\":\"([\\s\\S]*?)\"")
                lon = pullData(results, "\"gpsLongitude\":{\"value\":\"([\\s\\S]*?)\"")
                y = json_data["data"]["auto"]["assessments"][0]

                row = [
                    y["platformType"], y["packageKey"], y["isAppstoreDownload"], status,
                    y["taskId"], y["analysis"]["task"]["dynamic"]["id"], y["createdAt"],
                    y["applicationRef"], y["group"]["ref"], y["buildVersion"], y["packageVersion"],
                    y["score"], y["errorCode"], appCrash, automationScript, rd_presnt,
                    y["analysis"]["isAuthenticated"], runData, username, email,
                    total_actions, actions_completed, lat, lon, actions,
                    deviceVersion, deviceType, element, deleteIt
                ]
                csvFile[0].writerow(row)


def processAppList(appData, token, outBoundDirectory):
    """
    For each application ref in a text file, pull config data and write to CSV.
    Extracts username, email, automation script references, and config metadata.
    """
    alist = open(appData, 'r+')
    csvFile = generateCSV(outBoundDirectory + "appList_")
    header = [
        "ref", "platformType", "packageKey", "analysisConfigLevel",
        "latest_Assessment", "latest_Completed", "group_ref",
        "username", "Email", "searchTerms", "appium", "xctest", "jsScript", "Error Log", "String"
    ]
    csvFile[0].writerow(header)

    for x in alist:
        appRef = x.replace("\n", "")
        print("Parsing " + appRef)
        appConfigData = pullAppConfigData(token, appRef)
        if appConfigData is not None:
            try:
                json_data = json.loads(appConfigData)
                app = json_data["data"]["auto"]["applications"][0]
                if app is not None:
                    username, email = "", ""
                    if app["analysisConfig"]["searchData"]:
                        for y in app["analysisConfig"]["searchData"]:
                            if y["key"] == "email":
                                email = y["value"]
                            elif y["key"] == "username":
                                username = y["value"]

                    row = [
                        app["ref"], app["platformType"], app["packageKey"],
                        app["analysisConfigLevel"], app["latestAssessment"],
                        app["latestCompleteAssessment"], app["group"]["ref"],
                        username, email, app["analysisConfig"]["searchTerms"],
                        app["analysisConfig"]["appium"], app["analysisConfig"]["xctest"],
                        app["analysisConfig"]["jsScript"], "", ""
                    ]
                    csvFile[0].writerow(row)
            except Exception as e:
                print(e)
                row = [appRef, "", "", "", "", "", "", "", "", "", "", "", "", e, appConfigData]
                csvFile[0].writerow(row)

    print("Finished processing appList")
    alist.close()
    csvFile[1].close()


def main():
    parser = argparse.ArgumentParser()
    my_args = argeParseDef(parser)

    if my_args.outboundFileFolder:
        if my_args.outboundFileFolder.endswith("/"):
            outBoundDirectory = my_args.outboundFileFolder
        else:
            outBoundDirectory = my_args.outboundFileFolder + "/"
    else:
        outBoundDirectory = ""

    if my_args.bearerToken:
        token = my_args.bearerToken
    else:
        token = os.environ.get("TOKEN_PRODUCTION")

    if my_args.endDateTime is None:
        endDateTime = dateTimeString(0)
    else:
        endDateTime = my_args.endDateTime + "T00:00:00Z"
        print(endDateTime)

    if my_args.startDateTime is None:
        if my_args.daysBack:
            startDateTime = dateTimeString(my_args.daysBack)
        else:
            startDateTime = dateTimeString(30)
    else:
        startDateTime = my_args.startDateTime + "T00:00:00Z"
        print(startDateTime)

    # App list mode: pull all application refs and export config data
    if my_args.appList:
        if not os.path.exists(outBoundDirectory + "appList/"):
            os.makedirs(outBoundDirectory + "appList/")

        if my_args.fileAppList:
            if my_args.fileAppList.endswith(".txt"):
                appRefFile = my_args.fileAppList
            else:
                print("-fa, app list file, must be a txt file.")
        else:
            print("Pulling AppList")
            apps = pullAppList(token)
            if apps[1] == 200:
                print("Printing to JSON File: Application List")
                jsonPrintToFile(apps[0], outBoundDirectory + "appList/appList")
                appRefFile = generateAppTextList(apps[0], outBoundDirectory + "appList/")
        processAppList(appRefFile, token, outBoundDirectory)

    # Completed assessments — use inbound file or pull fresh from API
    if my_args.fileCompleted:
        if my_args.fileCompleted == "omit":
            completed_adv_data_file = None
        else:
            if my_args.fileCompleted.endswith(".txt"):
                completed_adv_data_file = my_args.fileCompleted
            else:
                sys.exit("-fc or --fileCompleted must be a .txt file.")
    else:
        if not os.path.exists(outBoundDirectory + "completed/"):
            os.makedirs(outBoundDirectory + "completed/")

        print("Pulling Completed Assessments by reference.")
        referenceData = pullAssessmentReferences_byDate(startDateTime, endDateTime, token, '"completed"')
        if referenceData[1] == 200:
            print("Printing to JSON File: Completed Assessments by reference.")
            jsonPrintToFile(referenceData[0], outBoundDirectory + "completed/")
            print("Printing to CSV File: Completed Assessments by reference.")
            jsonTocsv(referenceData[0]["data"]["auto"]["assessments"], outBoundDirectory + "completed/")
            print("Separating out config level type")
            completed_adv_data_file = seperateConfigLevelType(referenceData[0], outBoundDirectory + "completed/")
        else:
            completed_adv_data_file = None

    # Failed assessments — use inbound file or pull fresh from API
    if my_args.fileFailed:
        if my_args.fileFailed == "omit":
            failed_adv_file = None
        else:
            if my_args.fileFailed.endswith(".txt"):
                failed_adv_file = my_args.fileFailed
            else:
                sys.exit("-ff or --fileFailed must be a .txt file.")
    else:
        if not os.path.exists(outBoundDirectory + "failed/"):
            os.makedirs(outBoundDirectory + "failed/")

        print("Pulling Failed Assessments by reference.")
        referenceDataINC = pullAssessmentReferences_byDate(startDateTime, endDateTime, token, '"failed"')
        if referenceData[1] == 200:
            print("Printing to JSON File: Failed Assessments by reference.")
            jsonPrintToFile(referenceDataINC[0], outBoundDirectory + "failed/")
            print("Printing to CSV File: Failed Assessments by reference.")
            jsonTocsv(referenceDataINC[0]["data"]["auto"]["assessments"], outBoundDirectory + "failed/")
            print("Separating out config level type")
            failed_adv_file = seperateConfigLevelType(referenceDataINC[0], outBoundDirectory + "failed/")
        else:
            failed_adv_file = None

    # Priority level and org ID mode
    if my_args.priorityLevelOrg:
        plo(referenceDataINC, referenceData, outBoundDirectory, token)
        return

    # Main output: full assessment data CSV
    csvFile = generateCSV(outBoundDirectory + "advancedAssessments_")
    header = [
        "platformType", "packageKey", "isAppstoreDownload", "status", "taskId", "DynamicJobID",
        "createdAt", "applicationRef", "group", "buildVersion", "packageVersion",
        "score", "errorCode", "app crash", "AutomationScript", "Run Data Present in Script",
        "Authenticated", "RunData", "UserName", "Email", "Total Actions", "Actions Completed",
        "Latitude", "Longitude", "Actions", "Device Version", "Device Type", "Job Ref", "Delete"
    ]
    csvFile[0].writerow(header)

    if failed_adv_file is not None:
        ff = open(failed_adv_file, 'r+')
        processData(ff, csvFile, token, "Failed")
    if completed_adv_data_file is not None:
        cf = open(completed_adv_data_file, 'r+')
        processData(cf, csvFile, token, "Completed")

    csvFile[1].close()
    print("Complete")


if __name__ == "__main__":
    main()
