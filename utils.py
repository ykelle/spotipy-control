import enum


class REQUEST_TYPE(enum.Enum):
  SEND=      1
  GET =      2

  def __str__(self):
    return self.name

  def as_command( self ):
    if self.name== 'SEND' or \
       self.name== 'GET':
      return 0xb2