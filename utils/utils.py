from db.client import db_client
from fastapi import  HTTPException
from db.schemas.user import user_schema
from db.schemas.product import product_schema


# buscar un usuario y devolver el schema
def search_user(field: str, key, include_password=False):

    user = db_client.users.find_one({field: key})
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user_schema(user, include_password=include_password)




# buscar un producto y devolver el schema
def search_product(field: str, key):

    product = db_client.products.find_one({field: key})
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product_schema(product)
