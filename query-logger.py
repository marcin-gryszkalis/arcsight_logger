#!/usr/bin/python
# mg@fork.pl
# https://github.com/marcin-gryszkalis/arcsight_logger

import suds
from suds.xsd.doctor import Import, ImportDoctor
from datetime import datetime, timedelta
from dateutil import parser
import time, sys
import pprint
import getopt
import ConfigParser
import base64
import signal
import sys
import os
import logging
import re

procstart = time.time()

def sigint_handler(signal, frame):
    log("Query interrupted")
    global token
    global login_client
    if token:
        login_client.service.logout(token)
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

def hms_string(sec_elapsed):
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = int(sec_elapsed % 60)
    return "{}:{:>02d}:{:>02d}".format(h, m, s)

def log(s):
    #nowdt = datetime()
    now = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    print >>sys.stderr,"%s %s" % (now, s)

def parsetime(s):
    return int(time.mktime(parser.parse(s, dayfirst=True, yearfirst=False, fuzzy=True).timetuple())) * 1000

# command line
def usage():
    print >>sys.stderr, """Usage:
    help:    %s -h
    search:  %s [-v] [-D] -l logger -q query -s starttime [-e endtime] [-t step]
    report:  %s [-v] [-D] -l logger -r report-id -s starttime [-e endtime] [-f (csv|pdf)]
        [--scanlimit=nnn] [--resulttowlimit=nnn]
        [--reportdevices=sss] [--reportdevicegroups=sss] [--reportstoragegroups=sss]
    devices: %s [-v] [-D] -l logger -d
    """ % (sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0])

try:
    optlist, args = getopt.getopt(sys.argv[1:], 'l:s:e:q:r:t:f:dhvD', ['help', 'scanlimit=', 'resulttowlimit=','reportdevices=','reportdevicegroups=','reportstoragegroups='])
except getopt.GetoptError as err:
    log(str(err))
    usage()
    sys.exit(2)

verbose = False
servicedebug = False
sudsdebug = False
logger_id = False
query = False
report_id = False
starttime = False
endtime = False
step=1000
scanlimit=0
resulttowlimit=0
reportdevices="null"
reportdevicegroups="null"
reportstoragegroups="null"
reportparameters=""
reportformat="CSV"

for o, a in optlist:
#    log("(%s)=(%s)" % (o,a))
    if o == "-D":
        sudsdebug = True
    elif o == "-v":
        verbose = True
    elif o in ("-h", "--help"):
        usage()
        sys.exit()
    elif o in ("-d"):
        servicedebug = True
    elif o in ("-l"):
        logger_id = a
    elif o in ("-q"):
        query = a
    elif o in ("-r"):
        report_id = a
    elif o in ("-s"):
        starttime = a
    elif o in ("-e"):
        endtime = a
    elif o in ("-t"):
        step = a if a < 10000 else 1000
    elif o in ("--scanlimit"):
        scanlimit = a
    elif o in ("--resulttowlimit"):
        resulttowlimit = a
    elif o in ("--reportdevices"):
        reportdevices = a
    elif o in ("--reportdevicegroups"):
        reportdevicegroups = a
    elif o in ("--reportstoragegroups"):
        reportstoragegroups = a
    elif o in ("-f"):
        reportformat = a
    else:
        assert False, "unhandled option"

# validation
if (not logger_id or (not query and not report_id and not servicedebug)):
    usage()
    sys.exit(2)

if (report_id and (reportformat != "csv" and reportformat != "pdf")):
    log("Error: invalid report format")
    usage()
    sys.exit(2)

# config file
Config = ConfigParser.ConfigParser()
Config.read(['/etc/logger.ini', os.path.expanduser('~/.logger.ini'), './logger.ini'])
if (not Config.has_section("credentials")):
    log("Error: cannot read logger.ini")
    sys.exit(2)

# optionally stop veryfying SSL certs
invalidssl = Config.get("options", "accept_invalid_ssl")
if re.match('yes', invalidssl, flags=re.IGNORECASE):
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context


user = Config.get("credentials", "user")
password = Config.get("credentials", "password")

IP = Config.get("loggers", logger_id)
port = 443
server =  "https://%s:%s/soap/services/" % (IP,port)

log("logger: %s" % server)

# SOAP URLs
xsd = "http://www.arcsight.com/logger/xsd"
xsd_login = 'http://domain.login.webservices.logger.arcsight.com/xsd'
xsd_search = 'http://domain.search.webservices.logger.arcsight.com/xsd'
xsd_report = 'http://domain.reports.webservices.logger.arcsight.com/xsd'
login = "%sLoginService/LoginService.wsdl" % server
search = "%sSearchService/SearchService.wsdl" % server
report = "%sReportService/ReportService.wsdl" % server

imp = Import(xsd)
imp.filter.add(xsd_login)
doctor = ImportDoctor(imp)

if sudsdebug:
    log("Debug mode enabled")
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('suds.client').setLevel(logging.DEBUG)
    logging.getLogger('suds.transport').setLevel(logging.DEBUG)
    logging.getLogger('suds.xsd.schema').setLevel(logging.DEBUG)
    logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)


# login
login_client = suds.client.Client(url=login, doctor=doctor, location=login)

token = login_client.service.login(user, password)
if not token:
    log("Error: failed to log in")
    exit(1)

api_version = login_client.service.getVersion()
log("API version: %s" % (api_version))


if (query or report_id):
    log("time range: %s -- %s" % (starttime, endtime or "Now"))
    start = parsetime(starttime)
    end   = parsetime(endtime) if endtime else int(time.time()) * 1000

if (query):

    log("query: %s" % query)
    log("step: %s" % step)

    imp.filter.add(xsd_search)
    doctor = ImportDoctor(imp)

    # search
    client = suds.client.Client(url=search, doctor=doctor, location=search)
    search = client.service.startSearch(query, start, end, token)

    #try:
    totali = 0
    while client.service.hasMoreTuples(token):
        tuples = client.service.getNextTuples(step,10000,token)

        diff = time.time()-procstart
        if diff == 0: diff = 1
        totali = totali + len(tuples)
        log("extracted %d new rows, total %d rows (%.2f/s), %s elapsed" % (len(tuples), totali, totali/diff, hms_string(diff)))

        for  t in tuples:
            print (t[0][2]).encode('utf8')
    #
    # except:
    #         print "Stopping..."

    client.service.endSearch(token)

elif (report_id): # report mode

    imp.filter.add(xsd_report)
    doctor = ImportDoctor(imp)

    client = suds.client.Client(url=report, doctor=doctor, location=report)
    client.set_options(timeout=600)
    qreport = client.service.runReport(report_id, start, end, scanlimit, resulttowlimit, reportdevices, reportdevicegroups, reportstoragegroups, reportparameters, reportformat, token)

    print base64.b64decode(qreport)

elif (servicedebug): # service debug

    imp.filter.add(xsd_report)
    doctor = ImportDoctor(imp)

    client = suds.client.Client(url=report, doctor=doctor, location=report)

    print "Devices:"
    dgs = client.service.getDeviceGroups(token)
    for dg in dgs:
        print "   %s" % (dg)
        ddgs = client.service.getDevicesInDeviceGroup(token,dg)
        for d in ddgs:
            print "      %s" % (d)

    print "Storage Groups:"
    sgs = client.service.getStorageGroups(token)
    for sg in sgs:
        print "   %s" % (sg)

# logout
login_client.service.logout(token)

diff = time.time()-procstart
if diff == 0: diff = 1
log("Total processing time: %s" % hms_string(diff))
