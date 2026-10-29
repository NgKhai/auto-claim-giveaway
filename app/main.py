import os
import re
import secrets
import sqlite3
import time
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app import catalog
from app.db import connect, initialize
from app.policy import evaluate
from app.security import password_hash, password_matches, token_hash

BASE=Path(__file__).parent

def create_app(db_path=None):
    app=FastAPI(title='Opportunity Hunter',docs_url=None,redoc_url=None)
    app.state.db_path=str(db_path or os.getenv('AOH_DB_PATH','var/opportunities.db'))
    initialize(app.state.db_path)
    templates=Jinja2Templates(directory=str(BASE/'templates'))
    app.mount('/static',StaticFiles(directory=BASE/'static'),name='static')
    secure=os.getenv('AOH_SECURE_COOKIES','false').strip().lower() in {'1', 'true', 'yes'}
    attempts={}

    def database(): return connect(app.state.db_path)
    def identity(request):
        token=request.cookies.get('session','')
        with database() as db:
            row=db.execute('SELECT users.*,sessions.csrf FROM sessions JOIN users ON users.id=sessions.user_id WHERE token=? AND expires>?',(token_hash(token),time.time())).fetchone()
        return dict(row) if row else None
    def required(request):
        user=identity(request)
        if not user: raise HTTPException(401,'Sign in to continue.')
        return user
    def csrf(request,form,user=None):
        expected=user['csrf'] if user else request.cookies.get('preauth','')
        received=str(form.get('csrf',''))
        if not expected or not secrets.compare_digest(expected,received): raise HTTPException(403,'Invalid form token. Reload the page and try again.')
    def event(db,uid,action,detail): db.execute('INSERT INTO audit(user_id,action,detail) VALUES(?,?,?)',(uid,action,detail))
    def redirect(path='/'): return RedirectResponse(path,status_code=303)
    def render(request,page,**context):
        return templates.TemplateResponse(request=request,name=page,context={'user':identity(request),**context})

    @app.exception_handler(StarletteHTTPException)
    async def readable_error(request: Request, exc: StarletteHTTPException):
        if 'text/html' in request.headers.get('accept', ''):
            return templates.TemplateResponse(
                request=request, name='error.html', status_code=exc.status_code,
                context={'user': identity(request), 'message': str(exc.detail), 'status': exc.status_code},
                headers=exc.headers,
            )
        return JSONResponse({'detail': exc.detail}, status_code=exc.status_code, headers=exc.headers)

    @app.middleware('http')
    async def headers(request,call_next):
        size=request.headers.get('content-length','0')
        if size.isdigit() and int(size)>16384:
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse('Request too large',status_code=413)
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
        response.headers['Cache-Control']='no-store'
        return response

    @app.get('/healthz')
    def health():
        with database() as db: db.execute('SELECT 1').fetchone()
        return {'status':'ok','mode':'research-catalog','external_submission':False}

    @app.get('/register')
    @app.get('/login')
    def auth_form(request:Request):
        token=secrets.token_urlsafe(32)
        response=render(request,'auth.html',mode=request.url.path[1:],csrf=token,error=None)
        response.set_cookie('preauth',token,httponly=True,samesite='strict',secure=secure,max_age=1800)
        return response

    @app.post('/register')
    @app.post('/login')
    async def auth(request:Request):
        form=await request.form(); csrf(request,form)
        email=str(form.get('email','')).strip().lower(); password=str(form.get('password',''))
        key=request.client.host if request.client else 'unknown'
        now=time.time(); attempts[key]=[stamp for stamp in attempts.get(key,[]) if now-stamp<60]
        if len(attempts[key])>=10: raise HTTPException(429,'Too many attempts. Wait a minute.')
        attempts[key].append(now)
        if not re.fullmatch(r'[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,}',email) or not 12<=len(password)<=128:
            raise HTTPException(400,'Use a valid email and a password of 12–128 characters.')
        with database() as db:
            if request.url.path=='/register':
                try:
                    uid=db.execute('INSERT INTO users(email,password) VALUES(?,?)',(email,password_hash(password))).lastrowid
                    event(db,uid,'account_created','Account created; automation disabled.')
                except sqlite3.IntegrityError: raise HTTPException(400,'Unable to create account. Try signing in.')
            else:
                user=db.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
                if not user or not password_matches(password,user['password']): raise HTTPException(400,'Invalid email or password.')
                uid=user['id']
            token=secrets.token_urlsafe(32); form_token=secrets.token_urlsafe(32)
            db.execute('DELETE FROM sessions WHERE expires<=?',(now,))
            db.execute('INSERT INTO sessions VALUES(?,?,?,?)',(token_hash(token),uid,form_token,now+43200))
        response=redirect(); response.set_cookie('session',token,httponly=True,samesite='lax',secure=secure,max_age=43200)
        response.delete_cookie('preauth'); return response

    @app.post('/logout')
    async def logout(request:Request):
        user=required(request); form=await request.form(); csrf(request,form,user)
        with database() as db: db.execute('DELETE FROM sessions WHERE token=?',(token_hash(request.cookies.get('session','')),))
        response=redirect('/login'); response.delete_cookie('session'); return response

    @app.get('/')
    def dashboard(request:Request):
        user=identity(request)
        if not user:return redirect('/login')
        with database() as db:
            goals=db.execute('SELECT * FROM goals WHERE user_id=? ORDER BY id DESC',(user['id'],)).fetchall()
            applications=db.execute('SELECT * FROM applications WHERE user_id=? ORDER BY id DESC',(user['id'],)).fetchall()
            audit=db.execute('SELECT * FROM audit WHERE user_id=? ORDER BY id DESC LIMIT 30',(user['id'],)).fetchall()
            notifications=db.execute('SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 20',(user['id'],)).fetchall()
        query=str(request.query_params.get('q',''))[:300]
        results=[dict(item,decision=evaluate(item,user,user['automation'])) for item in catalog.search(query)]
        return render(request,'dashboard.html',goals=goals,applications=applications,audit=audit,notifications=notifications,results=results,query=query)

    @app.post('/goals')
    async def goal(request:Request):
        user=required(request); form=await request.form(); csrf(request,form,user)
        text=str(form.get('text','')).strip()
        if not 3<=len(text)<=300:raise HTTPException(400,'Goal must contain 3–300 characters.')
        with database() as db:
            db.execute('INSERT INTO goals(user_id,text) VALUES(?,?)',(user['id'],text)); event(db,user['id'],'goal_created','A discovery goal was saved.')
        return redirect()

    @app.post('/settings')
    async def settings(request:Request):
        user=required(request); form=await request.form(); csrf(request,form,user)
        country=str(form.get('country','')).upper()
        if not re.fullmatch('[A-Z]{2}',country):raise HTTPException(400,'Use a two-letter country code.')
        with database() as db:
            db.execute('UPDATE users SET country=?,student=?,automation=? WHERE id=?',(country,int(form.get('student')=='on'),int(form.get('automation')=='on'),user['id']))
            # No outstanding approval survives a permission/profile change.
            db.execute("UPDATE applications SET status='needs_user_action',reason='Profile or permissions changed. Re-evaluation required.' WHERE user_id=? AND status NOT IN ('cancelled','blocked')",(user['id'],))
            event(db,user['id'],'settings_changed','Profile and permissions updated; outstanding decisions invalidated.')
        return redirect('/#profile')

    @app.post('/applications')
    async def application(request:Request):
        user=required(request); form=await request.form(); csrf(request,form,user)
        item=next((x for x in catalog.CATALOG if x['id']==form.get('opportunity_id')),None)
        if not item:raise HTTPException(404,'Opportunity not found.')
        status,reason=evaluate(item,user,user['automation'])
        with database() as db:
            try: db.execute('INSERT INTO applications(user_id,opportunity_id,title,status,reason) VALUES(?,?,?,?,?)',(user['id'],item['id'],item['title'],status,reason))
            except sqlite3.IntegrityError:raise HTTPException(409,'You already track this opportunity.')
            event(db,user['id'],'application_evaluated',item['id']+': '+status+' — '+reason)
            db.execute('INSERT INTO notifications(user_id,message) VALUES(?,?)',(user['id'],item['title']+': '+reason))
        return redirect('/#applications')

    @app.post('/applications/{application_id}/{action}')
    async def update_application(request:Request,application_id:int,action:str):
        user=required(request); form=await request.form(); csrf(request,form,user)
        with database() as db:
            row=db.execute('SELECT * FROM applications WHERE id=? AND user_id=?',(application_id,user['id'])).fetchone()
            if not row:raise HTTPException(404,'Application not found.')
            if action not in ('cancel','review'):raise HTTPException(400,'Unsupported action.')
            if action=='cancel': status,reason='cancelled','Tracking cancelled by user. No external submission was made.'
            else:
                if row['status']=='cancelled':raise HTTPException(409,'Cancelled applications cannot be reviewed.')
                item=next((x for x in catalog.CATALOG if x['id']==row['opportunity_id']),None)
                if not item:raise HTTPException(409,'Opportunity is no longer available.')
                status,reason=evaluate(item,user,user['automation'])
            db.execute('UPDATE applications SET status=?,reason=? WHERE id=? AND user_id=?',(status,reason,application_id,user['id']))
            event(db,user['id'],'application_'+action,str(application_id)+': '+reason)
        return redirect('/#applications')

    @app.post('/account/delete')
    async def delete_account(request:Request):
        user=required(request);form=await request.form();csrf(request,form,user)
        if str(form.get('confirmation',''))!='DELETE':raise HTTPException(400,'Type DELETE to confirm account deletion.')
        with database() as db:db.execute('DELETE FROM users WHERE id=?',(user['id'],))
        response=redirect('/register');response.delete_cookie('session');return response

    return app

app=create_app()
