from fastapi import APIRouter,status,Body,HTTPException, Depends,Query
from pydantic import ValidationError
from db.models.product import Product, Product_update
from db.schemas.product import product_schema
from db.schemas.product import products_schema
from utils.utils import search_product
from db.client import db_client
from bson import ObjectId
from routers.users import auth_user, User


router=APIRouter(prefix='/products',
                #  tags sirve para la documentacion
                 tags=["products"],
                 responses={404:{"message":"no encontrado"}})

# obtener productos
@router.get(
    '/',
    response_model=list[Product],
    summary="Obtener todos los productos",
    description=(
        "Devuelve una lista de productos con soporte para paginación y filtros.\n\n"
        "- **Filtros disponibles**:\n"
        "  - `search`: Buscar productos por nombre o descripción (búsqueda parcial).\n"
        "  - `min_price` y `max_price`: Filtrar productos por rango de precios.\n"
        "- **Parámetros de paginación**:\n"
        "  - `limit`: Especifica la cantidad máxima de productos a devolver.\n"
        "  - `offset`: Especifica cuántos productos omitir desde el inicio."
    ),
)
async def get_products(
    limit: int = Query(10, ge=1, description="Cantidad de productos por página"),
    offset: int = Query(0, ge=0, description="Número de productos a omitir"),
    search: str = Query(None, description="Filtrar productos por nombre o descripción"),
    min_price: float = Query(None, ge=0, description="Filtrar productos por precio mínimo"),
    max_price: float = Query(None, ge=0, description="Filtrar productos por precio máximo")
):    
    query={}
    if search:
        query={
            "$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        }
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None:
            query["price"]["$gte"] = min_price
        if max_price is not None:
            query["price"]["$lte"] = max_price
    
    products = db_client.products.find(query).skip(offset).limit(limit)

    return  products_schema(products)
    
# obtener producto por id
@router.get(
    '/{id}',
    summary="Obtener un producto por ID",
    description="Devuelve los detalles de un producto específico usando su ID."
)
async def get_product_by_id(id:str):
    return  product_schema(db_client.products.find_one(ObjectId(id)))
    
 
# guardar producto 
@router.post(
    '/guardar',
    response_model=Product,
    status_code=201,
    summary="Guardar un nuevo producto",
    description=(
        "Permite agregar un nuevo producto a la base de datos.\n\n"
        "- **Requiere permisos de administrador**: Solo los administradores pueden usar este endpoint.\n"
        "- **Validaciones adicionales**:\n"
        "  - Se verifica que no exista otro producto con el mismo nombre."
    )
)
async def save_product(product:Product, user: User = Depends(auth_user)):
    
    if not user.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para guardar productos")
    
    #  buscar un producto con el mismo nombre
    try:
        search_product("name",product.name)
        raise HTTPException(status_code=400, detail="Este producto ya está registrado")
    except HTTPException as e:
        if e.status_code == 404:
            pass
        else:
            raise e    
        
    product_dict=dict(product)
    del product_dict['id']
     
    id=db_client.products.insert_one(product_dict).inserted_id
    product=db_client.products.find_one({"_id":id})
    return product_schema(product)


# actualizar un producto
@router.patch(
    '/{id}',
    response_model=Product,
    summary="Actualizar un producto",
    description=(
        "Permite actualizar los detalles de un producto existente dado su ID.\n\n"
        "- **Requiere permisos de administrador**: Solo los administradores pueden usar este endpoint.\n"
        "- **Validaciones adicionales**:\n"
        "  - Se verifican los datos proporcionados contra el modelo `Product_update`."
    )
)
async def update_product(id: str, product_data: dict = Body(...), user: User = Depends(auth_user)):
    if not user.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para editar productos")
    
    
    existing_product = search_product("_id",ObjectId(id))
    
    # Convertir el producto a un diccionario
    existing_product_dict = existing_product.model_dump(exclude_unset=True)
    
    
    # Validar si los campos de product_data están en el producto existente
    for key in product_data.keys():
        if key not in existing_product_dict:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El campo '{key}' no es válido para este producto.")
    
    
      # Validar los datos usando el modelo Product_update
    try:
        updated_product = Product_update(**product_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error de validación: {e.errors()}")


    
    for key, value in updated_product.model_dump(exclude_unset=True).items():
        # no actualizar estos campos
        if key in ["id", "_id"]: 
            continue
        
      
        existing_product_dict[key] = value

    try: 
        db_client.products.find_one_and_replace({"_id": ObjectId(id)}, existing_product_dict)
    except:
        raise HTTPException(status_code=400, detail="Error al actualizar el producto")
    return existing_product_dict


# eliminar un producto
@router.delete(
    '/{id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un producto",
    description=(
        "Este endpoint permite eliminar un producto de la base de datos dado su ID. "
        "Solo los usuarios con permisos de administrador pueden realizar esta acción. "
        "Si el producto no se encuentra, se devolverá un error con código 404."
    ),
)
async def delete_product(id: str, user: User = Depends(auth_user)):
    
    # Verificar que el usuario es un administrador
    if not user.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para eliminar productos")
    
    found = db_client.products.find_one_and_delete({"_id": ObjectId(id)})
    if not found:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
