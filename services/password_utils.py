from passlib.utils.pbkdf2 import pbkdf2
import secrets
import base64

def validatePassword(password: str, hashedPassword: str) -> bool:
    """ Decodifica la el valor del hash y retorna true si coincide con la contraseña dada """
    src = base64.b64decode(hashedPassword)
    if len(src) != 49:
        return False
    salt = src[1:17]
    bytes = src[17:49]
    passgened=pbkdf2(password, salt, 1000, 32, "hmac-sha1")
    for i in range(0, len(bytes)):
        if bytes[i] != passgened[i]:
            return False
    return True

def generateHash(password: str) -> str:
    """ Genera una cadena de hash para la contraseña dada """
    salt = secrets.token_bytes(16)
    bytes = pbkdf2(password, salt, 1000, 32, "hmac-sha1")
    src = b"\x00" + salt + bytes
    return base64.b64encode(src).decode('utf-8')
