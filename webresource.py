
import os
import sys
from os import path
from twisted.web import resource
import twisted.internet
from twisted.python import log

from model import SERVER_MODEL, LOGS_DIR
from webpage import htmlpage

log.startLogging(sys.stdout)

class WebRoot(resource.Resource):
    """This class defines the entry point for the logging server
    status home page. This page provides a view of what's going
    on inside the logging server.
    """
    html = """<tr class="info"><td>%s</td></tr>"""

    def getChild(self, name, request):
        if name == '':
            return self
        return resource.Resource.getChild(self, name, request)

    def render_GET(self, request):
        read_time, write_time = SERVER_MODEL.disk_io
        data = {
            "starttime"         : SERVER_MODEL.starttime,
            "uptime"            : SERVER_MODEL.uptime,
            "logrecordstotal"   : SERVER_MODEL.logRecordsTotal,
            "incomingrate"      : SERVER_MODEL.incomingrate,
            "cpu_usage"         : SERVER_MODEL.cpu_usage,
            "memory_usage"      : SERVER_MODEL.memory_usage,
            "disk_io_read"      : read_time,
            "disk_io_write"     : write_time
        }
        # create list of all log records
        rows = []
        for record in SERVER_MODEL:
            rows.append(WebRoot.html % (record))
        data["all"] = ''.join(rows)
        return (htmlpage % data).encode('utf8')

class WebLogs(resource.Resource):
    """This class shows all the log files available at a given
       token. Although, more work is needed.
    """
    body_html = "<html><body>%s</body></html>"
    row_html = """<tr><td>%s</td></tr> """

    def getChild(self, name, request):
        if name == '':
            return self
        return resource.Resource.getChild(self, name, request)

    def render_GET(self, request):
        token = request.args.get('token')
        if token is None:
            html = (WebLogs.body_html % "<h3>token not included</h3>")
            request.setResponseCode(401)
            return str(html)
        token = token[0]
        token_logs_dir = path.join(LOGS_DIR, token)
        if not path.exists(token_logs_dir):
            html = (WebLogs.body_html % "<h3>token not found</h3>")
            request.setResponseCode(404)
            return str(html)
        logs = []
        _type = request.args.get('type')
        if _type is None:
            for dirname, _, files in os.walk(token_logs_dir):
                for filename in files:
                    log_path = path.join(dirname, filename)
                    logs.append(WebLogs.row_html % log_path)
        logs_html = ''.join(logs)
        header_html = "<h3>Your logs:</h3>"
        table_html = "<table border=\"1\">%s</table>" % logs_html
        full_html = WebLogs.body_html % ''.join([header_html, table_html])
        return str(full_html)
