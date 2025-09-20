"""
Authentication Endpoints - Secure JWT-based authentication
Enterprise-grade authentication API with comprehensive security features
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, Field
import secrets

# PER-SERVICE INFRASTRUCTURE INTEGRATION
from ..business.auth_service import AuthenticationService, LoginResult, TokenPair, AuthContext
from ..business.user_service import UserService, UserCreateRequest, UserProfile
from ..business.base_domain_service import ServiceContext
from ..models.user_models import UserModel, UserCredentials

# Authentication models
class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6, description="2FA TOTP code")
    remember_me: bool = Field(False, description="Extended session duration")

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="JWT refresh token")

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")

class Enable2FARequest(BaseModel):
    password: str = Field(..., description="User password for verification")
    totp_code: str = Field(..., min_length=6, max_length=6, description="TOTP verification code")

class Verify2FARequest(BaseModel):
    secret: str = Field(..., description="2FA secret from setup")
    totp_code: str = Field(..., min_length=6, max_length=6, description="TOTP verification code")

class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="User email for password reset")

class PasswordResetConfirmRequest(BaseModel):
    reset_token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")

# Authentication router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Service instances
auth_service = AuthenticationService()
user_service = UserService()

# Security scheme
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> AuthContext:
    """Get current authenticated user from JWT token"""
    try:
        # Verify access token
        payload = auth_service.verify_token(credentials.credentials, "access")
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_id = payload.get("sub")
        session_id = payload.get("session_id")
        permissions = payload.get("permissions", [])
        
        # Verify session is still valid
        session = await auth_service.get_session(session_id)
        if not session or not session.is_valid:
            raise HTTPException(status_code=401, detail="Session expired")
        
        # Update session activity
        await auth_service.extend_session(session_id, hours=8)
        
        return AuthContext(
            user_id=user_id,
            session_id=session_id,
            ip_address=request.client.host if request else "unknown",
            user_agent=request.headers.get("user-agent", "") if request else "",
            permissions=permissions,
            is_admin="*" in permissions,
            expires_at=datetime.fromisoformat(payload.get("exp"))
        )
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

def get_client_info(request: Request) -> Dict[str, str]:
    """Extract client information from request"""
    return {
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent", ""),
        "x_forwarded_for": request.headers.get("x-forwarded-for", ""),
        "x_real_ip": request.headers.get("x-real-ip", "")
    }

# Authentication Endpoints
@router.post("/login", response_model=Dict[str, Any])
async def login(
    request: LoginRequest,
    http_request: Request,
    response: Response
):
    """User login with comprehensive security"""
    try:
        client_info = get_client_info(http_request)
        
        # Authenticate user
        result = await auth_service.authenticate_user(
            email=request.email,
            password=request.password,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            totp_code=request.totp_code
        )
        
        if not result.success:
            # Return specific error responses
            if result.data and result.data.requires_2fa:
                return {
                    "success": False,
                    "requires_2fa": True,
                    "message": "Two-factor authentication required"
                }
            
            if result.data and result.data.lockout_remaining:
                return {
                    "success": False,
                    "locked": True,
                    "lockout_remaining": result.data.lockout_remaining,
                    "message": result.data.error_message
                }
            
            raise HTTPException(status_code=401, detail=result.error_message or "Authentication failed")
        
        login_result = result.data
        
        # Set secure HTTP-only cookies for tokens
        if request.remember_me:
            # Extended session for remember me
            response.set_cookie(
                key="refresh_token",
                value=login_result.tokens.refresh_token,
                max_age=login_result.tokens.refresh_expires_in,
                httponly=True,
                secure=True,
                samesite="strict"
            )
        
        return {
            "success": True,
            "user_id": login_result.user_id,
            "access_token": login_result.tokens.access_token,
            "token_type": login_result.tokens.token_type,
            "expires_in": login_result.tokens.expires_in,
            "session_id": login_result.session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    try:
        result = await auth_service.refresh_access_token(request.refresh_token)
        
        if not result.success:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        tokens = result.data
        
        return {
            "success": True,
            "access_token": tokens.access_token,
            "token_type": tokens.token_type,
            "expires_in": tokens.expires_in
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")

@router.post("/logout", response_model=Dict[str, Any])
async def logout(
    auth_context: AuthContext = Depends(get_current_user),
    response: Response = None
):
    """User logout with session invalidation"""
    try:
        # Invalidate session
        await auth_service.invalidate_session(auth_context.session_id)
        
        # Clear cookies
        if response:
            response.delete_cookie(key="refresh_token")
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@router.post("/change-password", response_model=Dict[str, Any])
async def change_password(
    request: ChangePasswordRequest,
    auth_context: AuthContext = Depends(get_current_user)
):
    """Change user password"""
    try:
        # Validate password confirmation
        if request.new_password != request.confirm_password:
            raise HTTPException(status_code=400, detail="Password confirmation does not match")
        
        # Verify current password and update
        # This would be implemented in AuthenticationService
        success = await auth_service.change_password(
            user_id=auth_context.user_id,
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        return {
            "success": True,
            "message": "Password changed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password change failed: {str(e)}")

# Two-Factor Authentication Endpoints
@router.post("/2fa/setup", response_model=Dict[str, Any])
async def setup_2fa(
    auth_context: AuthContext = Depends(get_current_user)
):
    """Setup two-factor authentication"""
    try:
        # Generate 2FA secret
        secret = auth_service.generate_2fa_secret()
        
        # Get user email for QR code
        user_result = await user_service.get_user_profile(
            auth_context.user_id,
            ServiceContext(user_id=auth_context.user_id)
        )
        
        if not user_result.success:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_profile = user_result.data
        
        # Generate QR code
        qr_code = auth_service.generate_2fa_qr_code(user_profile.email, secret)
        
        return {
            "success": True,
            "secret": secret,
            "qr_code": qr_code,
            "message": "Scan the QR code with your authenticator app"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"2FA setup failed: {str(e)}")

@router.post("/2fa/enable", response_model=Dict[str, Any])
async def enable_2fa(
    request: Verify2FARequest,
    auth_context: AuthContext = Depends(get_current_user)
):
    """Enable two-factor authentication after verification"""
    try:
        success = await auth_service.enable_2fa(
            user_id=auth_context.user_id,
            secret=request.secret,
            token=request.totp_code
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Invalid TOTP code")
        
        return {
            "success": True,
            "message": "Two-factor authentication enabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enable 2FA failed: {str(e)}")

@router.post("/2fa/disable", response_model=Dict[str, Any])
async def disable_2fa(
    request: ChangePasswordRequest,
    auth_context: AuthContext = Depends(get_current_user)
):
    """Disable two-factor authentication"""
    try:
        success = await auth_service.disable_2fa(
            user_id=auth_context.user_id,
            password=request.current_password
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Invalid password")
        
        return {
            "success": True,
            "message": "Two-factor authentication disabled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Disable 2FA failed: {str(e)}")

# Password Reset Endpoints
@router.post("/password-reset/request", response_model=Dict[str, Any])
async def request_password_reset(
    request: PasswordResetRequest,
    http_request: Request
):
    """Request password reset"""
    try:
        client_info = get_client_info(http_request)
        
        # Generate reset token (implement in AuthenticationService)
        success = await auth_service.request_password_reset(
            email=request.email,
            ip_address=client_info["ip_address"]
        )
        
        # Always return success to prevent email enumeration
        return {
            "success": True,
            "message": "If the email exists, a reset link has been sent"
        }
        
    except Exception as e:
        # Log error but don't expose it to prevent information leakage
        return {
            "success": True,
            "message": "If the email exists, a reset link has been sent"
        }

@router.post("/password-reset/confirm", response_model=Dict[str, Any])
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    http_request: Request
):
    """Confirm password reset with token"""
    try:
        # Validate password confirmation
        if request.new_password != request.confirm_password:
            raise HTTPException(status_code=400, detail="Password confirmation does not match")
        
        client_info = get_client_info(http_request)
        
        success = await auth_service.confirm_password_reset(
            reset_token=request.reset_token,
            new_password=request.new_password,
            ip_address=client_info["ip_address"]
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        return {
            "success": True,
            "message": "Password reset successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")

# Session Management Endpoints
@router.get("/sessions", response_model=Dict[str, Any])
async def get_user_sessions(
    auth_context: AuthContext = Depends(get_current_user)
):
    """Get user's active sessions"""
    try:
        sessions = await auth_service.get_user_sessions(auth_context.user_id)
        
        return {
            "success": True,
            "sessions": [
                {
                    "session_id": session.session_id,
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent,
                    "created_at": session.created_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "expires_at": session.expires_at.isoformat(),
                    "is_current": session.session_id == auth_context.session_id
                }
                for session in sessions
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

@router.delete("/sessions/{session_id}", response_model=Dict[str, Any])
async def revoke_session(
    session_id: str,
    auth_context: AuthContext = Depends(get_current_user)
):
    """Revoke a specific session"""
    try:
        # Verify session belongs to user
        session = await auth_service.get_session(session_id)
        if not session or session.user_id != auth_context.user_id:
            raise HTTPException(status_code=404, detail="Session not found")
        
        await auth_service.invalidate_session(session_id)
        
        return {
            "success": True,
            "message": "Session revoked successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session revocation failed: {str(e)}")

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(
    auth_context: AuthContext = Depends(get_current_user)
):
    """Get current authenticated user information"""
    try:
        # Get user profile
        user_result = await user_service.get_user_profile(
            auth_context.user_id,
            ServiceContext(user_id=auth_context.user_id)
        )
        
        if not user_result.success:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_profile = user_result.data
        
        return {
            "success": True,
            "user": {
                "user_id": user_profile.user_id,
                "email": user_profile.email,
                "full_name": user_profile.full_name,
                "role": user_profile.role,
                "is_active": user_profile.is_active,
                "created_at": user_profile.created_at.isoformat(),
                "last_login": user_profile.last_login.isoformat() if user_profile.last_login else None
            },
            "session": {
                "session_id": auth_context.session_id,
                "permissions": auth_context.permissions,
                "is_admin": auth_context.is_admin,
                "expires_at": auth_context.expires_at.isoformat() if auth_context.expires_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user info: {str(e)}")