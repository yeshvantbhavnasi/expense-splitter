from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from config import get_settings
import httpx
import jwt
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

async def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.get("/github/login")
async def github_login(request: Request):
    # Get the redirect_uri from query params, default to dashboard
    redirect_uri = request.query_params.get("redirect_uri", f"{settings.FRONTEND_URL}/dashboard")
    
    # GitHub OAuth login URL
    github_auth_url = "https://github.com/login/oauth/authorize"
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "user:email",
        "state": redirect_uri  # Pass the frontend redirect URI in state
    }
    
    # Construct the authorization URL
    authorization_url = f"{github_auth_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    return RedirectResponse(url=authorization_url)

@router.get("/github/callback")
async def github_callback(code: str, state: str):
    try:
        # Exchange code for access token
        token_url = "https://github.com/login/oauth/access_token"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI
                },
                headers={"Accept": "application/json"}
            )
            token_data = response.json()
            
            if "error" in token_data:
                raise HTTPException(status_code=400, detail=token_data["error_description"])
            
            access_token = token_data["access_token"]
            
            # Get user info
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            user_data = user_response.json()
            
            # Create JWT token
            jwt_token = await create_access_token({
                "sub": str(user_data["id"]),
                "email": user_data.get("email"),
                "name": user_data["name"] or user_data["login"],
                "provider": "github"
            })
            
            # Get the frontend redirect URI from state
            frontend_redirect = state or f"{settings.FRONTEND_URL}/dashboard"
            
            # Redirect to frontend with token
            redirect_url = f"{frontend_redirect}?token={jwt_token}"
            return RedirectResponse(url=redirect_url)
            
    except Exception as e:
        # Redirect to frontend with error
        error_redirect = f"{settings.FRONTEND_URL}/login?error=Authentication failed"
        return RedirectResponse(url=error_redirect)

@router.get("/google/login")
async def google_login(request: Request):
    # Get the redirect_uri from query params, default to dashboard
    redirect_uri = request.query_params.get("redirect_uri", f"{settings.FRONTEND_URL}/dashboard")
    
    # Google OAuth login URL
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "email profile",
        "access_type": "offline",
        "state": redirect_uri  # Pass the frontend redirect URI in state
    }
    
    # Construct the authorization URL
    authorization_url = f"{google_auth_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    return RedirectResponse(url=authorization_url)

@router.get("/google/callback")
async def google_callback(code: str, state: str):
    try:
        # Exchange code for access token
        token_url = "https://oauth2.googleapis.com/token"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI
                }
            )
            token_data = response.json()
            
            if "error" in token_data:
                raise HTTPException(status_code=400, detail=token_data["error_description"])
            
            access_token = token_data["access_token"]
            
            # Get user info
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_data = user_response.json()
            
            # Create JWT token
            jwt_token = await create_access_token({
                "sub": user_data["id"],
                "email": user_data["email"],
                "name": user_data["name"],
                "provider": "google"
            })
            
            # Get the frontend redirect URI from state
            frontend_redirect = state or f"{settings.FRONTEND_URL}/dashboard"
            
            # Redirect to frontend with token
            redirect_url = f"{frontend_redirect}?token={jwt_token}"
            return RedirectResponse(url=redirect_url)
            
    except Exception as e:
        # Redirect to frontend with error
        error_redirect = f"{settings.FRONTEND_URL}/login?error=Authentication failed"
        return RedirectResponse(url=error_redirect)
