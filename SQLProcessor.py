#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Alexa Check SQLProcessor
# Author: Joseph Lee
# Email: joseph@ripplesoftware.ca
# Website: www.ripplesoftware.ca
# Github: www.github.com/rippledj/alexa_check

import psycopg2
import traceback
import json
import AlexaLogger

class SQLProcess:

    # Initialize connection to database using arguments
    def __init__(self, db_args, args):

        # Pass the database type to class variable
        self.database_type = db_args['database_type']

        # Define class variables
        self._host = db_args['host']
        self._port = db_args['port']
        self._username = db_args['user']
        self._password = db_args['passwd']
        self._dbname = db_args['db']
        self._charset = db_args['charset']
        self._conn = None
        self._cursor = None
        self.table_list = None

    # Establish connection to the database
    def connect(self):

        logger = AlexaLogger.logging.getLogger("Alexa_Database_Construction")

        # Connect to PostgreSQL
        if self.database_type == "postgresql":

            if self._conn == None:
                # Get a connection, if a connect cannot be made an exception will be raised here
                self._conn = psycopg2.connect("host=" + self._host +  " dbname=" + self._dbname + " user=" + self._username + " password=" + self._password + " port=" + str(self._port))
                self._conn.autocommit = True

            if self._cursor == None:
                # conn.cursor will return a cursor object, you can use this cursor to perform queries
                self._cursor = self._conn.cursor()
                print("Connection to PostgreSQL database established.")
                logger.info("Connection to PostgreSQL database established.")


    # Store headers to database
    def store_headers_to_database(self, args, data_obj):

        print("** Storing " + data_obj.tld + " to database.")

        sql = "INSERT INTO alexa.headers "
        sql += "(pos, tld, url, ip, ip_full, http_code, header_string, header_json)"
        sql += "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

        values = (
            data_obj.position,
            data_obj.tld,
            data_obj.url,
            data_obj.ip,
            data_obj.ip_full,
            data_obj.http_code,
            data_obj.header_str,
            json.dumps(data_obj.headers)
        )

        self._cursor.execute(sql, values)


    # Check the database to see if the item is already processed
    def is_already_scraped(self, ext, domain, position):

        sql = """SELECT COUNT(*) as count FROM alexa.headers
        WHERE pos=%s
        AND url=%s"""
        values = (position, ext + domain)
        self._cursor.execute(sql, values)
        count = self._cursor.fetchone()
        # Return scraped status
        #print("Num found: " + str(count[0]))
        if count[0] == 0: return False
        else:
            print("-- Skipping previous entry: " + ext + domain)
            return True

    # Check the database to see if all items are already processed
    def all_already_scraped(self, num, domain, position):

        sql = """SELECT COUNT(*) as count FROM alexa.headers
        WHERE pos=%s
        AND tld=%s"""
        values = (position, domain)
        self._cursor.execute(sql, values)
        count = self._cursor.fetchone()
        # Return scraped status
        #print("Num found: " + str(count[0]))
        # Compare to expected number
        if count[0] < num: return False
        else:
            print("-- Skipping previous entry: " + domain)
            return True

    # Store mx to database
    def store_mx_to_database(self, args, data_obj):

        print("** Storing " + data_obj.tld + " to database.")

        sql = "INSERT INTO alexa.mx "
        sql += "(pos, domain, mx)"
        sql += "VALUES (%s, %s, %s)"

        values = (
            data_obj.position,
            data_obj.ext + data_obj.tld,
            data_obj.mx
        )

        self._cursor.execute(sql, values)
