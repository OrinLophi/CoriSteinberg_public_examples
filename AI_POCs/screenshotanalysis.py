import requests
import os
import sys
import argparse
import json
import csv
import time

# Example usage:
# python3 screenshotanalysis.py -e https://api.your-endpoint.com --max -a 3 -d 7 -t "Action Strings" --pull_screenshots
#
# Overview:
# This script orchestrates AI-powered screenshot analysis for mobile application assessments.
# It retrieves app assessment data from a configurable API endpoint, submits screenshots
# to an AI analysis workflow (via Retool webhook - see inner_workflow/outer_workflow),
# and outputs structured results as CSV and JSON.
#
# The LLM prompt logic and OpenAI integration live in the Retool workflow layer.
# This script handles data retrieval, batching, orchestration, retry logic, and output formatting.
#
# Built as a production POC. Webhook endpoints are configurable via environment variables;
# in a production version these would be fully externalized from the codebase.


def test_case(x):
    errorOb = {
        'platformType': 'request_object["app"]["platformType"]',
        'packageKey': 'request_object["app"]["packageKey"]',
        'title': "error: " + 'str(response.status_code)'
    }
    return_string = [json.dumps(errorOb)]
    if len(return_string) > 0:
        print(return_string)
        try:
            json_print_to_file(return_string, x, "gpt_failure_apps")
        except Exception as e:
            print("GPT FAILURE list print to file error")
            print(e)


def arge_parse(parser):

    #   provide the full path to output folder
    parser.add_argument("-o", "--outboundFileFolder", required=False, help="Where should the data be stored")
    parser.add_argument("-e", "--endpoint", required=True, help="API endpoint domain")
    parser.add_argument("-b", "--bearerToken", required=False, help="Bearer token; defaults to NS_BEARER_TOKEN env variable")
    parser.add_argument("-g", "--groupID", required=False, help="GroupID")
    parser.add_argument("-t", "--tags", required=False, type=str, help="Assessment tags")
    parser.add_argument("-s", "--screenshotLimit", required=False, type=int, help="Screenshot limit")
    parser.add_argument("-a", "--appLimit", required=True, type=int, help="App limit")
    parser.add_argument("-d", "--daysBack", required=True, help="How far back to look")
    parser.add_argument("-f", "--jsonFile", required=False, help="JSON file for retrying a previous analysis run")
    parser.add_argument("-p", "--analysis_pass", required=False, type=int, help="Analysis pass number")
    parser.add_argument("--pull_screenshots", required=False, action='store_true', help="Download screenshots to local file")
    parser.add_argument("--test", required=False, action='store_true', help="Run test case")
    parser.add_argument("--max", required=False, action='store_true', help="Max screenshots: currently set to 50")

    return parser


def generate_csv(obff) -> object:

    file_name = obff + "ai_screenshot_analysis" + ".csv"
    f = open(file_name, 'w+')

    #   create the csv writer
    writer = csv.writer(f)

    return [writer, f]


def json_to_csv(assessment_data, obff) -> None:

    fileName = obff + "ai_screenshot_analysis" + ".csv"
    data_file = open(fileName, 'w')

    csv_writer = csv.writer(data_file)

    first_flag = True

    for x in assessment_data:
        if x is None or x == "":
            pass
        else:
            ref = json.loads(x)
            if first_flag:
                header = ref.keys()
                csv_writer.writerow(header)
                first_flag = False

            csv_writer.writerow(ref.values())

    data_file.close()


def json_print_to_file(json_data, obff, title):

    fileName = obff + title + ".json"

    with open(fileName, 'w+') as outFile:
        json.dump(json_data, outFile, sort_keys=True, indent=2)

    outFile.close()


def outer_workflow(request_object) -> str:
    # Retool webhook URL - configure via RETOOL_OUTER_WEBHOOK_URL environment variable in production
    webhook_url = os.environ.get("RETOOL_OUTER_WEBHOOK_URL", "https://api.retool.com/v1/workflows/YOUR_WORKFLOW_ID/startTrigger")
    retool_key = os.environ.get("RETOOL_OUTER_API_KEY", "YOUR_RETOOL_API_KEY")

    header = {
        'Content-Type': 'application/json',
        'X-Workflow-Api-Key': retool_key
    }

    response = requests.post(url=webhook_url, data=json.dumps(request_object), headers=header)
    print("API return status - outer: " + str(response.status_code) + " " + response.reason)

    if response.status_code != 200:
        return "None"
    else:
        return response.text


def inner_workflow(request_object, obff, retry_flag) -> str:
    # Retool webhook URL - configure via RETOOL_INNER_WEBHOOK_URL environment variable in production
    webhook_url = os.environ.get("RETOOL_INNER_WEBHOOK_URL", "https://api.retool.com/v1/workflows/YOUR_WORKFLOW_ID/startTrigger")
    retool_key = os.environ.get("RETOOL_INNER_API_KEY", "YOUR_RETOOL_API_KEY")

    header = {
        'Content-Type': 'application/json',
        'X-Workflow-Api-Key': retool_key
    }

    response = requests.post(url=webhook_url, data=json.dumps(request_object), headers=header)
    print("API return status - inner: " + str(response.status_code) + " " + response.reason)

    if response.status_code != 200:
        if retry_flag:
            print("Retrying")
            inner_workflow(request_object, obff, False)
        else:
            output_string = "analysisFailure_" + request_object["app"]["packageKey"]
            json_print_to_file(request_object["app"], obff, output_string)
            return None
    else:
        return response.text


def outer_to_inner_loop(app_json_data, config, obff) -> list:

    results_list = []
    failed_gpt_data = []
    screenshotLists = []

    for app in app_json_data:
        try:
            print("Submitting app to inner loop...")
            inner_json = {"config": config, "app": app}
            return_string = inner_workflow(inner_json, obff, True)
            if return_string:
                results = json.loads(return_string)
                results_list.append(json.dumps(results["appData"]))

                if results["appData"]["loginSuccess"] == "GPT FAILURE":
                    failed_gpt_data.append(app)
                screenshotLists.append(json.dumps({
                    'app': app['packageKey'],
                    'os': app['platformType'],
                    'screenshotList': results["screenshots"]
                }))

        except Exception as e:
            print("An exception occurred during the parsing of apps")
            print(e)
            failed_gpt_data.append(app)

        time.sleep(2)

    return [results_list, screenshotLists, failed_gpt_data]


def pull_screenshots(app_json_data, obff):

    for app_ob in app_json_data:
        ob = json.loads(app_ob)
        screen_shots = ob['screenshotList']
        if len(screen_shots) > 0:
            directory_string = ob['app'] + "_" + ob['os'] + "/"

            if not os.path.exists(obff + directory_string):
                os.makedirs(obff + directory_string)

            index = 1
            for url_string in screen_shots:
                filename = obff + directory_string + str(index) + ".jpeg"
                r = requests.get(url_string, allow_redirects=True)
                f = open(filename, 'wb')
                f.write(r.content)
                f.close()
                print("Processing Image {}".format(index))
                index += 1


def main():
    parser = argparse.ArgumentParser()
    my_args = arge_parse(parser).parse_args()

    if my_args.max:
        screenshot_limit = 50
    elif my_args.screenshotLimit:
        screenshot_limit = my_args.screenshotLimit
    else:
        print("Screenshot limit must be defined.\nSet -s int or --max")
        return

    if my_args.outboundFileFolder:
        if my_args.outboundFileFolder.endswith("/"):
            obff = my_args.outboundFileFolder + "ai_analysis/"
        else:
            obff = my_args.outboundFileFolder + "/" + "ai_analysis/"
    else:
        obff = "ai_analysis/"

    if not os.path.exists(obff):
        os.makedirs(obff)

    if my_args.bearerToken:
        token = my_args.bearerToken
    else:
        token = os.environ.get("NS_BEARER_TOKEN")

    if my_args.groupID:
        groupID = my_args.groupID
    else:
        groupID = None

    if my_args.tags:
        tags = my_args.tags
    else:
        tags = None

    if my_args.analysis_pass:
        analysis_pass = my_args.analysis_pass
    else:
        analysis_pass = 2

    if my_args.test:
        test_case(obff)
        return

    request_json = {
        "pass": analysis_pass,
        "appCount": my_args.appLimit,
        "tag": tags,
        "includeBaseline": False,
        "screenshotLimit": screenshot_limit,
        "withinPastNumberOfDays": my_args.daysBack,
        "input": "images",
        "endpoint": my_args.endpoint,
        "token": token
    }

    if my_args.jsonFile:
        if my_args.jsonFile.endswith(".json"):
            with open(my_args.jsonFile) as f:
                json_data = json.load(f)
        else:
            sys.exit("-f or --jsonFile must be a json file type.")
    else:
        results = outer_workflow(request_json)

        if results == "None":
            print("No results, exiting")
            return
        else:
            json_data = json.loads(results)

    json_print_to_file(json_data, obff, "app_list_data")
    final_list = outer_to_inner_loop(json_data, request_json, obff)
    json_to_csv(final_list[0], obff)

    if len(final_list[2]) > 0:
        print(final_list[2])
        try:
            json_print_to_file(final_list[2], obff, "gpt_failure_apps")
        except Exception as e:
            print("GPT FAILURE list print to file error")
            print(e)

    if my_args.pull_screenshots:
        pull_screenshots(final_list[1], obff)


if __name__ == '__main__':
    main()
