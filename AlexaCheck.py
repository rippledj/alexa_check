# AlexaCheck.py
# Alexa Top 1 Million Websites Data Collection
# Description: Collects headers from Alexa List websites
# Author: Joseph Lee
# Email: joseph@ripplesoftware.ca
# Website: www.ripplesoftware.ca
# Github: www.github.com/rippledj/alexa_list

# Import modules
import os
import subprocess
import traceback
import time
from datetime import datetime
from multiprocessing import Process, Queue
import pycurl
import tldextract
from io import BytesIO
import re
from nslookup import Nslookup
import dns.resolver

# Import custom classes
import SQLProcessor
import AlexaLogger


# Get Alexa top 1M list: http://s3.amazonaws.com/alexa-static/top-1m.csv.zip


# Create a link queue with all site and return
def create_list_queue(args):

    # Include logger
    logger = AlexaLogger.logging.getLogger("Alexa_Database_Construction")

    print("-- Creating a link queue for all Alexa sites in list...")
    logger.info("-- Creating a link queue for all Alexa sites in list...")

    # Create a database connection
    db_conn = SQLProcessor.SQLProcess(database_args, args)
    db_conn.connect()
    # Get the highest number in the database
    next_pos, missing = db_conn.get_next_position(args)

    # Initialize a queue of queue's
    qq = []
    # Initialize a queue to fill with items
    list_queue = Queue()

    # Set the max size of the list queue
    if args['list_limit'] == None: max_count = args['max_queue_count']
    else: max_count = args['list_limit']

    # Open the csv file and make into list
    # First column is only rank, second is url
    with open(args['alexa_list'], "r") as infile:
        alexa_list = infile.readlines()
    print("Starting Alexa List size: " + str(len(alexa_list)))

    # Append all to the list
    size = 0
    count = 1
    for site in alexa_list:
        # Get the domain
        arr = site.split(",")
        # Only add the item if not processed
        if int(arr[0]) in missing or int(arr[0]) >= next_pos:
            print("[adding " + arr[-1].strip() + " to the list...]")
            list_queue.put({ "pos" : arr[0].strip(), "domain" : arr[-1].strip()})
            size += 1
            if count == max_count:
                # Put the list queue on to the qq
                qq.append(list_queue)
                time.sleep(0.2)
                # Reinitialize the queue
                list_queue = Queue()
                # Reset the counter
                count = 0
            # Increment the position
            count += 1
        # Print message for skipping item
        else: print("[skipping " + arr[-1].strip() + " from the list...]")

    # Append the last partially-filled queue
    qq.append(list_queue)
    # Return the qq
    print("-- Finished adding sites to link queue for all Alexa sites in list...")
    logger.info("-- Finished adding sites to link queue for all Alexa sites in list...")
    time.sleep(2)
    print("-- Queue Size: " + str(size))

    return qq


class Headers:

    def __init__(self):

        # Set the object nslookup
        self.nslookup = Nslookup()

        # Store headers as dict
        self.headers = {
            "cookies" : []
        }
        # Store entire header string
        self.header_str = ""
        # Store top level domain
        self.tld = None
        # Store subdomain
        self.ext = None
        # Store url with extension
        self.url = None
        # Store the alexa position
        self.position = None
        # Store the http return code
        self.http_code = None
        # Store the nslookup IP address
        self.ip = None
        # Store full nslookup response
        self.ip_full = None
        # Store MX records for domain
        self.mx = []

    # Accept the header stream from pycurl
    def display_header(self, header_line):
        header_line = header_line.decode('iso-8859-1')

        # Append the line to string
        self.header_str = self.header_str + header_line

        # Ignore all lines without a colon
        if ':' not in header_line:
            return

        # Break the header line into header name and value
        h_name, h_value = header_line.split(':', 1)

        # Remove whitespace that may be present
        h_name = h_name.strip()
        h_value = h_value.strip()
        h_name = h_name.lower() # Convert header names to lowercase
        # If line is cookie then append to cookies
        if h_name == 'set-cookie': self.headers['cookies'].append(h_value)
        # Append all other Header name and value.
        else: self.headers[h_name] = h_value

    # Get the http code from header string
    def get_http_return_code(self):
        first_line = self.header_str.split("\n")[0]
        if re.search(r' [\d]{3,}', first_line):
            self.http_code = re.search(r' [\d]{3,}', first_line).group(0)

    # Get the IP from nslookup
    def get_ip(self):
        try:
            # Set the uri with subdomain
            if "www." in self.url: uri = "www." + self.tld
            else: uri = self.tld
            print("-- Looking up IP for: " + uri)
            ip_rec = self.nslookup.dns_lookup(uri)
            if len(ip_rec.answer):
                self.ip = ip_rec.answer[0]
            #if len(ip_rec.response_full):
                #self.ip_full = ip_rec.response_full[0]
        except Exception as e:
            traceback.print_exc()
            logger.error("-- Error getting nslookup for: " + uri)
            logger.error(traceback.format_exc())

    # Get MX records as array
    def get_mx_records(self):
        # Set the uri with subdomain
        if "www." in self.url: uri = "www." + self.tld
        else: uri = self.tld
        print("-- Looking up MX for: " + uri)
        try:
            mx = dns.resolver.query(uri, 'MX')
            if len(mx):
                for item in mx:
                    #print(item.exchange)
                    self.mx.append(str(item.exchange))
        except Exception as e:
            #traceback.print_exc()
            logger.error("-- Error getting MX for: " + uri)
            logger.error(traceback.format_exc())

# Parse single Alexa site for
def parse_items_thread(database_args, args, qq):

    # Include logger
    logger = AlexaLogger.logging.getLogger("Alexa_Database_Construction")

    # Create a database connection
    db_conn = SQLProcessor.SQLProcess(database_args, args)
    db_conn.connect()
    args['db_conn'] = db_conn

    # Create a PyCurl object
    curl = pycurl.Curl()
    # Keep track of the number I'm on
    item_num = args['max_queue_count']

    # Loop through each queue item in qq
    for queue in qq:

        # Pull the queue item off
        list_queue = queue

        # Go through each link in link_queue
        while not list_queue.empty():

            # Get item from queue
            print("[ Process " + str(os.getpid()) + " is picking next item from queue...]")
            item = list_queue.get()
            domain = item["domain"]
            position = item["pos"]

            # Only process if not found in database already
            if args['db_conn'].all_already_scraped(len(args['schemes_and_subdomains']), domain, position) == False:

                for ext in args['schemes_and_subdomains']:

                    # Only process if not found in database already
                    if args['db_conn'].is_already_scraped(ext, domain, position) == False:

                        # Instantiate object
                        data_obj = Headers()

                        # Get headers using pycurl
                        try:

                            # Set some other information in the data object
                            data_obj.tld = domain
                            data_obj.ext = ext.replace("https://","").replace("http://", "")
                            data_obj.url = ext + domain
                            data_obj.position = int(position)

                            print("-- Checking " + ext + domain + " for HTTP headers...")
                            # Set URL value
                            curl.setopt(curl.URL, ext + domain)
                            b_obj = BytesIO()
                            #user_agent = '-H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.2403.89 Safari/537.36"'
                            #command = "curl " + user_agent + " -I https://" + domain
                            #print(command)
                            #output = subprocess.check_output(command, shell=True)
                            curl.setopt(pycurl.FOLLOWLOCATION, args['curl_follow_redirect'])
                            curl.setopt(pycurl.MAXREDIRS, args['curl_max_redirect'])
                            curl.setopt(pycurl.CONNECTTIMEOUT, args['curl_conn_timeout'])
                            curl.setopt(pycurl.TIMEOUT, args['curl_timeout'])
                            curl.setopt(curl.HEADERFUNCTION, data_obj.display_header)
                            curl.setopt(curl.WRITEDATA, b_obj)
                            curl.perform()

                            data_obj.get_http_return_code()
                            data_obj.get_ip()
                            # Only want to do this once since it's for domain and subdomain
                            if "https://" in data_obj.url: data_obj.get_mx_records()
                            #print('Header values:-')
                            #print(data_obj.headers)

                        except Exception as e:
                            data_obj.http_code = 0
                            print("[ ** HTTP header request failed to respond " + ext + domain + "...]")
                            traceback.print_exc()
                            logger.error("[ ** HTTP header request failed to respond " + ext + domain + "...]")
                            logger.error(traceback.format_exc())

                        # Store the results to database
                        args['db_conn'].store_headers_to_database(args, data_obj)
                        if len(data_obj.mx): args['db_conn'].store_mx_to_database(args, data_obj)

                        # Delete the object
                        del data_obj

    # End curl session
    curl.close()
    return

#
# Main function
#
if __name__ == "__main__":

    cwd = os.getcwd()
    alexa_list_filename = cwd + "/res/top-1m.csv"
    app_log_file = cwd + "/alexa_check.log"
    today_datetime = datetime.today().strftime('%Y-%m-%d')

    # Log levels
    log_level = 3 # Log levels 1 = error, 2 = warning, 3 = info
    stdout_level = 1 # Stdout levels 1 = verbose, 0 = non-verbose
    # Declare variables
    start_time = time.time()

    # Database args
    database_args = {
        "database_type" : "postgresql", # only postgresql available now
        "host" : "127.0.0.1",
        "port" : 5432, # PostgreSQL port
        "user" : "alexa",
        "passwd" : "n4T8tejYMmCHHbpn6s92V", # PostgreSQL password
        "db" : "alexa",
        "charset" : "utf8"
    }

    # Declare args
    args = {
        "log_level" : log_level,
        "stdout_level" : stdout_level,
        # I/0 Files
        "alexa_list" : alexa_list_filename,
        "app_log_file" : app_log_file,
        "list_limit" : None,
        "num_threads" : 20,
        "max_queue_count" : 32767,
        "max_count" : 100,
        "curl_conn_timeout" : 10,
        "curl_timeout" : 10,
        "curl_follow_redirect" : True,
        "curl_max_redirect" : 5,
        "use_threading" : True,
        "scrape_every_days" : 90,
        "database_args" : database_args,
        "schemes_and_subdomains" : [
            "http://",
            "http://www.",
            "https://",
            "https://www.",
        ]
    }

    # Setup logger
    AlexaLogger.setup_logger(args['log_level'], app_log_file)
    # Include logger
    logger = AlexaLogger.logging.getLogger("Alexa_Database_Construction")

    # Create a Queue to hold all sites
    try:
        qq = create_list_queue(args)
    except Exception as e:
        traceback.print_exc()

    # Create all processes and start
    processes = []
    for i in range(args['num_threads']):
        p = Process(target=parse_items_thread, args=(database_args, args, qq))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()

    print("-- Finished quering the Alexa top million for...")
    exit(0)
