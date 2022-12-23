# dropbox-lambda-s3-dynamodb

This is my cloud computing class activity to deploy lambda function for mini version of dropbox

We manage file in s3 and using dynamodb for manage user permission.

For full information, please visit document.pdf in this repository

## How to

### Server side

- change bucket_name value in `lamba_function.py`
- deploy `lambda_function.py` in your aws account
- add api gateway as trigger

### Client side

- copy .env.example as .env and put your lambda function url inplace LAMBDA_FUNCTION_URL
- run pip3 install -r requirements.txt
- run python3 client.py
