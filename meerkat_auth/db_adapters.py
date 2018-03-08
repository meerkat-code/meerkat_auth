import boto3
import psycopg2
import logging
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import sql
from meerkat_auth import app
from psycopg2.extras import Json


class DynamoDBAdapter():

    def __init__(self):
        self.structure = {
            app.config['ROLES']: {
                "TableName": app.config['ROLES'],
                "AttributeDefinitions": [
                    {'AttributeName': 'country', 'AttributeType': 'S'},
                    {'AttributeName': 'role', 'AttributeType': 'S'}
                ],
                "KeySchema": [
                    {'AttributeName': 'country', 'KeyType': 'HASH'},
                    {'AttributeName': 'role', 'KeyType': 'RANGE'}
                ],
                "ProvisionedThroughput": {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            },
            app.config['USERS']: {
                "TableName": app.config['USERS'],
                "AttributeDefinitions": [
                    {'AttributeName': 'username', 'AttributeType': 'S'}
                ],
                "KeySchema": [
                    {'AttributeName': 'username', 'KeyType': 'HASH'}
                ],
                "ProvisionedThroughput": {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }
        }
        self.conn = boto3.resource(
            'dynamodb',
            endpoint_url=app.config['DB_URL'],
            region_name='eu-west-1'
        )

    def drop(self):
        logging.info('Cleaning the dev db.')

        try:
            response = self.conn.Table(app.config['USERS']).delete()
            logging.debug(response)
        except Exception as e:
            logging.error(e)
            logging.error('There has been error, probably because no tables'
                          'currently exist. Skipping the clean process.')

        try:
            response = self.conn.Table(app.config['ROLES']).delete()
            logging.debug(response)
        except Exception as e:
            logging.error(e)
            logging.error('There has been error, probably because no tables'
                          'currently exist. Skipping the clean process.')

        logging.info('Cleaned the db.')

    def setup(self):
        logging.info('Creating dev db')
        for table, structure in self.structure.items():
            response = self.conn.create_table(**structure)
            logging.debug(response)

    def read(self, table, keys, attributes=[]):
        args = {'Key': keys}
        if attributes:
            args['ProjectionExpression'] = ", ".join(attributes)
        table = self.conn.Table(table)
        return table.get_item(**args).get('Item', None)

    def write(self, table, keys, attributes):
        for key, value in attributes.items():
            attributes[key] = {'Value': value, 'Action': 'PUT'}
        table = self.conn.Table(table)
        return table.update_item(
            Key=keys,
            AttributeUpdates=attributes
        )

    def delete(self, table, keys):
        self.table = self.conn.Table(table)
        return table.delete_item(Key=keys)

    def get_all(self, table, conditions={}, attributes=[]):
        table = self.conn.Table(table)

        # Assemble scan arguments programatically, by building a dictionary.
        kwargs = {}

        # Include AttributesToGet if any are specified.
        # By not including them we get them all.
        if attributes:
            kwargs["AttributesToGet"] = attributes

        if not conditions:
            # If no conditions are specified, get all users and return as list.
            return table.scan(**kwargs).get("Items", [])

        else:
            items = []
            # Load data separately for each country
            # ...because Scan can't perform OR on CONTAINS
            for field, values in conditions:
                kwargs["ScanFilter"] = {
                    field: {
                        'AttributeValueList': values,
                        'ComparisonOperator': 'CONTAINS'
                    }
                }
                items += table.scan(**kwargs).get("Items", [])

            # Return a list of results without duplicates
            return [dict(t) for t in set([tuple(d.items()) for d in items])]


class PostgreSQLAdapter():

    def __init__(self):
        self.structure = {
            app.config['USERS']: [
                ("username", sql.SQL("username VARCHAR(50) PRIMARY KEY")),
                ("data",  sql.SQL("data JSON"))
            ],
            app.config['ROLES']: [
                ("country", sql.SQL("country VARCHAR(50)")),
                ("role", sql.SQL("role VARCHAR(50)")),
                ("data", sql.SQL("data JSON"))
            ]
        }

    def drop(self):
        try:
            logging.info("Dropping tables")
            conn = psycopg2.connect(
                dbname="meerkat_auth",
                user="postgres",
                host="db"
            )

            for table in self.structure.keys():
                conn.cursor().execute("DROP TABLE {};".format(table))
                conn.commit()

            conn.close()

        except psycopg2.ProgrammingError:
            logging.info("No database exists to drop.")

    def setup(self):
        # TODO: Backoff until postgres container running.
        self._create_db()
        self._create_tables()

    def list(self):
        for table in self.structure.keys():
            logging.info("Listing all records in {} table".format(table))
            cur = self.conn().cursor()
            cur.execute(sql.SQL("SELECT data from {}").format(
                sql.Identifier(table)
            ))
            results = [x[0] for x in cur.fetchall()]
            cur.close()
            logging.info(results)

    def _create_db(self):
        try:
            logging.info("Checking if db exist.")
            self.conn = psycopg2.connect(
                dbname="meerkat_auth",
                user="postgres",
                host="db"
            )
            logging.info("DB exists.")

        except psycopg2.OperationalError:
            logging.info("DB needs to be created.")
            conn = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                host="db"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            conn.cursor().execute("CREATE DATABASE meerkat_auth")
            conn.commit()
            conn.close()
            self.conn = psycopg2.connect(
                dbname="meerkat_auth",
                user="postgres",
                host="db"
            )
            logging.info("DB created and connection established.")
            self._create_tables()

    def _create_tables(self):
        for table, structure in self.structure.items():
            # Only create non-existant tables, so first check if table exists.
            try:
                logging.info("Checking if table {} exists.".format(table))
                cur = self.conn.cursor()
                cur.execute(sql.SQL("SELECT * FROM {} LIMIT 1;").format(
                    sql.Identifier(table)  # Always protect constructed SQL
                ))
                logging.info("Table {} exists.".format(table))

            except psycopg2.ProgrammingError:
                logging.info("Table {} needs to be created.".format(table))
                # Construct secure SQL query.
                structure = sql.SQL(", ").join(map(lambda x: x[1], structure))
                query = sql.SQL("CREATE TABLE {} ({});").format(
                    sql.Identifier(table),
                    structure
                )
                logging.debug("Create query: ".format(query.as_string(self.conn)))

                # Create a cursor and execute the table creation DB query.
                self.conn.rollback()
                cur = self.conn.cursor()
                cur.execute(query)
                self.conn.commit()

                logging.info("Table {} created".format(table))

    def read(self, table, key, attributes=[]):
        # Securely SQL stringify the attributes
        if attributes:
            tmp = [sql.SQL("data->>{}").format(sql.Literal(a)) for a in attributes]
            attributes = sql.SQL(", ").join(tmp)
        else:
            attributes = sql.SQL("data")

        # Securely SQL stringify the conditions
        conds = []
        for k, v in key.items():
            conds += [sql.SQL("{}={}").format(sql.Identifier(k), sql.Literal(v))]
        conditions = sql.SQL(" AND ").join(conds)

        # Form the secure SQL query
        query = sql.SQL("SELECT {} from {} where {};").format(
            attributes,
            sql.Identifier(table),
            conditions
        )
        logging.debug("Read query: {}".format(query.as_string(self.conn)))

        # Get and return the db result if it exists.
        # Function only searches on keys so should always be single result
        cur = self.conn.cursor()
        cur.execute(query)
        result = cur.fetchone()
        cur.close()
        if result:
            return result[0]
        else:
            return None  # The result may not exist

    def write(self, table, key, attributes):
        # Add the key data to the json blob.
        attributes = {**key, **attributes}
        # Stringify the insert data
        data = {**key, 'data': Json(attributes)}
        values = sql.SQL(", ").join(map(
            lambda x: sql.Literal(data[x[0]]),
            self.structure[table]
        ))

        # Securely build sql query to avoid sql injection.
        query = sql.SQL("INSERT INTO {} VALUES ({});").format(
            sql.Identifier(table),
            values
        )
        logging.debug("Write query: {}".format(query.as_string(self.conn)))

        # Insert the data
        cur = self.conn.cursor()
        cur.execute(query)
        self.conn.commit()
        cur.close()

    def delete(self, table, key):
        # Securely SQL stringify the conditions
        conditions = sql.SQL(" AND ").join(map(
            lambda k, v: sql.SQL("{}={}").format(sql.Identifier(k), sql.Literal(v)),
            key.items()
        ))

        # Securely build sql query to avoid sql injection.
        query = sql.SQL("DELETE from {} where {};").format(
            sql.Identifier(table),
            conditions
        )
        logging.debug("Delete query: {}".format(query.as_string(self.conn)))

        # Execute the delete query
        cur = self.conn.cursor()
        cur.execute(query)
        self.conn.commit()
        cur.close()

    def get_all(self, table, conditions={}, attributes=[]):
        # Securely compose sql list of attributes.
        if attributes:
            attributes = sql.SQL(", ").join(map(
                lambda x: sql.SQL("data->>{}").format(sql.Literal(x)),
                attributes
            ))
        else:
            attributes = sql.SQL("data")

        # Securely compose sql list of conditions.
        for field, values in conditions:
            condition = sql.SQL(" where data->>{} in ({});").format(
                sql.Identifier(field),
                sql.SQL(", ").join([sql.Literal(x) for x in values])
            )
        else:
            condition = sql.SQL("")

        # Securely build sql query to avoid sql injection.
        query = sql.SQL("SELECT {} from {}{};").format(
            attributes,
            sql.Identifier(table),
            condition
        )
        logging.debug("Read query: {}".format(query.as_string(self.conn)))

        # Execute and fetch only JSON data as a list of dicts
        # (Don't need key data as it is merged into JSON data during db write.)
        cur = self.conn.cursor()
        cur.execute(query)
        results = cur.fetchall()
        results = [x[0] for x in results]
        cur.close()
        return results