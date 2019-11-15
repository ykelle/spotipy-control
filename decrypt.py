import hashlib
import base64
import hmac
import os

from Crypto.Cipher import AES
from Crypto.Util import Counter
import Crypto.Random as random
from Crypto.Util.Padding import pad, unpad
from google.protobuf import text_format

import protocol.impl.authentication_pb2 as Authentication


def readBlobInt(blob):
    lo = blob[0]
    if (lo & 0x80) == 0:
        return lo, 1
    hi = blob[1]
    return (lo & 0x7f | hi << 7), 2


def getBlobFromAuth(dh, blob, clientKey):

    decoded = base64.b64decode(clientKey)

    dh.generate_shared_secret(int.from_bytes(decoded, byteorder='big'))

    sharedKey = dh.shared_secret

    sharedKeyBytes = sharedKey.to_bytes((sharedKey.bit_length() + 7) // 8, 'big')

    blobBytes = base64.b64decode(blob)

    blobLen = len(blobBytes)

    # IV = encrypted_blob[:0x10]
    iv = blobBytes[:16]

    # encrypted = encrypted_blob[0x10:-0x14]
    encrypted = blobBytes[16:(blobLen - 20)]

    # expected_mac = encrypted_blob[-0x14:]
    checksum = blobBytes[(blobLen - 20):]

    # base_key = SHA1(shared_secret)
    base_key = hashlib.sha1(sharedKeyBytes).digest()[:16]

    # checksum_key = HMAC - SHA1(base_key, "checksum")
    checksum_key = hmac.new(base_key, 'checksum'.encode(), hashlib.sha1).digest()

    # encryption_key = HMAC - SHA1(base_key, "encryption")[:0x10]
    encryption_key = hmac.new(base_key, 'encryption'.encode(), hashlib.sha1).digest()

    # mac
    mac = hmac.new(checksum_key, encrypted, hashlib.sha1).digest()

    if checksum != mac:
        print("Mac and checksum don't match!")
        print("checksum: ", checksum.hex())
        print("mac", mac.hex())
        raise Exception('Mac and checksum dont match!')

    # blob = AES128-CTR-DECRYPT(encryption_key, IV, encrypted)
    ctr = Counter.new(128, initial_value=int.from_bytes(iv, byteorder="big"))
    cipher = AES.new(encryption_key[:16], AES.MODE_CTR, counter=ctr)
    decrypted = cipher.decrypt(encrypted)

    return decrypted


def decryptBlob(base64Blob, username, deviceId):
    encryptedBlob = base64.b64decode(base64Blob)

    # base_key = PBKDF2(SHA1(deviceID), username, 0x100, 1)
    secret = hashlib.sha1(deviceId.encode()).digest()
    basekey = hashlib.pbkdf2_hmac('sha1', secret, username, 256, dklen=20)

    # key = SHA1(base_key) || htonl(len(base_key))
    base_key_hashed = hashlib.sha1(basekey).digest()
    key = base_key_hashed + (20).to_bytes(4, byteorder='big')

    # login_data = AES192-DECRYPT(key, data)
    cipher = AES.new(key, AES.MODE_ECB)
    decryptedBlob = cipher.decrypt(encryptedBlob)

    login_data = bytearray(decryptedBlob)

    l = len(decryptedBlob)
    for i in range(0, l - 16):
        login_data[l - i - 1] ^= login_data[l - i - 17]

    with open('blob.dat', 'wb') as f:
        f.write(login_data)
        f.close()

    pointer = 1
    lenght, count = readBlobInt(login_data[pointer:(pointer + 1)])
    pointer = pointer + count + lenght + 1

    typeInt, count = readBlobInt(login_data[pointer:(pointer + 1)])
    pointer = pointer + count + 1

    lenght, count = readBlobInt(login_data[pointer:(pointer + 1)])
    pointer = pointer + count

    authData = login_data[pointer:(pointer + lenght)]

    login = Authentication.LoginCredentials()
    login.username = bytes(username)
    login.typ = Authentication.AUTHENTICATION_STORED_SPOTIFY_CREDENTIALS
    login.auth_data = bytes(authData)

    return login


def encryptBlob(blobBytes, device_id, username):
    login_data = bytearray(blobBytes)

    l = len(login_data)
    for i in range(l - 17, -1, -1):
        login_data[l - i - 1] ^= login_data[l - i - 17]

    # base_key = PBKDF2(SHA1(deviceID), username, 0x100, 1)
    secret = hashlib.sha1(device_id.encode()).digest()
    basekey = hashlib.pbkdf2_hmac('sha1', secret, username, 256, dklen=20)

    # key = SHA1(base_key) || htonl(len(base_key))
    base_key_hashed = hashlib.sha1(basekey).digest()
    key = base_key_hashed + (20).to_bytes(4, byteorder='big')

    cipher = AES.new(key, AES.MODE_ECB)
    encryptedBlob = cipher.encrypt(login_data)

    b64_encryptedBlob = base64.standard_b64encode(encryptedBlob)

    return b64_encryptedBlob

def buildBlob(auth_data, name, type):
    i = b'I' # 49
    name_len = len(name).to_bytes(1, byteorder="big")
    name_byte = name.encode()
    p = b'P' # 50
    type_byte = type.to_bytes(1, byteorder="big")
    q = b'Q' # 51
    data_len = len(auth_data).to_bytes(1, byteorder="big")

    complete_blob = i + name_len + name_byte + p + type_byte + q + data_len + auth_data

    # padding to 128 bytes
    padding_len = 128 - len(complete_blob)
    padding_bytes = padding_len.to_bytes(padding_len, byteorder="big")
    complete_blob += padding_bytes

    return complete_blob

def makeAuthBlob(dh, blob, pub_server_key, device_id, username):
    enc_blob = encryptBlob(blob, device_id, username.encode())

    # Create shared secret with D.H.
    decoded = base64.b64decode(pub_server_key)
    dh.generate_shared_secret(int.from_bytes(decoded, byteorder='big'))

    sharedKey = dh.shared_secret
    sharedKeyBytes = sharedKey.to_bytes((sharedKey.bit_length() + 7) // 8, 'big')

    iv = random.get_random_bytes(16)

    # base_key = SHA1(shared_secret)
    base_key = hashlib.sha1(sharedKeyBytes).digest()[:16]

    # checksum_key = HMAC - SHA1(base_key, "checksum")
    checksum_key = hmac.new(base_key, 'checksum'.encode(), hashlib.sha1).digest()

    # encryption_key = HMAC - SHA1(base_key, "encryption")[:0x10]
    encryption_key = hmac.new(base_key, 'encryption'.encode(), hashlib.sha1).digest()

    # blob = AES128-CTR-ENCRYPT(encryption_key, IV, encrypted)
    ctr = Counter.new(128, initial_value=int.from_bytes(iv, byteorder="big"))
    cipher = AES.new(encryption_key[:16], AES.MODE_CTR, counter=ctr)
    encrypted = cipher.encrypt(enc_blob)

    # mac
    mac = hmac.new(checksum_key, encrypted, hashlib.sha1).digest()

    complete_enc_blob = iv + encrypted + mac

    b64_complete_enc_blob = base64.b64encode(complete_enc_blob)

    return b64_complete_enc_blob



