import os 
import json
import boto3
import time
import requests

def main():
    # Input Variables
    # AWS Credentials
    AWS_KEY_ID = os.environ["INPUT_AWS_KEY_ID"]
    AWS_KEY_SECRET = os.environ["INPUT_AWS_KEY_SECRET"]
    #File path of tfsec report
    file_path = os.environ["INPUT_REPORT"]
    # CWL Group
    cwl_group = os.environ["INPUT_CWL_GROUP"]
    # CWL Stream
    cwl_stream = os.environ["INPUT_CWL_STREAM"]
    #Get github token
    token = os.environ['INPUT_GITHUB_TOKEN']
    branch = os.environ["GITHUB_REF"]
    repository = os.environ["GITHUB_REPOSITORY"]

    #Github environment variables
    repository = os.environ["GITHUB_REPOSITORY"]
    author = os.environ["GITHUB_ACTOR"]
    commit = os.environ["GITHUB_SHA"]
    branch = os.environ["GITHUB_REF"]
    #Check if pr
    try:
        head = os.environ["GITHUB_HEAD_REF"]
        base = os.environ["GITHUB_BASE_REF"]
    except:
        print('[-] Not a PR... skipping comments')
        head = ''
        base = ''
    #Initialize rules list
    rules = []
    #Instantiate client with CWL
    client = boto3.client(
                            'logs', 
                            region_name='us-east-1', 
                            aws_access_key_id=AWS_KEY_ID, 
                            aws_secret_access_key=AWS_KEY_SECRET
                        )
    
    with open(file_path) as f:
        data = json.load(f)
        # CAREFULLY DECONSTRUCTED from serif format
        rules = data['runs'][0]['tool']['driver']['rules']

    #TODO: Check if PR and comment rules
    if head and base:
        output = commentRules(rules, token, branch, repository, commit)
    else:
        print('[-] No head or base ref, not a PR...')
    
    #Check if CWL stream is created
    try:
        client.create_log_stream(
            logGroupName=cwl_group,
            logStreamName=cwl_stream
        )
    except:
        print(f"[-] Log Stream, {cwl_stream}, already exists")

    # Build dir to send
    message = {}
    message['Repository'] = repository
    message['Branch'] = branch
    message['User'] = author
    message['Commit'] = commit
    message['Rule_Count'] = len(rules) #Get number of rules
    message['Rules'] = rules

    # Get stream status
    response = client.describe_log_streams(
        logGroupName=cwl_group,
        logStreamNamePrefix=cwl_stream
    )

    # Get current timestamp
    timestamp = int(round(time.time() * 1000))

    event_log = {
        'logGroupName': cwl_group,
        'logStreamName': cwl_stream,
        'logEvents': [
            {
                'timestamp': timestamp, 
                'message': json.dumps(message)
            }
        ]
    }

    if 'uploadSequenceToken' in response['logStreams'][0]:
           event_log.update({'sequenceToken': response['logStreams'][0] ['uploadSequenceToken']})

    putResponse = client.put_log_events(**event_log)

    
    print(f'[-] Sent log event to {cwl_group} / {cwl_stream}')

def commentRules(rules, token, branch, repository, commit):
    #Get pr number
    ref = os.environ["GITHUB_REF"]
    pr_num = ref.split('/')[2]
    owner = repository.split('/')[0]
    repo_name = repository.split('/')[1]
    query_url = f"https://api.github.com/repos/{repository}/pulls/{pr_num}/reviews"
    #TODO: Get current comments and compare. Drop rule from rules if match
    params = {
            "owner": owner,
            "repo": repo_name,
            "pull_number": pr_num,
    }
    headers = {'Authorization': f'token {token}'}
    comment_response = requests.post(query_url, headers=headers, data=json.dumps(params))
    current_comments = []
    for comment in comment_response:
        print(comment)
        print(type(comment))
        current_comments.append(comment['body'])
    #Iterate over rules and comment
    net_rules = []
    for rule in rules:
        if rule not in current_comments:
            print(f"[-] {rule} not in comments, adding...")
            net_rules.append(rule)

    print('[-] Commenting broken rules')
    for rule in net_rules:
        body = rule['shortDescription']['text']
        params = {
            "owner": owner,
            "repo": repo_name,
            "pull_number": pr_num,
            "event": 'COMMENT',
            "body": body
        }
        print(params)
        headers = {'Authorization': f'token {token}'}
        r = requests.post(query_url, headers=headers, data=json.dumps(params))
        print(r.status_code)
    

if __name__ == "__main__":
    main()
