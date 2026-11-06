"""Validated immutable deployment settings; errors deliberately omit values."""
from dataclasses import dataclass
import ipaddress
import os
from pathlib import Path
import re
from urllib.parse import urlsplit
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse

class ConfigurationError(ValueError):
    pass

def _host(value):
    if not value or not value.isascii() or value != value.strip():
        raise ConfigurationError('Invalid allowed host configuration')
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        if len(value)>253 or not all(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?',label) for label in value.split('.')):
            raise ConfigurationError('Invalid allowed host configuration') from None
        return value.lower()

def _authority(value):
    if not value or not value.isascii() or any(ch.isspace() or ord(ch)<32 or ord(ch)==127 for ch in value):
        raise ConfigurationError('Invalid authority configuration')
    if value.startswith('['):
        match=re.fullmatch(r'\[([0-9A-Fa-f:.]+)\](?::([0-9]+))?',value)
        if not match: raise ConfigurationError('Invalid authority configuration')
        try: host=str(ipaddress.IPv6Address(match.group(1)))
        except ValueError: raise ConfigurationError('Invalid authority configuration') from None
    else:
        match=re.fullmatch(r'([A-Za-z0-9.-]+)(?::([0-9]+))?',value)
        if not match: raise ConfigurationError('Invalid authority configuration')
        host=_host(match.group(1))
    try: port=int(match.group(2)) if match.group(2) else None
    except ValueError: raise ConfigurationError('Invalid authority configuration') from None
    if port is not None and not 1<=port<=65535: raise ConfigurationError('Invalid authority configuration')
    return host,port


def normalize_origin(value):
    if not isinstance(value,str) or not value.startswith('https://'):
        raise ConfigurationError('Invalid trusted origin configuration')
    host,port=_authority(value[len('https://'):])
    host='['+host+']' if ':' in host else host
    return 'https://'+host+(':'+str(port) if port and port!=443 else '')

@dataclass(frozen=True)
class Settings:
    environment: str = 'development'
    allowed_hosts: tuple[str,...] = ('localhost','127.0.0.1','::1','testserver')
    trusted_origins: tuple[str,...] = ()
    db_path: str|None = None
    secure_cookie: bool = False

    def __post_init__(self):
        if type(self.secure_cookie) is not bool:
            raise ConfigurationError('Invalid secure cookie configuration')
        if self.environment not in {'development','production'}:
            raise ConfigurationError('Invalid environment configuration')
        hosts=tuple(dict.fromkeys(_host(v) for v in self.allowed_hosts))
        origins=tuple(dict.fromkeys(normalize_origin(v) for v in self.trusted_origins))
        if not hosts: raise ConfigurationError('Explicit allowed hosts required')
        if any(urlsplit(origin).hostname not in hosts for origin in origins):
            raise ConfigurationError('Trusted origins must use allowed hosts')
        if self.environment=='production':
            if not origins or not self.secure_cookie or not self.db_path or not Path(self.db_path).is_absolute():
                raise ConfigurationError('Production requires trusted origins, secure cookies and an absolute database path')
        object.__setattr__(self,'allowed_hosts',hosts)
        object.__setattr__(self,'trusted_origins',origins)

    @classmethod
    def from_env(cls,environ=None):
        env=os.environ if environ is None else environ
        mode=env.get('HUNTER_ENV','development')
        if mode=='production' and (not env.get('HUNTER_ALLOWED_HOSTS') or not env.get('HUNTER_TRUSTED_ORIGINS') or env.get('HUNTER_SECURE_COOKIE')!='1' or not env.get('HUNTER_DB_PATH')):
            raise ConfigurationError('Production configuration is incomplete')
        cookie=env.get('HUNTER_SECURE_COOKIE','0')
        if cookie not in {'0','1'}: raise ConfigurationError('Invalid secure cookie configuration')
        def csv(key,default):
            if key not in env: return default
            values=tuple(v.strip() for v in env[key].split(','))
            if any(not v for v in values): raise ConfigurationError('Empty deployment configuration entry')
            return values
        return cls(environment=mode,allowed_hosts=csv('HUNTER_ALLOWED_HOSTS',cls().allowed_hosts),trusted_origins=csv('HUNTER_TRUSTED_ORIGINS',()),db_path=env.get('HUNTER_DB_PATH'),secure_cookie=cookie=='1')

class ExactTrustedHostMiddleware(TrustedHostMiddleware):
    """Starlette host validation with exact bracketed IPv6 support.

    The installed Starlette middleware splits Host at the first colon and cannot
    recognise IPv6 literals. Handle those only, retaining its normal DNS path.
    """
    async def __call__(self,scope,receive,send):
        if scope['type'] not in {'http','websocket'}:
            return await self.app(scope,receive,send)
        hosts=Headers(scope=scope).getlist('host')
        if len(hosts)!=1:
            return await PlainTextResponse('Invalid host header',status_code=400)(scope,receive,send)
        raw=hosts[0]
        try:
            host,port=_authority(raw)
            if host not in self.allowed_hosts: raise ConfigurationError('Invalid host header')
        except ConfigurationError:
            return await PlainTextResponse('Invalid host header',status_code=400)(scope,receive,send)
        if ':' in host:
            return await self.app(scope,receive,send)
        normalized=host+(':'+str(port) if port else '')
        checked_scope=dict(scope)
        checked_scope['headers']=[(key,normalized.encode('ascii') if key.lower()==b'host' else value) for key,value in scope['headers']]
        return await super().__call__(checked_scope,receive,send)
