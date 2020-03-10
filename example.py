from time import sleep
from zeroauth import Zeroauth
import json
from authtoken import AuthToken
from connection import Connection
from mercury import MercuryManager
from session import Session
from pyfy import Spotify
from blob import Blob


class BlobListener:
    def __init__(self):
        self.blob = None

    def new_blob_status(self, blob: Blob):
        self.blob = blob
        print("User %s blob received" % self.blob.username)


if __name__ == "__main__":
    print("Start ZeroConf Server")
    za = Zeroauth()
    za.start()
    blob_listener = BlobListener()
    za.register_listener(blob_listener)

    while True:
        sleep(1)
        if blob_listener.blob is not None:
            break

    za.stop()
    login = blob_listener.blob.create_login()
    connection = Connection()
    session = Session().connect(connection)
    session.authenticate(login)
    manager = MercuryManager(connection)

    client_id = '<YOUR_CLIENT_ID>'
    authToken = AuthToken(manager, client_id)
    manager.terminate()
    token = authToken.accessToken
    print("AuthToken: ", token)

    spt = Spotify(token)
    devices = spt.devices()
    print(devices)

    last_10_played = spt.recently_played_tracks(10)
    print(last_10_played)


