import os 
import json
import boto3

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
    #Initialize rules list
    rules = []
    #Instantiate client with CWL
    client = boto3.client('logs', region_name='us-east-1')
    
    with open(file_path) as f:
        data = json.load(f)
        # CAREFULLY DECONSTRUCTED from serif format
        rules = data['runs'][0]['tool']['driver']['rules']

    #Check if CWL stream is created
    response = client.create_log_stream(
        logGroupName=cwl_group,
        logStreamName=cwl_stream
    )

    if not response:
        putResponse = client.put_log_events(
            logGroupName=cwl_group,
            logStreamName=cwl_stream,
            # Include repo, and branch, and user
            logEvents=[
                {
                    'Repository': 123,
                    'Branch': 'branch1',
                    'User': 'user1',
                    'Rules': rules
                },
            ]
        )

    

if __name__ == "__main__":
    main()
