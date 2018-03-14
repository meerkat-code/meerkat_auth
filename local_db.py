#!/usr/local/bin/python3
"""
This is a utility script to help set up some accounts for testing and
development. It create a registered, manager and root account for every country
currently under active development. NOTE: the passwords for every account is
just 'password'.

Run:
    `local_db.py --clear` (To get rid of any existing db)
    `local_db.py --setup` (To setup the db tables)
    `local_db.py --populate` (To populate the tables with accounts & roles)
    `local_db.py --list` (To list the acounts in the db)

If no flag is provided (i.e. you just run `local_db.py`) it will perform all
steps in the above order.

You can run these commands inside the docker container if there are database
issues.
"""

from os import path
import ast
from meerkat_auth import app
import argparse
import logging
from meerkat_auth.role import Role
from meerkat_auth.user import User

logging.basicConfig(level=logging.INFO)
logging.getLogger("boto3.resources.action").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)

parser = argparse.ArgumentParser()
parser.add_argument(
    '--setup',
    help='Setup the local dynamodb development database.',
    action='store_true'
)
parser.add_argument(
    '--list',
    help='List data from the local dynamodb development database.',
    action='store_true'
)
parser.add_argument(
    '--clear', help='Clear the local dynamodb development database.',
    action='store_true'
)
parser.add_argument(
    '--populate',
    help='Populate the local dynamodb development database.',
    action='store_true'
)
args = parser.parse_args()
args_dict = vars(args)

if all(arg is False for arg in args_dict.values()):
    logging.info("Re-starting the dev database.")
    for arg in args_dict:
        args_dict[arg] = True

if args.clear:
    app.db.drop_all_tables()


if args.setup:
    app.db.setup()

if args.populate:
    logging.info('Populating dev db')
    # Create some roles for each country.
    # TODO: Need a clever solution to match dev to deployment here.
    # Maybe we define roles for dev and deployment in a sngle file and import.
    countries = ['demo', 'rms']
    roles = []

    for country in countries:
        # Add some data for development
        roles += [
            Role(country, 'registered', 'A standard registered user', []),
            Role(country, 'admin',
                 'A manager with backend access.', ['registered']),
            Role(country, 'cd', 'Communicable disease access', []),
            Role(country, 'ncd', 'Non-Communicable disease access', []),
            Role(country, 'all', 'All disease access', ['cd', 'ncd']),
            Role(country, 'personal',
                 'A Personal account with access to account settings.', []),
            Role(country, 'root', 'Complete access',
                 ['admin', 'all', 'personal']),
            Role(country, 'emails', ' ', [], visible=['root']),

        ]

    # Create the jordan access network
    roles += [
        Role('jordan', 'reports', ' ', []),
        Role('jordan', 'foreigner', ' ', []),
        Role('jordan', 'dashboard', ' ', []),
        Role('jordan', 'clinic', ' ', ['reports', 'dashboard']),
        Role('jordan', 'directorate', ' ', ['clinic']),
        Role('jordan', 'central', ' ', ['directorate']),
        Role('jordan', 'pip', ' ', []),
        Role('jordan', 'foreign', ' ', []),
        Role('jordan', 'cd', ' ', ['pip', 'foreign']),
        Role('jordan', 'ncd', ' ', []),
        Role('jordan', 'mh', ' ', []),
        Role('jordan', 'all', ' ', ['cd', 'ncd', 'mh']),
        Role('jordan', 'admin', ' ', []),
        Role('jordan', 'personal', ' ', []),
        Role('jordan', 'refugee', ' ', []),
        Role('jordan', 'root', ' ', ['central',
                                     'all', 'admin', 'personal', 'refugee', 'foreigner']),
        Role('jordan', 'emails', ' ', [], visible=['root'])

    ]

    # Add the madagascar access network.
    for country in ['somalia', 'somaliland', 'southcentral', 'puntland', 'madagascar']:
        roles += [
            Role(country, 'reports', ' ', []),
            Role(country, 'dashboard', ' ', ['reports']),
            Role(country, 'explore', ' ', ['dashboard']),
            Role(country, 'download', ' ', ['explore']),
            Role(country, 'personal', ' ', []),
            Role(country, 'admin', ' ', ['personal']),
            Role(country, 'emails', ' ', [], visible=['root'])
        ]

    roles += [
        Role('somalia', 'ctc', ' ', []),
        Role('somalia', 'sc', ' ', []),
        Role('somalia', 'other', ' ', []),
        Role('somalia', 'all', ' ', ['ctc', 'sc', 'other']),
        Role('somaliland', 'ctc', ' ', []),
        Role('somaliland', 'sc', ' ', []),
        Role('somaliland', 'other', ' ', []),
        Role('somaliland', 'all', ' ', ['ctc', 'sc', 'other']),
        Role('southcentral', 'ctc', ' ', []),
        Role('southcentral', 'sc', ' ', []),
        Role('southcentral', 'other', ' ', []),
        Role('southcentral', 'all', ' ', ['ctc', 'sc', 'other']),
        Role('puntland', 'ctc', ' ', []),
        Role('puntland', 'sc', ' ', []),
        Role('puntland', 'other', ' ', []),
        Role('puntland', 'all', ' ', ['ctc', 'sc', 'other']),
        Role('somalia', 'puntland', ' ', []),
        Role('somalia', 'southcentral', ' ', []),
        Role('somalia', 'somaliland', ' ', []),
        Role('somalia', 'somalia', ' ', ['somaliland', 'puntland', 'southcentral']),
        Role('somalia', 'root', ' ', ['download', 'admin', 'all', 'somalia']),
        Role('somaliland', 'root', ' ', ['download', 'admin', 'all']),
        Role('puntland', 'root', ' ', ['download', 'admin', 'all']),
        Role('southcentral', 'root', ' ', ['download', 'admin', 'all']),
        Role('madagascar', 'root', ' ', ['download', 'admin'])
    ]

    roles += [
        Role('meerkat', 'slack', ' ', []),
        Role('meerkat', 'logging', ' ', []),
        Role('meerkat', 'hermes', ' ', ['slack']),
        Role('meerkat', 'admin', ' ', ['logging', 'hermes']),
        Role('meerkat', 'root', ' ', ['admin'])
    ]

    for role in roles:
        logging.debug(role.to_db())

    # Create registered, manager and root user objects for each country.
    users = []

    for country in countries:
        users += [
            User(
                '{}-cd'.format(country),
                'cd@{}test.org.uk'.format(country),
                ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
                 'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
                [country, country],
                ['registered', 'cd'],
                data={'name': {'val': 'Testy McTestface'}},
                state='new'
            )
        ]

    for country in countries:
        # Password for all dev accounts is just 'password'.
        users += [
            User(
                '{}-registered'.format(country),
                'registered@{}test.org.uk'.format(country),
                ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
                 'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
                [country],
                ['registered'],
                data={'name': {'val': 'Testy McTestface'}},
                state='new'
            ),
            User(
                '{}-admin'.format(country),
                'manger@{}test.org.uk'.format(country),
                ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
                 'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
                [country],
                ['admin'],
                data={'name': {'value': 'Mr Boss Man'}},
                state='new'
            )

        ]

    # Create some Jordan accounts
    users += [
        User(
            'jordan-reports',
            'reports@jordantest.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['jordan', 'jordan'],
            ['reports', 'all'],
            data={'name': {'value': 'Report Person'}},
            state='new'
        ), User(
            'jordan-clinic',
            'clinic@jordantest.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['jordan', 'jordan'],
            ['clinic', 'cd'],
            data={'name': {'value': 'Clinic Person'}},
            state='new'
        ), User(
            'jordan-central-admin',
            'central.admin@jordantest.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['jordan', 'jordan', 'jordan', 'jordan'],
            ['central', 'all', 'admin', 'personal'],
            data={'name': {'value': 'Central Administrator'}},
            state='new'
        ), User(
            'jordan-admin-cd',
            'central.admin@jordantest.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['jordan', 'jordan', 'jordan', 'jordan'],
            ['central', 'cd', 'admin', 'personal'],
            data={'name': {'value': 'Central Administrator'}},
            state='new'
        ), User(
            'jordan-admin-ncd',
            'central.admin@jordantest.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['jordan', 'jordan', 'jordan', 'jordan'],
            ['central', 'ncd', 'admin', 'personal'],
            data={'name': {'value': 'Central Administrator'}},
            state='new'
        ), User(
            'jordan-refugee',
            'refugee@jordantest.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['jordan', 'jordan'],
            ['refugee', 'admin'],
            data={'name': {'value': 'Central Administrator'}},
            state='new'
        ), User(
            'jordan-pip',
            'pip@jordantest.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['jordan', 'jordan'],
            ['pip', 'clinic'],
            data={'name': {'value': 'Pip user'}},
            state='new'
        )
    ]

    # Create some user accounts for specific countries.
    for country in ['madagascar', 'somalia', 'somaliland', 'puntland', 'southcentral']:
        users += [
            User(
                country + '-reports',
                'reports@madagascartest.org.uk',
                ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
                 'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
                [country],
                ['reports'],
                data={'name': {'value': 'Report Person'}},
                state='new'
            ), User(
                country + '-dashboard',
                'clinic@madagascartest.org.uk',
                ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
                 'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
                [country],
                ['dashboard'],
                data={'name': {'value': 'Dashboard Person'}},
                state='new'
            ), User(
                country + '-explore',
                'central.admin@madagascartest.org.uk',
                ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
                 'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
                [country],
                ['explore'],
                data={'name': {'value': 'Explore Person'}},
                state='new'
            ), User(
                country + '-download',
                'central.admin@madagascartest.org.uk',
                ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
                 'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
                [country],
                ['download'],
                data={'name': {'value': 'Download Person'}},
                state='new'
            ), User(
                country + '-admin-download',
                'central.admin@madagascartest.org.uk',
                ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
                 'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
                [country, country],
                ['download', 'admin'],
                data={'name': {'value': 'Central Administrator'}},
                state='new'
            )
        ]

    # Create a CTC account for somalia
    users += [User(
        'ctc',
        'ctc@test.org.uk',
        ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
        ['somalia', 'somalia'],
        ['ctc', 'dashboard'],
        data={'name': {'val': 'CTC User'}},
        state='new'
    ), User(
        'reports-som-ctc',
        'ctc@test.org.uk',
        ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
        ['somalia', 'somalia'],
        ['ctc', 'reports'],
        data={'name': {'val': 'CTC Reports'}, 'TOKEN_LIFE': {'val': '60'}},
        state='new'
    ), User(
        'reports-som-sc',
        'sc@test.org.uk',
        ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
        ['somalia', 'somalia'],
        ['sc', 'reports'],
        data={'name': {'val': 'SC Reports'}, 'TOKEN_LIFE': {'val': '60'}},
        state='new'
    )]

    # Create a location restricted account for somalia
    users += [User(
        'puntland',
        'puntland@test.org.uk',
        ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
        ['somalia', 'somalia', 'somalia'],
        ['puntland', 'download', 'other'],
        data={'name': {'val': 'Puntland User'}},
        state='new'
    ), User(
        'somaliland',
        'somaliland@test.org.uk',
        ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
        ['somalia', 'somalia', 'somalia'],
        ['somaliland', 'download', 'other'],
        data={'name': {'val': 'somaliland User'}},
        state='new'
    ), User(
        'southcentral',
        'southcentral@test.org.uk',
        ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
        ['somalia', 'somalia', 'somalia'],
        ['southcentral', 'download', 'other'],
        data={'name': {'val': 'southcentral User'}},
        state='new'
    ), User(
        'somalia',
        'somalia@test.org.uk',
        ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
        ['somalia', 'somalia'],
        ['download', 'other'],
        data={'name': {'val': 'somalia User'}},
        state='new'
    )]

    # Create an overall root acount with access to everything.
    root_countries = countries + [
        'jordan', 'madagascar', 'somalia',
        'meerkat', 'somaliland', 'southcentral', 'puntland'
    ]
    users += [User(
        'root',
        'root@test.org.uk',
        ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
        root_countries,
        ['root']*len(root_countries),
        data={'name': {'val': 'Supreme Omnipotent Overlord'}},
        state='new'
    )]

    # Create an account to authenticate email sending.
    users += [User(
        'report-emails',
        'report-emails@test.org.uk',
        ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
        countries + countries + ['jordan', 'jordan', 'jordan'] +
        ['madagascar', 'madagascar'] + ['somalia', 'somalia', 'somalia'],
        ['registered' for c in countries] +
        ['emails' for c in countries] + ['reports', 'emails', 'all'] +
        ['emails', 'reports'] + ['emails', 'reports', 'all'],
        state='new'
    )]
    # Create an account to authenticate email sending.
    users += [User(
        'server',
        'server@test.org.uk',
        ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
        ["meerkat"],
        ["hermes"],
        state='new'
    ), User(
        'slack',
        'slack@test.org.uk',
        ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
        ["meerkat"],
        ["slack"],
        state='new'
    )]
    try:
        # Get developer accounts from file to be inserted into local database.
        fpath = (path.dirname(path.realpath(__file__)) +
                 '/../.settings/accounts.cfg')
        devs_file = open(fpath, 'r+').read()
        devs = ast.literal_eval(devs_file) if devs_file else {}

        # Create the developer accounts
        for devuser, dev in devs.items():
            users += [User(
                dev['username'],
                dev['email'],
                dev['password'],
                countries + ['jordan', 'madagascar', 'somalia', 'meerkat'],
                ['root' for c in countries] + ['root', 'root', 'root', 'root'],
                data={'name': {
                    'val': '{} {}'.format(dev['first_name'], dev['last_name'])
                }},
                state='new'
            )]

    except Exception as e:
        logging.error('There has been an error with the developer\'s accounts...')
        logging.error(e)

    for user in users:
        logging.debug(user.to_db())

    logging.info('Populated dev db')

if args.list:
    logging.info("Listing all users")
    results = app.db.get_all(app.config['USERS'])
    logging.info("\n".join([str(User(**x)) for x in results]))
    logging.info("Listing all roles")
    results = app.db.get_all(app.config['ROLES'])
    logging.info("\n".join([str(Role(**x)) for x in results]))
