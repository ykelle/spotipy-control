import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs
import json
import decrypt
import deffHell
import base64
from authtoken import AuthToken
from connection import Connection
from mercury import MercuryManager
from parameter import *
from session import Session


class Server(BaseHTTPRequestHandler):
    dh = deffHell.DiffieHellman(group=1)
    privateKey = dh.get_private_key()
    publicKey = dh.gen_public_key()

    def _set_200_headers(self, keyword, value):
        self.send_response(200)
        #self.send_header('Content-type', 'application/json')
        self.send_header(keyword, value)
        self.end_headers()

    def _set_404_headers(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        parse = urlparse(self.path)
        request_path = parse.path
        query = parse.query

        key_byte_array = self.publicKey.to_bytes((self.publicKey.bit_length() + 7) // 8, 'big')
        b64_key = base64.standard_b64encode(key_byte_array).decode()

        if (request_path == "/spotzc") and (query == "action=getInfo"):
            self._set_200_headers('Content-type', 'application/json')
            self.wfile.write(json.dumps(
                {
                    "status": 101,
                    "statusString": "ERROR-OK",
                    "spotifyError": 0,
                    "version": VERSION_STRING,
                    "deviceID": DEVICE_ID,
                    "remoteName": REMOTE_NAME,
                    "activeUser": "",
                    "publicKey": b64_key,
                    "deviceType": "SPEAKER",
                    "libraryVersion": "0.1.0",
                    "accountReq": "PREMIUM",
                    "brandDisplayName": "librespot",
                    "modelDisplayName": "librespot"
                }).encode())
        else:
            self._set_404_headers()

    # POST echoes the message adding a JSON field
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        data_bytes = self.rfile.read(content_length)  # <--- Gets the data itself
        data_str = data_bytes.decode('utf-8')
        path = self.path
        headers = self.headers
        var = parse_qs(data_str)
        print("Var: ", var)

        if path != "/spotzc" or 'action' not in var or 'addUser' not in var['action']:
            self._set_404_headers()
            return

        user_name = var['userName'][0].encode()
        blob = var['blob'][0].encode()
        client_key = var['clientKey'][0].encode()

        response = json.dumps(
            {
                "status": 101,
                "spotifyError": 0,
                "statusString": "ERROR-OK"
            }).encode()

        self._set_200_headers('Content-Length', str(len(response)))
        self.wfile.write(response)

        blob_dec = decrypt.getBlobFromAuth(Server.dh, blob, client_key)
        login = decrypt.decryptBlob(blob_dec, user_name, DEVICE_ID)
        #typeInt, authData = decrypt.decryptBlob(blob_dec, userName, DEVICE_ID)

        connection = Connection()
        session = Session().connect(connection)
        #reusable_token = session.authenticate(bytes(userName), bytes(authData), Authentication.AUTHENTICATION_STORED_SPOTIFY_CREDENTIALS)
        reusable_token = session.authenticate(login)
        print("Token: ", reusable_token)
        manager = MercuryManager(connection)
        authToken = AuthToken(manager)
        print("AuthToken: ", authToken)
        manager.terminate()


        #b64_authData = base64.standard_b64encode(authData)
        #print("b64_auth: ", b64_authData)
        #print("b64_auth_hex: ", b64_authData.hex())

        #print("auth_data: ", authData.hex())


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """ This class allows to handle requests in separated threads.
        No further content needed, don't touch this. """


def run(server_class=HTTPServer, handler_class=Server, port=8200):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)

    print('Starting httpd on port %d...' % port)
    httpd.serve_forever()


def start_thread(port=None):
    if port is None:
        port = random_port()

    server_address = ('', port)
    server = ThreadedHTTPServer(server_address, Server)
    thread = threading.Thread(target=server.serve_forever)
    thread.deamon = False
    thread.start()
    print("---Server started (Port %d) ---" % port)
    return server


def random_port():
    min = 1024
    max = 65536
    randPort = random.randint(min, max)
    return randPort