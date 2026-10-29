import hashlib
import hmac
import secrets


def password_hash(password):
    salt=secrets.token_hex(16)
    return salt+':'+hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()

def password_matches(password,stored):
    salt,digest=stored.split(':')
    actual=hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()
    return hmac.compare_digest(actual,digest)

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()
