from fastapi import APIRouter, HTTPException,Body,Query, status,Depends
from pydantic import ValidationError
from db.models.user import User, User_update
from db.client import db_client
from db.schemas.user import user_schema, users_schema
from bson import ObjectId
from passlib.context import CryptContext
from utils.utils import search_user
from routers.jwt_auth_users import auth_user



crypt = CryptContext(schemes=["bcrypt"])



router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Usuario no encontrado"}},
)



# obtener todos los usuarios
@router.get(
    "/",
    response_model=list[User],
    summary="Obtener todos los usuarios",
    description=(
        "Devuelve una lista de usuarios registrados con soporte para paginación y filtros.\n\n"
        "- **Filtros disponibles**:\n"
        "  - `search`: Buscar usuarios por nombre de usuario o correo electrónico.\n"
        "- **Parámetros de paginación**:\n"
        "  - `limit`: Especifica la cantidad máxima de usuarios a devolver.\n"
        "  - `offset`: Especifica cuántos usuarios omitir desde el inicio."
    ),
)
async def get_users(
    limit: int = Query(10, ge=1, description="Cantidad de usuarios por página"),
    offset: int = Query(0, ge=0, description="Número de usuarios a omitir"),
    search: str = Query(None, description="Filtrar usuarios por nombre o email")
):    
    query = {}
    if search:
        query = {
            "$or": [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
        }
        
    users = list(db_client.users.find(query).skip(offset).limit(limit))
    return users_schema(users)


# obtener a un usuario por id
@router.get(
    "/{id}",
    response_model=User,
    summary="Obtener un usuario por ID",
    description="Devuelve un usuario específico dado su ID.",
)
async def get_user(id: str):
    try:
        return search_user("_id", ObjectId(id))
    except:
        raise HTTPException(status_code=404, detail="Usuario unico no encontrado")


# guardar un usuario
@router.post(
    "/guardar",
    response_model=User,
    status_code=201,
    summary="Guardar un nuevo usuario",
    description=(
        "Crea un nuevo usuario en la base de datos.\n\n"
        "- **Validaciones**:\n"
        "  - Verifica que el email proporcionado no esté registrado.\n"
        "- **Procesos adicionales**:\n"
        "  - La contraseña del usuario se encripta antes de guardarse."
    )
)
async def save_user(user:User):

   

    # Intentar buscar un usuario con el mismo email
    try:
        search_user("email", user.email)
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    except HTTPException as e:
        if e.status_code == 404:
            pass 
        else:
            raise e 
    
    user_dict = dict(user)
    del user_dict["id"]  
    
    # Encriptar la contraseña
    hashed_password = crypt.hash(user.password)  
    user_dict["password"] = hashed_password  

    id = db_client.users.insert_one(user_dict).inserted_id
    user = db_client.users.find_one({"_id": ObjectId(id)})

    return user_schema(user, True)


# modificar un usuario
@router.patch(
    "/{id}",
    response_model=User,
    summary="Actualizar un usuario",
    description=(
        "Actualiza los datos de un usuario existente dado su ID.\n\n"
        "- **Requiere permisos de administrador**:\n"
        "  - Los usuarios no administradores solo pueden actualizar su propia información.\n"
        "- **Validaciones adicionales**:\n"
        "  - Se verifica que los campos proporcionados sean válidos y se encripta la contraseña si se actualiza."
    )
)
async def update_user(id: str, user_data: dict = Body(...), user: User = Depends(auth_user)):
    if  user.id != id:
        if not user.admin:
            raise HTTPException(status_code=403, detail="No tiene permiso para eliminar usuarios")

       
    existing_user = search_user("_id",ObjectId(id),True)
    
    # Convertir el usuario a un diccionario
    existing_user_dict = existing_user.model_dump(exclude_unset=True)
    
    
      # Validar si los campos de user_data están en user_dict
    for key in user_data.keys():
        if key not in existing_user_dict:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El campo '{key}' no es válido para este usuario.")
    
    
    # Validar los datos usando el modelo User_update
    try:
        updated_user = User_update(**user_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error de validación: {e.errors()}")



   
    for key, value in updated_user.model_dump(exclude_unset=True).items():
        # no actualizar estos campos
        if key in ["id", "_id", "email"]: 
            continue
        
        
        # hashear la contraseña
        if key == "password": 
                value = crypt.hash(value)
        
        # actualizar los valores de los campos
        existing_user_dict[key] = value
        
    try:
        db_client.users.find_one_and_replace({"_id": ObjectId(id)}, existing_user_dict)
    except:
        raise HTTPException(status_code=400, detail="Error al actualizar el usuario")
    return existing_user_dict


# eliminar un usuario
@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un usuario",
    description=(
        "Elimina un usuario de la base de datos dado su ID.\n\n"
        "- **Requiere permisos de administrador**: Solo los administradores pueden eliminar usuarios."
    )
)
async def delete_user(id: str, user: User =Depends(auth_user)):
    found = db_client.users.find_one_and_delete({"_id": ObjectId(id)})
    
    if not user.admin:
        raise HTTPException(status_code=403, detail="No tiene permiso para eliminar usuarios")

    if not found:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")



# autenticar un usuario
@router.get(
    "/user/auth",
    summary="Obtener información del usuario autenticado",
    description=(
        "Devuelve la información del usuario autenticado mediante un token JWT.\n\n"
        "- **Restricciones**:\n"
        "  - El usuario debe estar activo."
    )
)
async def me(user: User = Depends(auth_user)):
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo"
        )
    return user