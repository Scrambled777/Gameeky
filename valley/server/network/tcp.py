from gi.repository import Gio, GLib, GObject


class Client(GObject.GObject):
    __gtype_name__ = "TCPServerClient"

    MAX_BYTES = 2048

    def __init__(self, server, connection):
        super().__init__()

        self._acknowledged = False
        self._server = server
        self._connection = connection
        self._input_stream = connection.get_input_stream()
        self._output_stream = connection.get_output_stream()

    def send(self, data):
        self._output_stream.write(data)

    def run(self):
        while self._connection.is_connected():
            try:
                raw = self._input_stream.read_bytes(self.MAX_BYTES, None)
            except:
                break

            data = raw.get_data()
            if not data:
                break

            if self._acknowledged is False:
                self._server.emit("connected", self, data)
                self._acknowledged = True
            else:
                self._server.emit("received", self, data)

        self._server.emit("disconnected", self)


class Server(GObject.GObject):
    __gtype_name__ = "TCPServer"

    __gsignals__ = {
        "connected": (GObject.SignalFlags.RUN_LAST, None, (object, object)),
        "received": (GObject.SignalFlags.RUN_LAST, None, (object, object)),
        "disconnected": (GObject.SignalFlags.RUN_LAST, None, (object,)),
    }

    def __init__(self, port, clients, context):
        super().__init__()

        self._service = Gio.ThreadedSocketService.new(clients)
        self._service.add_inet_port(port)
        self._service.connect("run", self.__on_session_started_cb)
        self._service.start()

    def __on_session_started_cb(self, service, connection, source=None):
        client = Client(server=self, connection=connection)
        client.run()

    def emit(self, *args):
        GLib.idle_add(GObject.GObject.emit, self, *args)