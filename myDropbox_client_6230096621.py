import requests

######### for this activity I have set response to be error if there are 'message' in response so another case is action complete
URL = 'https://kpyc78zcuf.execute-api.ap-southeast-1.amazonaws.com/default/dropboxFunction'

print('Welcome to myDropbox Application')
print('======================================================')
print('Please input command (newuser username password password, login')
print('username password, put filename, get filename, view, or logout).')
print('If you want to quit the program just type quit.')
print('======================================================')

current_username = ''
current_password = ''
if current_username == '':
    print('>>', end='')
else:
    print('['+current_username+']'+'>>', end='')
commands = input()


while True:
    BODY = {}

    if current_username != '':
        BODY['username'] = current_username
        BODY['password'] = current_password

    command_list = commands.split(' ')

    command = command_list[0]
    BODY['action'] = command

    #break the app if command is exit
    if command == 'quit':
        break

    #check if user using newuser command
    if command == 'newuser' and len(command_list) >= 4:
        if current_username != '':
            print('please logout first')
        else:
            username = command_list[1]
            password = command_list[2]
            confirmPassword = command_list[3]
            # check if password match
            if password == confirmPassword:
                print('create')
                BODY['username'] = username
                BODY['password'] = password
                response = requests.post(url = URL, json = BODY).json()
                if 'message' in response:
                    print(response['message'])
                else:
                    print('successfully created')
            else:
                print('password are not match')

    #check if user using login command
    elif command == 'login' and len(command_list) >= 3:
        if current_username != '':
            print('please logout first')
        else:
            print('login')
            username = command_list[1]
            password = command_list[2]
            BODY['username'] = username
            BODY['password'] = password
            response = requests.get(url = URL, json = BODY).json()
            if 'message' in response:
                print(response['message'])
            else:
                current_username = username
                current_password = password

    #check if user using logout command
    elif command == 'logout':
        print('logout')
        current_username = ''

    #check if user using share command
    elif command == 'share' and len(command_list) >= 3:
        print('share')
        filename = command_list[1]
        sharee = command_list[2]
        BODY['filename'] = filename
        BODY['sharee'] = sharee
        response = requests.put(url = URL, json = BODY).json()
        if 'message' in response:
            print(response['message'])
        else:
            print('share successfully')

    #check if user using view command
    elif command == 'view':
        print('view all your files')
        # get all files
        BODY['username'] = current_username
        response = requests.get(url = URL, json = BODY).json()
        if 'message' in response:
            print(response['message'])
        else:
            filesLists = response['fileLists']
            i = 1
            for file in filesLists:
                # we got object format
                print(i, '>> filename:', file['filename'], 'lastModifiedDate:', file['lastModifiedDate'], 'ownername:', file['username'])
                i += 1
            print('end of your files')
            
    # check if user input 2 argument
    elif len(command_list)  >= 2:
        filename = command_list[1]

        #check if user using put command
        if command == 'put':
            # upload file
            BODY['filename'] = filename

            # get the presigned url first
            response = requests.put(url=URL, json=BODY).json()
            print('put')
            if 'message' in response:
                print(response['message'])
            else:
                #upload file to the presigned url from response
                with open(filename, 'rb') as f:
                    files = {'file': (filename, f)}
                    http_response = requests.post(response['url'], data=response['fields'], files=files)
                    print('upload success')

        # check if user using get command
        elif command == 'get':
            print('get')
            BODY['filename'] = filename

            if len(command_list) == 3:
                BODY['sharer'] = command_list[2]

            # get the presigned url first
            response = requests.get(url = URL, json = BODY).json()

            # download file from presigned url
            if 'url' in response:
                file = requests.get(url = response['url'])
                open(filename, 'wb').write(file.content)

            #if there aren't url so that mean filename is invalid in s3 bucket
            elif 'message' in response:
                print(response['message'])

        #other more thaan 2 argument command is invalid command
        else:
            print('invalid command')

    #other command is invalid command
    else:
        print('invalid command')
    if current_username == '':
        print('>>', end='')
    else:
        print('['+current_username+']'+'>>', end='')
    commands = input()