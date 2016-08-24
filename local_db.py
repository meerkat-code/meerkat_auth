#!/usr/local/bin/python3
import boto3, meerkat_auth, logging, argparse
from meerkat_auth.role import Role
from meerkat_auth.user import User

parser = argparse.ArgumentParser()
parser.add_argument('--setup', help='Setup the local dynamodb development database.', action='store_true')
parser.add_argument('--list', help='List data from the local dynamodb development database.', action='store_true')
parser.add_argument('--clear', help='Clear the local dynamodb development database.', action='store_true')
parser.add_argument('--populate', help='Populate the local dynamodb development database.', action='store_true')
args = parser.parse_args()

if args.setup:
    print('Creating dev db')

    #Create the client for the local database
    db = boto3.client('dynamodb', endpoint_url='http://dynamodb:8000', region_name='eu_west')

    #Create the required tables in the database
    response = db.create_table( 
        TableName=meerkat_auth.app.config['USERS'], 
        AttributeDefinitions=[{ 'AttributeName':'username', 'AttributeType':'S'}], 
        KeySchema=[{ 'AttributeName':'username', 'KeyType':'HASH' }], 
        ProvisionedThroughput={ 'ReadCapacityUnits':5, 'WriteCapacityUnits':5} 
    )

    print( response )

    response = db.create_table( 
        TableName=meerkat_auth.app.config['ROLES'], 
        AttributeDefinitions=[
            { 'AttributeName':'country', 'AttributeType':'S'},
            { 'AttributeName':'role', 'AttributeType':'S'}
        ], 
        KeySchema=[
            { 'AttributeName':'country', 'KeyType':'HASH' },
            { 'AttributeName':'role', 'KeyType':'RANGE' }
        ], 
        ProvisionedThroughput={ 'ReadCapacityUnits':5, 'WriteCapacityUnits':5} 
    )

    print( response )

if args.populate:
    print('Populate dev db')
    #Add some data for development
    roles = [
        Role( 'demo', 'registered', 'A standard registered user', [] ),
        Role( 'demo', 'manager', 'A manager with backend access.', ['registered'] ),
        Role( 'demo', 'root', 'Complete access', ['manager'] )
    ]
    for role in roles:
        print( role.to_db() )

    users = [ 
        User( 
            'registered', 
            'registered@test.org.uk', 
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
            'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['demo'],
            ['registered'],
            data={ 'name':{'value':'Testy McTestface'} },
            state='new'
        ),
        User(
            'manager', 
            'manager@test.org.uk', 
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
            'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['demo'],
            ['manager'],
            data={ 'name':{ 'value':'Mr Boss Man' } },
            state='new'
        ),
        User(
            'root', 
            'root@test.org.uk', 
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
            'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['demo'],
            ['root'],
            data={ 'name':{'value':'Supreme Omnipotent Overlord'} },
            state='new'
        )
    ]
    for user in users:
        print( user.to_db() )

    print('Populated dev db')

if args.list:
    print('Listing data in the database.')
    db = boto3.resource('dynamodb', endpoint_url='http://dynamodb:8000', region_name='eu_west')
    try:
        accounts = db.Table(meerkat_auth.app.config['USERS']).scan().get("Items",[])

        if accounts:
            print( "Dev acounts created:" )
            for item in accounts:
                print( "  " + str(User.from_db(item["username"])) )
        else:
            print( "No dev accounts exist." )
        roles = db.Table(meerkat_auth.app.config['ROLES']).scan().get("Items",[])
        if roles:
            print( "Dev roles created:" )
            for item in roles:
                print( "  " + str(Role.from_db(item["country"], item["role"])) )
        else:
            print( "No dev roles exist." )
    except Exception as e:
        print("Listing failed. Has database been setup?")

if args.clear:
    print('Cleaning the dev db.')
    db = boto3.resource('dynamodb', endpoint_url='http://dynamodb:8000', region_name='eu_west')
    response = db.Table(meerkat_auth.app.config['USERS']).delete()
    print( response )
    response = db.Table(meerkat_auth.app.config['ROLES']).delete()
    print( response )
    print('Cleaned the db.')

