from typing import Any, Optional

from gi.repository import Gio, GLib, GObject

from ...common.logger import logger
from ...common.definitions import MAX_UDP_BYTES


class Server(GObject.GObject):
    __gtype_name__ = "UDPServer"

    __gsignals__ = {
        "received": (GObject.SignalFlags.RUN_LAST, None, (object, object)),
    }

    def __init__(self, port: int, context: GLib.MainContext) -> None:
        super().__init__()

        self._address = Gio.InetSocketAddress.new(
            Gio.InetAddress.new_any(Gio.SocketFamily.IPV4), port
        )

        self._socket = Gio.Socket.new(
            Gio.SocketFamily.IPV4, Gio.SocketType.DATAGRAM, Gio.SocketProtocol.UDP
        )
        self._socket.init(None)
        self._socket.set_blocking(False)
        self._socket.bind(self._address, True)

        self._input_stream = Gio.UnixInputStream.new(self._socket.get_fd(), False)

        self._source = self._socket.create_source(GLib.IOCondition.IN, None)
        self._source.set_callback(self.__received_data_cb)
        self._source.attach(context)

    def __received_data_cb(self, data: Optional[Any]) -> int:
        if self.shut is True:
            return GLib.SOURCE_REMOVE

        # XXX replace with .receive_from() when fixed
        try:
            size, address, messages, flags = self._socket.receive_message(
                [], Gio.SocketMsgFlags.PEEK, None
            )
            raw = self._input_stream.read_bytes(MAX_UDP_BYTES, None)
        except Exception as e:
            logger.error(e)
        else:
            self.emit("received", address, raw.get_data())

        return GLib.SOURCE_CONTINUE

    def send(self, address: Gio.InetSocketAddress, data: bytes) -> None:
        if self.shut is True:
            return

        try:
            self._socket.send_to(address, data)
        except Exception as e:
            logger.error(e)

    def shutdown(self) -> None:
        self._socket.close()

        logger.info("Server.UDP.shut")

    @property
    def shut(self) -> bool:
        return self._socket.is_closed()
