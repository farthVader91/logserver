
"""
This module provides a Twisted Service that handles the output of
a client(logforwarder) that streams log records in plain text over TCP.

logforwarder is the source, this is the sink.
"""

import os
import sys
import json
import twisted
from os import path
import logging.config
import logging.handlers
from struct import unpack
from model import LOGS_DIR, SERVER_MODEL
from twisted.python import log
from twisted.internet.protocol import Protocol, Factory

log.startLogging(sys.stdout)

LONG_INT_LEN = 4

class LoggingProtocol(Protocol):
    """Encapsulates the actual handling of the data received by the
    protocol. It collects all incoming data, building and forwarding complete
    log records as they arrive.
    """

    def __init__(self):
        """Get a "loggingserver" logger, and set up our buffer and record
           instance variables.
        """
        log.msg("Creating new LoggingProtocol object")
        self.logger = None
        self.buffer = ""
        self.buffer_len = self.full_buffer_len = 0
        self.rec_len = None

    def connectionMade(self):
        self.factory.num_protocols += 1
        log.msg('there are currently {} connections'.format(
            self.factory.num_protocols))

    def dataReceived(self, data):
        """Called whenever there's data available in the socket.
        """
        # First, paste the recieved data onto what we have and compute the
        # buffer's length only once rather than every time we need it.
        self.buffer += data
        self.buffer_len = len(self.buffer)
        # Keep processing the buffer, peeling off logging records, till we
        # no longer have a complete record, then exit.  We'll get called again
        # as soon as there's more data available.
        while True:
            # If we've not yet gotten the record length for the next record,
            # and we have enough data to get it, do so.
            if not self.rec_len and self.buffer_len >= LONG_INT_LEN:
                self.rec_len = unpack(">L", self.buffer[:LONG_INT_LEN])[0]
                self.full_buffer_len = LONG_INT_LEN + self.rec_len
            # If we've gotten the length, and there's enough data in the
            # buffer to build our record, do so.
            #
            # Otherwise, we're done (for now).
            if (self.rec_len and self.buffer_len >= self.full_buffer_len):
                # get the plain log message, from the end of the length bytes
                # to the end of full_buffer_len i.e. just the data
                pure_data = self.buffer[LONG_INT_LEN:self.full_buffer_len]
                # extract python dictionary from the json string
                obj = json.loads(pure_data)
                # use the factory helper to get a logger instance
                # insert the log entry using the same instance
                log.msg("LoggingProtocol: logging new record")
                logger = self.factory.get_logger(obj.get('token'),
                                                 obj.get('type'),
                                                 obj.get('name'))
                # strip newline character while logging
                logger.debug(obj.get('data').strip())
                # track the object in our models
                SERVER_MODEL.logRecordHandler(obj)
                # Adjust our buffer to point past the end of what we just
                # processed and recompute the length
                self.buffer = self.buffer[self.full_buffer_len:]
                self.buffer_len = len(self.buffer)
                # Unset self.rec_len and self.full_buffer_len since we don't
                # yet know the length of the next one.  When we loop around,
                # we'll take care of that if we've got enough data to work on.
                self.rec_len = self.full_buffer_len = None
            else:
                # otherwise, we either don't know the length,
                # or don't have a complete record, done for now
                break

    def connectionLost(self, reason):
        log.msg("connectionLost called")
        self.factory.num_protocols -= 1
        self.buffer = ""

    def handle_quit(self):
        log.msg("handle_quit called")
        self.transport.loseConnection()


class LoggingFactory(Factory):
    """Factory that creates the LoggingProtocol object"""
    protocol = LoggingProtocol
    def __init__(self):
        self.num_protocols = 0
        self.logger_cache = {}

    def get_logger(self, token, _type, name):
        logger_name = '.'.join([token, _type, name])
        if logger_name in self.logger_cache:
            return self.logger_cache.get(logger_name)
        else:
            logger = self.instantiate_logger(token, _type, name)
            self.logger_cache[logger_name] = logger
            return logger

    @staticmethod
    def instantiate_logger(token, _type, name):
        client_log_dir = path.join(LOGS_DIR, token, _type)
        if not path.exists(client_log_dir):
            os.makedirs(client_log_dir)
        logger_name = '.'.join([token, _type, name])
        logger_file = path.join(client_log_dir, name)
        logger = logging.getLogger(logger_name)
        rfg = logging.handlers.TimedRotatingFileHandler(
            logger_file, when='D', backupCount=6)
        logger.setLevel(logging.DEBUG)
        rfg.setLevel(logging.DEBUG)
        logger.addHandler(rfg)
        return logger
