import json
import boto3
import datetime
from boto3.dynamodb.conditions import Key

print('Loading function')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

bucket_name = 'your_bucket_name'

def lambda_handler(event, context):
    body = json.loads(event['body'])
    
    ### check if body contain action, username and password
    if ('action' not in body) or ('username' not in body) or ('password' not in body):
        return json.dumps({'message': 'Unauthorized'})
        
    
    action = body['action']
    username = body['username']
    password = body['password']
    
    ### initialize table instance
    usersTable = dynamodb.Table('myDropboxUsers')
    itemOwnershipsTable = dynamodb.Table('myDropboxItemOwnerships')
    sharePairsTable = dynamodb.Table('myDropboxSharePairs')
    pairToItemsTable = dynamodb.Table('myDropboxPairToItems')
    
    ### find user from username
    userRes = usersTable.get_item(Key={'username': username})
    
    if action == 'newuser':
        ### if action is newuser the response should be not found the username
        if 'Item' in userRes:
            return json.dumps({'message': 'username is already exist'})
        ### username cannot contain /
        if '/' in username:
            return json.dumps({'message': 'username cannot include /'})
        
        ### username can be create
        newuser = {'username': username, 'password': password}
        usersTable.put_item(Item=newuser)
        return json.dumps({})
    
    ### validate password every time ( feel like simple jwt)
    if 'Item' not in userRes:
        return json.dumps({'message': 'No username exist'})
    
    ### error if password not match
    if userRes['Item']['password'] != password:
        return json.dumps({'message': 'Unauthorized'})
    
    ### if login complete return empty response
    if action == 'login':
        return json.dumps({})
        
    if action == 'view':
        username = body["username"]
        fileLists = []
        
        ### get own filename lists
        itemOwnershipRes = itemOwnershipsTable.query(KeyConditionExpression=Key('username').eq(username))
        fileLists += itemOwnershipRes['Items']
        
        ### find sharePairs which contain this username
        sharePairListsRes = sharePairsTable.query(KeyConditionExpression=Key('sharee').eq(username))
        for sharePair in sharePairListsRes['Items']:
            sharePairKey = sharePair['sharePairKey']
            
            ### query pairToItem filenames
            sharer = sharePair['sharer']
            pairToItemRes = pairToItemsTable.query(KeyConditionExpression=Key('sharePairKey').eq(sharePairKey))
            pairToItems = pairToItemRes['Items']
            toQueryFilenames = []
            for pair in pairToItems:
                toQueryFilenames.append(pair['filename'])
                
            ### query all sharer item from itemOwnershipsTable
            itemOwnershipRes = itemOwnershipsTable.query(KeyConditionExpression=Key('username').eq(sharer))
            
            ### put all match filename from sharer to pairToItem toQuery filenames
            for item in itemOwnershipRes['Items']:
                if item['filename'] in toQueryFilenames:
                    fileLists.append(item)
                    
        return json.dumps({"fileLists": fileLists})
    
    ### other action are need filename to perform action
    if 'filename' not in body:
        return json.dumps({'message': 'filename not found'})
        
    filename = body['filename']
    s3_filename = username + '/' + filename
    
    if action == 'put':
        ### set new latest modified date
        lastModifiedDate = datetime.datetime.now().isoformat()
        newItem = {'username': username, 'filename': filename, 'lastModifiedDate': lastModifiedDate}
        
        ### send presigned url for upload file to bucket
        itemOwnershipsTable.put_item(Item=newItem)
        return s3.generate_presigned_post(Bucket=bucket_name, Key=s3_filename, ExpiresIn=10)
        
    ### check if there are file to get/share
    found = False
    userRes = itemOwnershipsTable.get_item(Key={'username': username, 'filename': filename})
    if 'Item' in userRes:
        found = True
    
    res = {}
        
    if action == 'get':
        if found and 'sharer' not in body:
            res['url'] = s3.generate_presigned_url(
                ClientMethod='get_object', 
                Params={'Bucket': bucket_name, 'Key': s3_filename},
                ExpiresIn=10)
        
        if 'sharer' in body:
            ### find sharePair are exists or not
            sharer = body['sharer']
            sharePairKeyRes = sharePairsTable.get_item(Key={'sharee': username, 'sharer': sharer})
            if 'Item' not in sharePairKeyRes:
                res = {'message':'no access to this user file/ there are no user have this username'} 
            else:
                ### find that sharePair are contain filename or not
                sharePairKey = sharePairKeyRes['Item']['sharePairKey']
                pairToItemRes = pairToItemsTable.get_item(Key={'sharePairKey': sharePairKey, 'filename': filename})
                if 'Item' not in pairToItemRes:
                    ### although sharee contain same filename as sharer we would change our res and remove url
                    res = {'message': 'no access to this file/ there are no file to get'} 
                else:
                    ### successfully found filename and generate url
                    found = True
                    s3_filename = sharer + '/' + filename
                    res['url'] = s3.generate_presigned_url(
                        ClientMethod='get_object', 
                        Params={'Bucket': bucket_name, 'Key': s3_filename},
                        ExpiresIn=10)
        
        elif not found:
            ### set message for file not found in any case
            res['message'] = 'file not found'
                    
        return json.dumps(res)
        
    if not found:
        ### validate for share action
        return json.dumps({'message': 'file not found'})
        
    if action == 'share':
        ### check if there sharee username to share or not
        foundSharee = False
        if 'sharee' in body:
            sharee = body['sharee']
            shareeFromTable = usersTable.get_item(Key={'username': sharee})
            if 'Item' in shareeFromTable:
                foundSharee = True
        if not foundSharee:        
            return json.dumps({'message': 'sharee not found'})
        
        ### create new sharePair and save to it table
        sharePairKey = sharee + '/' + username
        newSharePair = {'sharee': sharee, 'sharer': username, 'sharePairKey': sharePairKey}
        sharePairsTable.put_item(Item=newSharePair)
        
        ### create new pairToItem and save to it table
        newPairToItem = {'sharePairKey': sharePairKey, 'filename': filename}
        pairToItemsTable.put_item(Item=newPairToItem)
        return json.dumps({'message': 'successfully shared file'})
    
    return json.dumps({error:'command invalid'})
            