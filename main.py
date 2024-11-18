from  fastapi import FastAPI
from routers import products,jwt_auth_users,users
app = FastAPI(
    title="API de Gestión de Usuarios y Productos",
    description=(
        "Esta API proporciona un conjunto de funcionalidades "
        "para gestionar usuarios y productos, con autenticación segura mediante JWT.\n\n"
        "### Funcionalidades principales:\n"
        "- **Gestión de usuarios**: Consultar, crear, actualizar y eliminar usuarios.\n"
        "- **Gestión de productos**: Consultar, crear, actualizar y eliminar productos.\n"
        "- **Autenticación con JWT**: Sistema de login para generar y validar tokens JWT.\n\n"
    ),
    version="1.0.0",
)

@app.get("/", summary="Ruta raiz")
async def root():
    return {"message": "Ingrese a '/docs' para ver la documentación interactiva."}



# rutas
app.include_router(products.router)
app.include_router(users.router)
app.include_router(jwt_auth_users.router)


# iniciar server  
# python -m uvicorn main:app --reload