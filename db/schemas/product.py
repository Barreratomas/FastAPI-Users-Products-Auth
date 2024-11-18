from db.models.product import Product
def product_schema(product:dict) -> Product:
    schema ={
        "id":str(product["_id"]),
        "name": product["name"],
        "description": product["description"],
        "price": product["price"]
    }
    return Product(**schema)

def products_schema(products)->list[Product] :
    return [product_schema(product) for product in products]




