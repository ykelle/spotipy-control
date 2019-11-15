import sys
import threading
import mercury
import argparse

from connection import Connection
from session import Session


class Spotify(object):

    def __init__(self, client_id=None):
        self.current_user = ''
        self.authenticated = False
        self.manager = mercury.MercuryManager()
        self.lock = threading.Lock()


    def login(self, username, password):
        print("Login with username and password")
        self.current_user = username

    def start_zeroconf(self, name='Spotipy'):
        print("Start advertising")

    def stop_zeroconf(self):
        print("Stop advertising")

    def authenticated(self):
        self.lock.acquire()
        current_auth = None
        try:
            print("Authenticated?")
            current_auth = self.authenticated
        finally:
            self.lock.release()
        return current_auth

    def get_token(self):
        if not self.authenticated():
            return None
        connection = Connection()
        session = Session().connect(connection)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--verbosity", help="increase output verbosity")

    args = parser.parse_args()

    answer = args.square ** 2

    if args.verbosity == 2:
        print("the square of {} equals {}".format(args.square, answer))
    elif args.verbosity == 1:
        print("{}^2 == {}".format(args.square, answer))
    else:
        print(answer)
