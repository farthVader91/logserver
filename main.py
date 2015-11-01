"""
This is the main model. This is where the app will be run from.
"""


from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from protocol import LoggingFactory
from twisted.web import server
from webresource import WebRoot, WebLogs

LOGGER_TCP_PORT = 9898
LOGGER_WEB_PORT = 9900

# configure the logging endpoint
logging_endpoint = TCP4ServerEndpoint(reactor, LOGGER_TCP_PORT)
logging_endpoint.listen(LoggingFactory())

# configure the web endpoint
root = WebRoot()
logs = WebLogs()
root.putChild('logs', logs)
site = server.Site(root)
reactor.listenTCP(LOGGER_WEB_PORT, site)

if __name__ == '__main__':
    reactor.run()
