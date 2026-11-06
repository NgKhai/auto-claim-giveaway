import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator
from hunter.analysis import analyze_source
from hunter.config import Settings, ConfigurationError, ExactTrustedHostMiddleware, normalize_origin
from hunter.sources import REGISTRY, COOLDOWN_SECONDS, SourceFailure, fetch_source, source_view

class Credentials(BaseModel):
    email: str = Field(min_length=3,max_length=254)
    password: str = Field(min_length=1,max_length=256)
    country: str = Field(default='VN',pattern=r'^[A-Z]{2}$')
    @field_validator('email')
    @classmethod
    def email_valid(cls,v):
        v=v.strip().lower()
        if '@' not in v or '.' not in v.split('@')[-1]: raise ValueError('Email address required')
        return v

class Goal(BaseModel):
    query: str = Field(min_length=1,max_length=500)
    @field_validator('query')
    @classmethod
    def query_valid(cls,v):
        if not v.strip(): raise ValueError('Enter a goal')
        return v.strip()

class AccountDeletion(BaseModel):
    password: str = Field(min_length=1,max_length=256)

class NewApplication(BaseModel):
    opportunity_id: str = Field(max_length=100)

class SourceRefresh(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Approval(BaseModel):
    version: int

BASE={'country':'VN','deadline':'2099-12-31T23:59:59+00:00','source_url':'sandbox://opportunity-hunter/credits','evidence':'Controlled local fixture; eligibility and automation permitted here only. No real reward.','is_sandbox':True,'description':'Local test opportunity. No external account or reward is created.','required_fields':['email']}
OPPORTUNITIES={key:{**BASE,'id':key,'title':title,**changes} for key,title,changes in [
    ('sandbox-credits','Sandbox developer credits',{}),
    ('sandbox-expired','Sandbox expired campaign',{'deadline':'2020-01-01T00:00:00+00:00'}),
    ('sandbox-country','Sandbox US-only campaign',{'country':'US'}),
    ('sandbox-unverified','Sandbox missing evidence',{'evidence':''}),
    ('sandbox-sensitive','Sandbox sensitive-data campaign',{'required_fields':['email','credit_card']})]}

def policy(o,country):
    if not o['is_sandbox']: return 'External automation unavailable; provider handoff required.'
    if not o['evidence']: return 'Missing verification evidence.'
    if datetime.fromisoformat(o['deadline'])<=datetime.now(timezone.utc): return 'Opportunity has expired.'
    if o['country']!=country: return 'Country is not eligible.'
    if set(o['required_fields'])-{'email'}: return 'Sensitive fields exceed permitted email scope.'
    return ''

def create_app(db_path=None, source_transport=None, settings=None):
    settings=settings or Settings.from_env()
    if settings.environment=='production' and db_path is not None and not Path(db_path).is_absolute():
        raise ConfigurationError('Production database override must be absolute')
    path=Path(db_path or settings.db_path or str(Path(__file__).resolve().parent.parent/'.data/hunter.sqlite3'))
    path.parent.mkdir(parents=True,exist_ok=True)
    app=FastAPI(title='Opportunity Hunter — sandbox')
    @contextmanager
    def db():
        c=sqlite3.connect(str(path),timeout=10); c.row_factory=sqlite3.Row
        try:
            c.execute('PRAGMA foreign_keys=ON'); c.execute('BEGIN IMMEDIATE')
            yield c
            c.commit()
        except Exception:
            c.rollback(); raise
        finally: c.close()
    with db() as c:
        c.executescript('''
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,country TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),csrf TEXT NOT NULL,expires REAL NOT NULL);
CREATE TABLE IF NOT EXISTS goals(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),query TEXT NOT NULL,created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS applications(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),opportunity_id TEXT NOT NULL,status TEXT NOT NULL,version INTEGER NOT NULL,payload TEXT NOT NULL,approval_hash TEXT,receipt TEXT,policy_reason TEXT NOT NULL,UNIQUE(user_id,opportunity_id));
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT NOT NULL,action TEXT NOT NULL,application_id TEXT,created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS source_records(user_id TEXT NOT NULL REFERENCES users(id),source_id TEXT NOT NULL,last_attempt_at REAL NOT NULL,attempt_id TEXT NOT NULL,last_error TEXT,content_hash TEXT,retrieved_at REAL,excerpt TEXT,changed INTEGER NOT NULL DEFAULT 0,truncated INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(user_id,source_id));
CREATE TABLE IF NOT EXISTS login_limits(key TEXT PRIMARY KEY,attempts INTEGER NOT NULL,started REAL NOT NULL);
''')
    with db() as c:
        if 'approval_expires' not in {r['name'] for r in c.execute('PRAGMA table_info(applications)')}:
            c.execute('ALTER TABLE applications ADD COLUMN approval_expires REAL')
    with db() as c:
        if 'user_id' not in {r['name'] for r in c.execute('PRAGMA table_info(login_limits)')}:
            c.execute('ALTER TABLE login_limits ADD COLUMN user_id TEXT')
    with db() as c:
        if 'truncated' not in {r['name'] for r in c.execute('PRAGMA table_info(source_records)')}:
            c.execute('ALTER TABLE source_records ADD COLUMN truncated INTEGER NOT NULL DEFAULT 0')
    def audit(c,uid,action,aid=None):
        c.execute('INSERT INTO audit(user_id,action,application_id,created_at) VALUES(?,?,?,?)',(uid,action,aid,time.time()))
    def identity(req,c,mutate=False):
        raw=req.cookies.get('hunter_session','')
        u=c.execute('SELECT u.*,s.csrf FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND s.expires>?',(hashlib.sha256(raw.encode()).hexdigest(),time.time())).fetchone()
        if not u: raise HTTPException(401,'Sign in required')
        if mutate and not hmac.compare_digest(req.headers.get('X-CSRF-Token',''),u['csrf']): raise HTTPException(403,'CSRF token required')
        return u
    def public(u,csrf=None): return {'id':u['id'],'email':u['email'],'country':u['country'],'csrf_token':csrf or u['csrf']}
    def session(c,u,r):
        token=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(32)
        c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),u['id'],csrf,time.time()+43200))
        r.set_cookie('hunter_session',token,httponly=True,samesite='strict',secure=settings.secure_cookie,max_age=43200,path='/')
        return public(u,csrf)
    def pw(password,salt=None):
        salt=salt or secrets.token_hex(16)
        return salt+':'+hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),310000).hex()
    @app.middleware('http')
    async def headers(req,call_next):
        if settings.environment=='production' and req.url.scheme!='https' and req.url.path!='/api/health':
            return Response(content='HTTPS required',status_code=400)
        if req.method in {'POST','PUT','PATCH','DELETE'}:
            origins=req.headers.getlist('origin')
            if len(origins)>1: return Response(content='Ambiguous Origin denied',status_code=403)
            origin=origins[0] if origins else None
            if origins:
                if settings.environment=='production':
                    try: trusted=normalize_origin(origin) in settings.trusted_origins
                    except ConfigurationError: trusted=False
                else: trusted=origin == str(req.base_url).rstrip('/')
                if not trusted: return Response(content='Cross-origin request denied',status_code=403)
            if req.headers.get('sec-fetch-site')=='cross-site':
                return Response(content='Cross-site request denied',status_code=403)
        r=await call_next(req)
        r.headers.update({'X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})
        if settings.environment=='production': r.headers['Strict-Transport-Security']='max-age=31536000'
        if req.url.path.startswith('/api/'): r.headers['Cache-Control']='no-store'
        return r
    @app.get('/api/health')
    def health():
        with db() as c: c.execute('SELECT 1')
        return {'status':'ok','mode':'sandbox','external_registration_enabled':False}
    @app.post('/api/auth/register',status_code=201)
    def register(data:Credentials,response:Response):
        if len(data.password)<12: raise HTTPException(422,'Password requires 12 characters')
        with db() as c:
            u={'id':secrets.token_hex(16),'email':data.email,'country':data.country}
            try: c.execute('INSERT INTO users VALUES(?,?,?,?)',(u['id'],data.email,pw(data.password),data.country))
            except sqlite3.IntegrityError: raise HTTPException(409,'Account already exists')
            audit(c,u['id'],'account_created')
            return session(c,u,response)
    @app.post('/api/auth/login')
    def login(data:Credentials,response:Response,request:Request):
        failure=False
        with db() as c:
            c.execute('DELETE FROM login_limits WHERE started<=?',(time.time()-900,))
            key=hashlib.sha256((data.email+'|'+(request.client.host if request.client else '')).encode()).hexdigest()
            limit=c.execute('SELECT * FROM login_limits WHERE key=?',(key,)).fetchone()
            if limit and limit['started']>time.time()-900 and limit['attempts']>=10: raise HTTPException(429,'Too many attempts; retry in 15 minutes')
            u=c.execute('SELECT * FROM users WHERE email=?',(data.email,)).fetchone()
            stored=u['password'] if u else pw('dummy-password','0'*32)
            if not u or not hmac.compare_digest(stored,pw(data.password,stored.split(':')[0])):
                if limit and limit['started']>time.time()-900: c.execute('UPDATE login_limits SET attempts=attempts+1,user_id=? WHERE key=?',(u['id'] if u else None,key))
                else: c.execute('INSERT OR REPLACE INTO login_limits(key,attempts,started,user_id) VALUES(?,1,?,?)',(key,time.time(),u['id'] if u else None))
                failure=True
            else:
                c.execute('DELETE FROM login_limits WHERE key=?',(key,)); result=session(c,u,response)
        if failure: raise HTTPException(401,'Invalid email or password')
        return result
    @app.get('/api/me')
    def me(request:Request):
        with db() as c: return public(identity(request,c))
    @app.post('/api/auth/logout')
    def logout(request:Request,response:Response):
        with db() as c:
            identity(request,c,True)
            c.execute('DELETE FROM sessions WHERE token=?',(hashlib.sha256(request.cookies['hunter_session'].encode()).hexdigest(),))
        response.delete_cookie('hunter_session'); return {'status':'signed_out'}
    @app.get('/api/goals')
    def goals(request:Request):
        with db() as c:
            u=identity(request,c)
            return [dict(r) for r in c.execute('SELECT id,query,created_at FROM goals WHERE user_id=? ORDER BY created_at DESC',(u['id'],))]
    @app.post('/api/goals',status_code=201)
    def add_goal(data:Goal,request:Request):
        with db() as c:
            u=identity(request,c,True); g={'id':secrets.token_hex(16),'query':data.query,'created_at':time.time()}
            c.execute('INSERT INTO goals VALUES(?,?,?,?)',(g['id'],u['id'],g['query'],g['created_at'])); audit(c,u['id'],'goal_created'); return g
    @app.get('/api/opportunities')
    def opportunities(request:Request,goal_id:str|None=None):
        with db() as c:
            u=identity(request,c); query=''
            if goal_id:
                g=c.execute('SELECT query FROM goals WHERE id=? AND user_id=?',(goal_id,u['id'])).fetchone()
                if not g: raise HTTPException(404,'Goal not found')
                query=g['query'].lower()
            rows=[{**o,'relevance':sum(w in (o['title']+' '+o['description']).lower() for w in query.split()),'policy_reason':policy(o,u['country'])} for o in OPPORTUNITIES.values()]
            return sorted([r for r in rows if not query or r['relevance']>0],key=lambda r:r['relevance'],reverse=True)
    def app_public(row):
        r=dict(row); r.pop('user_id',None); r.pop('approval_hash',None); r['payload']=json.loads(r['payload']); r['title']=OPPORTUNITIES[r['opportunity_id']]['title']; r['action']={'name':'sandbox.register','destination':OPPORTUNITIES[r['opportunity_id']]['source_url'],'adapter_version':1}; return r
    def get(c,u,aid):
        row=c.execute('SELECT * FROM applications WHERE id=? AND user_id=?',(aid,u['id'])).fetchone()
        if not row: raise HTTPException(404,'Application not found')
        return row
    def fingerprint(row): return hashlib.sha256((row['opportunity_id']+'|'+str(row['version'])+'|'+row['payload']+'|'+json.dumps({'action':'sandbox.register','adapter_version':1,'destination':OPPORTUNITIES[row['opportunity_id']]['source_url'],'required_fields':OPPORTUNITIES[row['opportunity_id']]['required_fields']},sort_keys=True)).encode()).hexdigest()
    @app.get('/api/applications')
    def applications(request:Request):
        with db() as c:
            u=identity(request,c)
            return [app_public(r) for r in c.execute('SELECT * FROM applications WHERE user_id=?',(u['id'],))]
    @app.post('/api/applications',status_code=201)
    def create_application(data:NewApplication,request:Request):
        with db() as c:
            u=identity(request,c,True); o=OPPORTUNITIES.get(data.opportunity_id)
            if not o: raise HTTPException(404,'Opportunity not found')
            existing=c.execute('SELECT * FROM applications WHERE user_id=? AND opportunity_id=?',(u['id'],data.opportunity_id)).fetchone()
            if existing:
                expired=existing['status']=='ready' and (not existing['approval_expires'] or existing['approval_expires']<=time.time())
                if existing['status']=='revoked' or expired:
                    reason=policy(o,u['country'])
                    c.execute('UPDATE applications SET status=?,version=version+1,approval_hash=NULL,approval_expires=NULL,policy_reason=? WHERE id=?',('blocked' if reason else 'awaiting_approval',reason,existing['id']))
                    audit(c,u['id'],'application_renewed',existing['id'])
                    return app_public(get(c,u,existing['id']))
                return app_public(existing)
            reason=policy(o,u['country']); aid=secrets.token_hex(16); payload=json.dumps({'email':u['email']},sort_keys=True)
            c.execute('INSERT INTO applications(id,user_id,opportunity_id,status,version,payload,approval_hash,receipt,policy_reason) VALUES(?,?,?,?,1,?,NULL,NULL,?)',(aid,u['id'],data.opportunity_id,'blocked' if reason else 'awaiting_approval',payload,reason)); audit(c,u['id'],'application_created',aid)
            return app_public(get(c,u,aid))
    @app.post('/api/applications/{aid}/approve')
    def approve(aid:str,data:Approval,request:Request):
        with db() as c:
            u=identity(request,c,True); row=get(c,u,aid)
            if row['status']!='awaiting_approval' or row['version']!=data.version: raise HTTPException(409,'Approval stale or action ineligible')
            reason=policy(OPPORTUNITIES[row['opportunity_id']],u['country'])
            if reason: raise HTTPException(409,reason)
            c.execute('UPDATE applications SET status=?,approval_hash=?,approval_expires=? WHERE id=?',('ready',fingerprint(row),time.time()+900,aid)); audit(c,u['id'],'approval_granted',aid)
            return app_public(get(c,u,aid))
    @app.post('/api/applications/{aid}/submit')
    def submit(aid:str,request:Request):
        with db() as c:
            u=identity(request,c,True); row=get(c,u,aid)
            if row['status']=='submitted': return app_public(row)
            if row['status']!='ready' or row['approval_hash']!=fingerprint(row) or not row['approval_expires'] or row['approval_expires']<=time.time(): raise HTTPException(409,'Current explicit approval required')
            reason=policy(OPPORTUNITIES[row['opportunity_id']],u['country'])
            if reason: raise HTTPException(409,reason)
            c.execute('UPDATE applications SET status=?,receipt=? WHERE id=?',('submitted','SANDBOX-'+secrets.token_hex(12),aid)); audit(c,u['id'],'sandbox_submitted',aid)
            return app_public(get(c,u,aid))
    @app.post('/api/applications/{aid}/revoke')
    def revoke(aid:str,request:Request):
        with db() as c:
            u=identity(request,c,True); row=get(c,u,aid)
            if row['status']=='submitted': raise HTTPException(409,'Submission completed; cannot undo')
            c.execute('UPDATE applications SET status=?,approval_hash=NULL,version=version+1 WHERE id=?',('revoked',aid)); audit(c,u['id'],'approval_revoked',aid)
            return app_public(get(c,u,aid))
    @app.get('/api/audit')
    def audit_log(request:Request):
        with db() as c:
            u=identity(request,c)
            return [dict(r) for r in c.execute('SELECT id,action,application_id,created_at FROM audit WHERE user_id=? ORDER BY id DESC LIMIT 200',(u['id'],))]
    @app.get('/api/sources')
    def list_sources(request:Request):
        with db() as c:
            u=identity(request,c)
            rows={r['source_id']:r for r in c.execute('SELECT * FROM source_records WHERE user_id=?',(u['id'],))}
            return [source_view(sid,rows.get(sid)) for sid in REGISTRY]

    @app.get('/api/sources/{source_id}/analysis')
    def source_analysis(source_id:str,request:Request):
        with db() as c:
            u=identity(request,c)
            if source_id not in REGISTRY: raise HTTPException(404,'Source not found')
            row=c.execute('SELECT * FROM source_records WHERE user_id=? AND source_id=?',(u['id'],source_id)).fetchone()
            return analyze_source(source_view(source_id,row))

    @app.post('/api/sources/{source_id}/refresh')
    def refresh_source(source_id:str,data:SourceRefresh,request:Request):
        # Claim the persistent cooldown while holding a short transaction, then
        # release the DB before doing any remote I/O.
        with db() as c:
            u=identity(request,c,True)
            if source_id not in REGISTRY: raise HTTPException(404,'Source not found')
            row=c.execute('SELECT * FROM source_records WHERE user_id=? AND source_id=?',(u['id'],source_id)).fetchone()
            now=time.time()
            if row and now-row['last_attempt_at']<COOLDOWN_SECONDS:
                raise HTTPException(429,'Source refresh cooldown: retry after 60 seconds')
            attempt=secrets.token_hex(16)
            c.execute('INSERT INTO source_records(user_id,source_id,last_attempt_at,attempt_id,last_error) VALUES(?,?,?,?,?) ON CONFLICT(user_id,source_id) DO UPDATE SET last_attempt_at=excluded.last_attempt_at,attempt_id=excluded.attempt_id,last_error=excluded.last_error',(u['id'],source_id,now,attempt,'refresh_in_progress'))
            uid=u['id']
        failure=None
        try:
            evidence=fetch_source(source_id,source_transport)
        except SourceFailure as exc:
            failure=str(exc)
        with db() as c:
            # Account deletion during a fetch must never recreate private state.
            if not c.execute('SELECT 1 FROM users WHERE id=?',(uid,)).fetchone():
                raise HTTPException(401,'Account no longer exists')
            row=c.execute('SELECT * FROM source_records WHERE user_id=? AND source_id=?',(uid,source_id)).fetchone()
            if not row or row['attempt_id']!=attempt: raise HTTPException(409,'Refresh superseded')
            if failure:
                c.execute('UPDATE source_records SET last_error=? WHERE user_id=? AND source_id=?',(failure,uid,source_id))
                audit(c,uid,'source_refresh_failed')
            else:
                changed=bool(row['content_hash'] and row['content_hash']!=evidence['content_hash'])
                c.execute('UPDATE source_records SET last_error=NULL,content_hash=?,retrieved_at=?,excerpt=?,changed=?,truncated=? WHERE user_id=? AND source_id=?',(evidence['content_hash'],evidence['retrieved_at'],evidence['excerpt'],int(changed),int(evidence['truncated']),uid,source_id))
                audit(c,uid,'source_refreshed')
            result=source_view(source_id,c.execute('SELECT * FROM source_records WHERE user_id=? AND source_id=?',(uid,source_id)).fetchone())
        if failure: raise HTTPException(502,'Official source refresh failed: '+failure)
        return result

    @app.get('/api/account/export')
    def export_account(request:Request,response:Response):
        with db() as c:
            u=identity(request,c)
            profile={key:u[key] for key in ['id','email','country']}
            goals=[dict(row) for row in c.execute('SELECT id,query,created_at FROM goals WHERE user_id=? ORDER BY created_at',(u['id'],))]
            applications=[app_public(row) for row in c.execute('SELECT * FROM applications WHERE user_id=? ORDER BY id',(u['id'],))]
            events=[dict(row) for row in c.execute('SELECT id,action,application_id,created_at FROM audit WHERE user_id=? ORDER BY id',(u['id'],))]
            sources=[source_view(row['source_id'],row) for row in c.execute('SELECT * FROM source_records WHERE user_id=?',(u['id'],)) if row['source_id'] in REGISTRY]
            response.headers['Content-Disposition']='attachment; filename="opportunity-hunter-export.json"'
            return {'schema_version':1,'exported_at':datetime.now(timezone.utc).isoformat(),'profile':profile,'goals':goals,'applications':applications,'audit':events,'sources':sources,'analyses':[analyze_source(source) for source in sources]}

    @app.post('/api/account/delete')
    def delete_account(data:AccountDeletion,request:Request,response:Response):
        failed=False
        with db() as c:
            u=identity(request,c,True)
            c.execute('DELETE FROM login_limits WHERE started<=?',(time.time()-900,))
            key=hashlib.sha256(('delete|'+u['id']).encode()).hexdigest()
            limit=c.execute('SELECT * FROM login_limits WHERE key=?',(key,)).fetchone()
            if limit and limit['started']>time.time()-900 and limit['attempts']>=10:
                raise HTTPException(429,'Too many attempts; retry in 15 minutes')
            if not hmac.compare_digest(u['password'],pw(data.password,u['password'].split(':')[0])):
                if limit and limit['started']>time.time()-900:
                    c.execute('UPDATE login_limits SET attempts=attempts+1,user_id=? WHERE key=?',(u['id'] if u else None,key))
                else:
                    c.execute('INSERT OR REPLACE INTO login_limits(key,attempts,started,user_id) VALUES(?,1,?,?)',(key,time.time(),u['id']))
                failed=True
            else:
                for table in ['applications','goals','audit','sessions','source_records']:
                    c.execute(f'DELETE FROM {table} WHERE user_id=?',(u['id'],))
                c.execute('DELETE FROM users WHERE id=?',(u['id'],))
                c.execute('DELETE FROM login_limits WHERE user_id=? OR key=?',(u['id'],key))
        if failed:
            raise HTTPException(401,'Current password is incorrect')
        response.delete_cookie('hunter_session',path='/')
        return {'status':'deleted'}

    web=Path(__file__).resolve().parent.parent/'web'
    if web.exists():
        app.mount('/static',StaticFiles(directory=web),name='static')
        @app.get('/')
        def index(): return FileResponse(web/'index.html')
    app.add_middleware(ExactTrustedHostMiddleware,allowed_hosts=settings.allowed_hosts,www_redirect=False)
    return app

app=create_app()
