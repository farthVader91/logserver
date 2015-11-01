"""
Defines the logging server system 'model' code, sort of like the model of an
MVC pattern of thinking about the logging server system.
"""

import os
import psutil
import datetime
from os import path

LOGS_DIR = path.abspath('logs')
if not path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

class LoggingServerModel(object):
    """Defines what data will be saved and available to the logging system
    viewers and controllers.
    """

    def __init__(self, queuesize=30):
        self._proc = psutil.Process()
        self._proc.cpu_percent()
        self._startTime = datetime.datetime.now()
        self._queuesize = queuesize
        self._logRecordsTotal = 0L
        self._logrecords = []

    def __iter__(self):
        for entry in reversed(self._logrecords):
            yield entry

    @property
    def disk_io(self):
        """the psutil helper returns the following:
           read_count: number of reads
           write_count: number of writes
           read_bytes: number of bytes read
           write_bytes: number of bytes written
           read_time: time spent reading from disk (in milliseconds)
           write_time: time spent writing to disk (in milliseconds)
           --------------------------------------------------------
           this function returns a 2-tuple(read time, write time)
        """
        counters = psutil.disk_io_counters()
        return (counters.read_time, counters.write_time)

    @property
    def cpu_usage(self):
        return self._proc.cpu_percent()

    @property
    def memory_usage(self):
        return self._proc.memory_info()[0]

    @property
    def starttime(self):
        """Get the time the logging server was started"""
        return self._startTime.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def uptime(self):
        """Get the current uptime of the logging server sans microseconds"""
        diff = (datetime.datetime.now() - self._startTime).__str__()
        return diff[:diff.find('.')]

    @property
    def logRecordsTotal(self):
        return self._logRecordsTotal

    @property
    def incomingrate(self):
        elapsed_time = datetime.datetime.now() - self._startTime
        return (self.logRecordsTotal / elapsed_time.total_seconds())

    @property
    def queuesize(self):
        """Get the current size of the logging record queue"""
        return self._queuesize

    def logRecordHandler(self, log_obj):
        """Add the logrecord to the sliding window of logrecords coming into
        the logging server.
        """
        logrecords = self._logrecords
        logrecords.append(log_obj['data'])
        if len(logrecords) > self._queuesize:
            logrecords.pop(0)
        self._logRecordsTotal += 1

SERVER_MODEL = LoggingServerModel()
