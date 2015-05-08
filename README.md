ArcSight Logger SOAP Client
===========================

Console SOAP client written in Python to interact with ArcSight Logger's API to retrieve search results.

Forked from https://github.com/zrlram/arcsight_logger (Raffael Marty of pixlcloud)

## usage
```
Usage:
    help:    query-logger.py -h
    search:  %s [-v] [-D] -l logger -q query -s starttime [-e endtime] [-t step]
    report:  %s [-v] [-D] -l logger -r report-id -s starttime [-e endtime] [-f (csv|pdf)]
        [--scanlimit=nnn] [--resulttowlimit=nnn]
        [--reportdevices=sss] [--reportdevicegroups=sss] [--reportstoragegroups=sss]
    devices: %s [-v] [-D] -l logger -d
```
## configuration file
It's required to have config file. Following locations are searched:
 - /etc/logger.ini
 - ~/.logger.ini
 - ./logger.ini

```
[credentials]
user = loggeruser
password = secretpassw0rd

[loggers]
mylogger1 = 192.168.0.1
mylogger2 = 192.168.0.2
myloggertest = 192.168.1.1

[options]
accept_invalid_ssl = yes
```

## examples
```
$ ./query-logger.py -l mylogger
    -q '(sourceAddress="192.168.0.1" OR destinationAddress="192.168.0.1")'
    -s "`date -d '7 days ago' '+%F %T'`"

$ ./query-logger.py -l mylogger
    -r "F123F654-ABCD-CDEF-0000-123123123123"
    -s "2014-01-01 00:00:00"
    --reportdevices="192.168.0.0 [ARCS1]" --reportdevicegroups="NET" --reportstoragegroups="SGNET"
    -f csv

$ ./query-logger.py -l mylogger
    -q '(request contains ".exe")'
    -s "2014-01-01 09:00:00" -e "2014-01-01 17:00:00"
    | ./filter-eq.pl rt src request
```
