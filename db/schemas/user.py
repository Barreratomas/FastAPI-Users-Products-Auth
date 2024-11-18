from db.models.user import User
def user_schema(user:dict, include_password=False) -> User:

    """Convierte un documento de la base de datos a un modelo User."""
    schema = {
        "id": str(user["_id"]),
        "username": user["username"],
        "full_name": user["full_name"],
        "email": user["email"],
        "admin": user["admin"],
        "disabled": user["disabled"]
    }
    if include_password:
        schema["password"] = user["password"]
    return User(**schema)

def users_schema(users, include_password=False) -> list[User]:
    """Convierte una lista de documentos a una lista de esquemas de usuario."""
    return [user_schema(user, include_password) for user in users]
