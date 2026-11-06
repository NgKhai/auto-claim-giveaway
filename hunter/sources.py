"""Fixed official read-only evidence registry; fetched text is untrusted data.

This module supplies no registration tools and derives no eligibility claims from
provider prose. Only developer-reviewed registry URLs may be fetched.
"""
import asyncio
import hashlib
import time
import httpx

MAX_BYTES=256*1024
TIMEOUT=10.0
FRESH_SECONDS=86400
COOLDOWN_SECONDS=60
REGISTRY={'github-education':{
    'id':'github-education',
    'title':'GitHub Education student application documentation',
    'source_url':'https://raw.githubusercontent.com/github/docs/main/content/education/about-github-education/github-education-for-students/apply-to-github-education-as-a-student.md',
    'canonical_url':'https://docs.github.com/en/education/about-github-education/github-education-for-students/apply-to-github-education-as-a-student',
    'purpose':'eligibility evidence only',
    'attribution':'GitHub documentation contributors',
    'license':'CC-BY-4.0',
    'license_url':'https://creativecommons.org/licenses/by/4.0/',
    'excerpt_format':'unrendered Markdown; Liquid templates are not evaluated',
    'eligibility':'unknown','deadline':'unknown','automation_status':'unknown',
}}

class SourceFailure(Exception):
    """A fixed, credential-free error code suitable for persistence and display."""


def fetch_source(source_id,transport=None):
    return asyncio.run(_fetch_source(source_id,transport))


async def _fetch_source(source_id,transport=None):
    source=REGISTRY[source_id]
    try:
        # A total deadline cancels even a slow body trickle that never reaches
        # the byte iterator's chunk boundary. Keep proxy and CA trust enabled.
        async with asyncio.timeout(TIMEOUT):
            async with httpx.AsyncClient(transport=transport,timeout=TIMEOUT,follow_redirects=False,trust_env=True) as client:
                async with client.stream('GET',source['source_url'],headers={'Accept':'text/plain, text/markdown','Accept-Encoding':'identity','User-Agent':'OpportunityHunterEvidence/1.0'}) as response:
                    if response.status_code!=200: raise SourceFailure('upstream_http_error')
                    media=response.headers.get('content-type','').split(';',1)[0].strip().lower()
                    if media not in {'text/plain','text/markdown'}: raise SourceFailure('unsupported_content_type')
                    # Refuse compression to avoid uncontrolled decompression.
                    if response.headers.get('content-encoding','identity').lower()!='identity': raise SourceFailure('unsupported_content_encoding')
                    data=bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=4096):
                        if len(data)+len(chunk)>MAX_BYTES: raise SourceFailure('response_too_large')
                        data.extend(chunk)
                    if not data: raise SourceFailure('empty_response')
                    try: text=bytes(data).decode('utf-8',errors='strict')
                    except UnicodeDecodeError: raise SourceFailure('invalid_utf8') from None
                    return {'content_hash':hashlib.sha256(data).hexdigest(),'retrieved_at':time.time(),'excerpt':text[:4000],'truncated':len(text)>4000}
    except SourceFailure:
        raise
    except (TimeoutError,httpx.TimeoutException):
        raise SourceFailure('upstream_timeout') from None
    except httpx.HTTPError:
        raise SourceFailure('upstream_unavailable') from None


def source_view(source_id,row=None,now=None):
    now=time.time() if now is None else now
    source=dict(REGISTRY[source_id])
    evidence=None
    if row and row['content_hash']:
        evidence={key:row[key] for key in ['content_hash','retrieved_at','excerpt']}
        evidence['changed']=bool(row['changed'])
        evidence['truncated']=bool(row['truncated'])
        evidence['freshness']='fresh' if now-evidence['retrieved_at']<FRESH_SECONDS else 'stale'
    status='not_fetched'
    if row and row['last_error']: status='unverified'
    elif evidence: status='fresh' if now-evidence['retrieved_at']<FRESH_SECONDS else 'stale'
    return {**source,'status':status,'evidence':evidence,
            'last_error':row['last_error'] if row else None,
            'last_attempt_at':row['last_attempt_at'] if row else None,
            'cooldown_until':row['last_attempt_at']+COOLDOWN_SECONDS if row else None}
