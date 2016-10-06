#!/usr/local/bin/python3
"""
This is a utility script to help set up some accounts for testing and development.
It create a registered, manager and root account for every country currently under
active development. NOTE: the passwords for every account is just 'password'.

Run:
    `local_db.py --clear` (To get rid of any existing db)
    `local_db.py --setup` (To setup the db tables)
    `local_db.py --populate` (To populate the tables with accounts & roles)
    `local_db.py --list` (To list the acounts in the db)

If no flag is provided (i.e. you just run `local_db.py`) it will perform all steps
in the above order.

You can run these commands inside the docker container if there are database issues.
"""

import boto3, meerkat_auth, logging, argparse
from meerkat_auth.role import Role
from meerkat_auth.user import User

parser = argparse.ArgumentParser()
parser.add_argument('--setup', help='Setup the local dynamodb development database.', action='store_true')
parser.add_argument('--list', help='List data from the local dynamodb development database.', action='store_true')
parser.add_argument('--clear', help='Clear the local dynamodb development database.', action='store_true')
parser.add_argument('--populate', help='Populate the local dynamodb development database.', action='store_true')
args = parser.parse_args()
args_dict = vars(args)

if all(arg == False for arg in args_dict.values()):
    print( "Re-starting the dev database." )
    for arg in args_dict:
        args_dict[arg] = True

if args.clear:
    print('Cleaning the dev db.')
    db = boto3.resource('dynamodb', endpoint_url='http://dynamodb:8000', region_name='eu_west')
    response = db.Table(meerkat_auth.app.config['USERS']).delete()
    print( response )
    response = db.Table(meerkat_auth.app.config['ROLES']).delete()
    print( response )
    print('Cleaned the db.')

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
    #Create some roles for each country.
    #TODO: Need a clever solution to match dev to deployment here.
    #Maybe we define roles for dev and deployment in a sngle file and import.
    countries = ['demo','mad','rms']
    roles = []
    
    for country in countries:
        #Add some data for development
        roles += [
            Role( country, 'registered', 'A standard registered user', [] ),
            Role( country, 'admin', 'A manager with backend access.', ['registered'] ),
            Role( country, 'root', 'Complete access', ['admin'] )
        ]

    #Create the jordan access network
    #TODO:Find a way of syncing this with the live database.
    roles += [
        Role( 'jordan', 'reports', ' ', [] ),
        Role( 'jordan', 'clinic', ' ', ['reports'] ),        
        Role( 'jordan', 'directorate', ' ', ['clinic'] ),    
        Role( 'jordan', 'central', ' ', ['directorate'] ),
        Role( 'jordan', 'cd', ' ', [] ),
        Role( 'jordan', 'ncd', ' ', [] ),
        Role( 'jordan', 'mh', ' ', [] ),
        Role( 'jordan', 'all', ' ', ['cd','ncd','mh'] ),
        Role( 'jordan', 'admin', ' ', [] ),
        Role( 'jordan', 'personal', ' ', [] ),
        Role( 'jordan', 'root', ' ', ['central','all','admin','personal'] )
    ]

    for role in roles:
        print( role.to_db() )

    #Create registered, manager and root user objects for each country.
    users = []

    for country in countries:
        #Password for all dev accounts is just 'password'.
        users += [ 
            User( 
                '{}-registered'.format(country), 
                'registered@{}test.org.uk'.format(country),  
                ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
                'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
                [country],
                ['registered'],
                data={ 'name':{'val':'Testy McTestface'} },
                state='new'
            ),
            User(
                '{}-admin'.format(country), 
                'manger@{}test.org.uk'.format(country), 
                ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
                'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
                [country],
                ['admin'],
                data={ 'name':{ 'value':'Mr Boss Man' } },
                state='new'
            )

        ]

    #Create some Jordan accounts
    users += [
        User(
            'jordan-reports', 
            'reports@jordantest.org.uk', 
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
            'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['jordan', 'jordan'],
            ['reports', 'all'],
            data={ 'name':{ 'value':'Report Person' } },
            state='new'
        ), User(
            'jordan-clinic', 
            'clinic@jordantest.org.uk', 
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
            'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['jordan', 'jordan'],
            ['clinic', 'all'],
            data={ 'name':{ 'value':'Clinic Person' } },
            state='new'
        ), User(
            'jordan-central-admin', 
            'central.admin@jordantest.org.uk', 
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
            'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['jordan', 'jordan', 'jordan'],
            ['central', 'all', 'admin'],
            data={ 'name':{ 'value':'Central Administrator' } },
            state='new'
        )
    ]

    #Create an overall root acount with access to everything.
    users += [ User(
        'root', 
        'root@test.org.uk', 
        ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
        'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
        countries + ['jordan'],
        ['root' for c in countries] + ['root'],
        data={ 'name':{'val':'Supreme Omnipotent Overlord'} },
        state='new'
    )]
        
    for user in users:
        print( user.to_db() )

    

    print('Populated dev db')

if args.list:
    print('Listing data in the database.')
    db = boto3.resource(
            'dynamodb', 
            endpoint_url='http://dynamodb:8000', region_name='eu_west'
    )
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

