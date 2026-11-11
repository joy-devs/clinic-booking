from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.auth import create_access_token, verify_password

router = APIRouter(tags=["authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(form_data: LoginRequest):
    """
    Authenticate staff/admin and return a JWT access token.
    """
    # Replace this with your actual database user lookup/verification logic
    if form_data.username != "admin" or form_data.password != "secret123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout():
    """
    Log out the user. Clients should discard the stored token.
    """
    return {"detail": "Successfully logged out. Please discard your local token."}