from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
import httpx

from database import get_db
from config import get_settings
import models
import auth

router = APIRouter(prefix="/auth", tags=["oauth"])
settings = get_settings()

# OAuth setup
config = Config(environ={
    'GOOGLE_CLIENT_ID': settings.GOOGLE_CLIENT_ID,
    'GOOGLE_CLIENT_SECRET': settings.GOOGLE_CLIENT_SECRET,
    'GITHUB_CLIENT_ID': settings.GITHUB_CLIENT_ID,
    'GITHUB_CLIENT_SECRET': settings.GITHUB_CLIENT_SECRET,
})

oauth = OAuth(config)

# Google OAuth setup
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# GitHub OAuth setup
oauth.register(
    name='github',
    api_base_url='https://api.github.com/',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    client_kwargs={'scope': 'user:email'},
)

@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_data = token.get('userinfo')
    if not user_data:
        raise HTTPException(status_code=400, detail="Failed to get user info")
    
    # Check if user exists
    user = db.query(models.User).filter(models.User.email == user_data['email']).first()
    if not user:
        # Create new user
        user = models.User(
            email=user_data['email'],
            full_name=user_data['name'],
            profile_picture_url=user_data.get('picture'),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create access token
    access_token = auth.create_access_token(data={"sub": user.email})
    
    # Get redirect URI from query params or use default
    redirect_uri = str(request.query_params.get('redirect_uri', 'http://localhost:5173/'))
    
    # Redirect to frontend with token
    response = RedirectResponse(url=f"{redirect_uri}?token={access_token}")
    return response

@router.get("/github/login")
async def github_login(request: Request):
    redirect_uri = settings.GITHUB_REDIRECT_URI
    return await oauth.github.authorize_redirect(request, redirect_uri)

@router.get("/github/callback")
async def github_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.github.authorize_access_token(request)
    
    # Get user data from GitHub API
    async with httpx.AsyncClient() as client:
        resp = await client.get('https://api.github.com/user', 
                              headers={'Authorization': f'Bearer {token["access_token"]}'})
        user_data = resp.json()
        
        # Get user's email (it might be private)
        email_resp = await client.get('https://api.github.com/user/emails',
                                    headers={'Authorization': f'Bearer {token["access_token"]}'})
        emails = email_resp.json()
        primary_email = next(email for email in emails if email['primary'])['email']
    
    # Check if user exists
    user = db.query(models.User).filter(models.User.email == primary_email).first()
    if not user:
        # Create new user
        user = models.User(
            email=primary_email,
            full_name=user_data.get('name', user_data['login']),
            profile_picture_url=user_data.get('avatar_url'),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create access token
    access_token = auth.create_access_token(data={"sub": user.email})
    
    # Get redirect URI from query params or use default
    redirect_uri = str(request.query_params.get('redirect_uri', 'http://localhost:5173/'))
    
    # Redirect to frontend with token
    response = RedirectResponse(url=f"{redirect_uri}?token={access_token}")
    return response
