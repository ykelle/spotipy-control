import hashlib
import base64
import hmac
from Crypto.Cipher import AES
from Crypto.Util import Counter
from google.protobuf import text_format

import protocol.impl.authentication_pb2 as Authentication


def readBlobInt(blob):
    lo = blob[0]
    if (lo & 0x80) == 0:
        return lo, 1
    hi = blob[1]
    return (lo & 0x7f | hi << 7), 2


def getBlobFromAuth(dh, blob, clientKey):
    publicKey = dh.gen_public_key()
    keyByteArray = publicKey.to_bytes((publicKey.bit_length() + 7) // 8, 'big')
    b64key = base64.standard_b64encode(keyByteArray).decode()

    decoded = base64.b64decode(clientKey)
    dh.gen_shared_key(int.from_bytes(decoded, byteorder="big"))
    sharedKey = dh.shared_key
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

    open('credentials.dat', 'w').write(text_format.MessageToString(login))

    return login
