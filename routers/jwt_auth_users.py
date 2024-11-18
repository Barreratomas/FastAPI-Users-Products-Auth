
from fastapi import APIRouter, Depends, HTTPException, status, Request
from db.models.user import User
from utils.utils import search_user
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi.responses import JSONResponse



router = APIRouter(tags=["Auth"])

ALGORITHM = "HS256"
# duracion del token en minutos 
ACCESS_TOKEN_DURATION = 20
# semilla
SECRET = "d3ff5d4192838ba63395a0e6f3506b5bced5ab80b82a6407b20bd578b2dd00fe"
# encriptado
crypt = CryptContext(schemes=["bcrypt"])




#generar un token
def create_access_token(email: str, expiration: timedelta) -> str:
    exp_time = datetime.now(timezone.utc) + expiration
    payload = {"sub": email, "exp": exp_time}
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


# decodificar y verificar un token
def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload.get("sub")  
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )



# validar usuario autenticado
async def auth_user(request: Request) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no encontrado"
        )
    email = decode_access_token(token)
    user = search_user("email", email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autorizado"
        )
    return user


# hacer login
@router.post(
    "/login",
    summary="Iniciar sesión",
    description=(
        "Genera un token de acceso para un usuario autenticado.\n\n"
        "- **Parámetros requeridos**:\n"
        "  - `username` (correo electrónico del usuario).\n"
        "  - `password` (contraseña del usuario).\n"
        "- **Proceso**:\n"
        "  1. Valida las credenciales del usuario.\n"
        "  2. Genera un token JWT con una duración de 20 minutos.\n"
        "  3. Establece el token en una cookie HTTP-only."
    )
)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    # Buscar usuario
    user = search_user("email", form.username, include_password=True)
    if not user or not crypt.verify(form.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credenciales incorrectas",
        )

    # Crear token
    token = create_access_token(user.email, timedelta(minutes=ACCESS_TOKEN_DURATION))

    # Configurar cookie
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_DURATION)
    response = JSONResponse(content={"message": "Inicio de sesión exitoso"})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="Strict",
        expires=expiration_time,
    )
    return response




