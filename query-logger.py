#!/usr/bin/python
# $Id$
# marcin.gryszkalis@mbank.pl

import suds
from suds.xsd.doctor import Import, ImportDoctor

from datetime import datetime, timedelta
import time, sys
import pprint
import getopt
import ConfigParser
import base64

# [credentials]
# user = xxx
# password = xxx
# [loggers]
# lgib = 10.24.53.3
# lgl = 10.24.51.3

Config = ConfigParser.ConfigParser()
Config.read("logger.ini")

user = Config.get("credentials", "user")
password = Config.get("credentials", "password")

# command line
def usage():
    print >>sys.stderr, """Usage: 
    help:    %s -h
    search:  %s [-v] -l logger -q query -s starttime [-e endtime] [-t step]
    report:  %s [-v] -l logger -r report-id -s starttime [-e endtime] [-f (csv|pdf)] 
        [--scanlimit=nnn] [--resulttowlimit=nnn] 
        [--reportdevices=sss] [--reportdevicegroups=sss] [--reportstoragegroups=sss]
    devices: %s [-v] -l logger -d 
    """ % (sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0])

try:
    optlist, args = getopt.getopt(sys.argv[1:], 'l:s:e:q:r:t:f:dh', ['help', 'scanlimit=', 'resulttowlimit=','reportdevices=','reportdevicegroups=','reportstoragegroups='])
except getopt.GetoptError as err:
    print >>sys.stderr, str(err)
    usage()
    sys.exit(2)

verbose = False
servicedebug = False
logger_id = False
query = False
report_id = False
starttime = False
endtime = False
step=1000
scanlimit=0
resulttowlimit=0
reportdevices="null"
reportdevicegroups="null" # "PROD"
reportstoragegroups="null" # SGLodIB"
reportparameters=""
reportformat="CSV"

for o, a in optlist:
#    print >>sys.stderr, "(%s)=(%s)" % (o,a)
    if o == "-v":
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
    print >>sys.stderr, "Invalid report format"
    usage()
    sys.exit(2)


# config file
IP = Config.get("loggers", logger_id)
port = 443
server =  "https://%s:%s/soap/services/" % (IP,port)

print >>sys.stderr, "logger: %s" % server

# SOAP URLs
xsd = "http://www.arcsight.com/logger/xsd"
xsd_login = 'http://domain.login.webservices.logger.arcsight.com/xsd'
xsd_search = 'http://domain.search.webservices.logger.arcsight.com/xsd'
xsd_report = 'http://domain.reports.webservices.logger.arcsight.com/xsd'
login = "%sLoginService/LoginService.wsdl" % server
search = "%sSearchService/SearchService.wsdl" % server
report = "%sReportService/ReportService.wsdl" % server

# Setup Logging
import logging
logging.basicConfig(level=logging.INFO)

imp = Import(xsd)
imp.filter.add(xsd_login)
doctor = ImportDoctor(imp)

# login
login_client = suds.client.Client(url=login, doctor=doctor, location=login)

token = login_client.service.login(user, password)
if not token:
    sys.stderr.write("Failed to log in")
    exit(1)

api_version = login_client.service.getVersion()
print >> sys.stderr, "API version: %s" % (api_version)


if (query or report_id):
    print >>sys.stderr, "time range: %s -- %s" % (starttime, endtime or "Now")
    start = int(time.mktime(datetime.strptime(starttime, "%Y-%m-%d %H:%M:%S").timetuple())) * 1000
    end   = int(time.mktime(datetime.strptime(endtime, "%Y-%m-%d %H:%M:%S").timetuple())) * 1000 if endtime else int(time.time()) * 1000

if (query):

    print >>sys.stderr, "query: %s" % query
    print >>sys.stderr, "step: %s" % step

    imp.filter.add(xsd_search)
    doctor = ImportDoctor(imp)  

    # search
    client = suds.client.Client(url=search, doctor=doctor, location=search)
    search = client.service.startSearch(query, start, end, token)

    #try:
    totali = 0
    procstart = time.time()
    while client.service.hasMoreTuples(token):
        tuples = client.service.getNextTuples(step,10000,token)
        
        diff = time.time()-procstart
        if diff == 0: diff = 1
        totali = totali + len(tuples)
        print >> sys.stderr, "extracted %d rows (%.2f/s)" % (totali,totali/diff)


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
