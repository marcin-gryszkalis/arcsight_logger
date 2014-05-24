ArcSight Logger SOAP Client
===========================

Console SOAP client written in Python to interact with ArcSight Logger's API to retrieve search results.

Forked from https://github.com/zrlram/arcsight_logger (Raffael Marty of pixlcloud)

## usage
```
    help:    %s -h
    search:  %s [-v] -l logger -q query -s starttime [-e endtime] [-t step]
    report:  %s [-v] -l logger -r report-id -s starttime [-e endtime] [-f (csv|pdf)] 
        [--scanlimit=nnn] [--resulttowlimit=nnn] 
        [--reportdevices=sss] [--reportdevicegroups=sss] [--reportstoragegroups=sss]
    devices: %s [-v] -l logger -d 
```

## examples
```
$ ./query-logger.py -l mylogger -q ""(sourceAddress=\"$IP\" OR destinationAddress=\"$IP\") -s "`date -d \"7 days ago\" '+%F %T'`" 

$ ./query-logger.py -l mylogger -r F123F654-ABCD-CDEF-0000-123123123123 -s "2014-01-01 00:00:00" --reportdevices="192.168.0.0 [ARCS1]" --reportdevicegroups="NET" --reportstoragegroups="SGNET" -f csv

$ ./query-logger.py -l mylogger -q '(request contains ".exe")' -s "2014-01-01 09:00:00" -e "2014-01-01 17:00:00" | ./filter-eq.pl rt src request
```    