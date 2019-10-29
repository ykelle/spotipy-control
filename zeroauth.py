import random
import socket
from time import sleep
import webserver
from zeroconf import Zeroconf, ServiceInfo
from parameter import REMOTE_NAME


class Zeroauth:

    MAX_PORT = 65536
    MIN_PORT = 1024

    def __init__(self, deviceName = REMOTE_NAME):
        self.hostname = socket.gethostname()
        try:
            self.ip = ip = socket.gethostbyname(self.hostname)
        except:
            self.hostname += '.local'
            self.ip = ip = socket.gethostbyname(self.hostname)

        self.deviceName = deviceName
        self.service = "_spotify-connect._tcp.local."
        self.name = self.deviceName + "._spotify-connect._tcp.local."
        self.port = random.randint(Zeroauth.MIN_PORT, Zeroauth.MAX_PORT)
        self.desc = {"CPath": "/spotzc", "VERSION": "1.0"}

        self.info = ServiceInfo(
            type_=self.service,
            name=self.name,
            addresses=[socket.inet_aton(self.ip)],
            port=self.port,
            properties=self.desc,
            #server=self.hostname,
        )

        self.zeroconf = Zeroconf()

    def start(self):
        self.server = webserver.startThread(self.port)
        self.zeroconf.register_service(self.info)

    def stop(self):
        self.zeroconf.unregister_service(self.info)
        self.zeroconf.close()
        self.server.shutdown()


if __name__ == "__main__":
    print("Start ZeroConf Server")
    za = Zeroauth()
    za.start()
    try:
        while True:
            sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        print("Stop ZeroConf Server")
        za.stop()
