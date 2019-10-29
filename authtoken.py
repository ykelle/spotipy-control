import threading
from parameter import *

from utils import REQUEST_TYPE


class AuthToken:
  def __init__( self, mercury_manager ):
    self._mercury_manager= mercury_manager
    self._event= threading.Event()
    self._event.clear()

    self._mercury_manager.execute( REQUEST_TYPE.GET,
                                   AUTH_TOKEN_TEMPLATE.format(clientId=CLIENT_ID, scope=DEFAULT_SCOPE),
                                   self._info_callback )
    self._event.wait()

  def _info_callback( self, header, parts ):
    open( 'auth_data.dat', 'wb' ).write( parts[ 0 ] )
    self._event.set()