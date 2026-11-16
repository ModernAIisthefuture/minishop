from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Mini E-commerce API")

# In-memory product storage
products = [
    {
        "id": 1,
        "name": "Laptop",
        "price": 55000,
        "stock": 10
    },
    {
        "id": 2,
        "name": "Mobile",
        "price": 25000,
        "stock": 20
    }
]

# Pydantic model
class Product(BaseModel):
    name: str
    price: float
    stock: int


class ProductPatch(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None


# 1. GET - Get all products
@app.get("/products")
def get_products():
    return products


# 2. GET - Get product by ID
@app.get("/products/{product_id}")
def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product

    raise HTTPException(status_code=404, detail="Product not found")


# 3. POST - Create a product
@app.post("/products", status_code=201)
def create_product(product: Product):
    new_product = product.model_dump()

    new_product["id"] = max(
        (p["id"] for p in products),
        default=0
    ) + 1

    products.append(new_product)

    return new_product


# 4. PUT - Update entire product
@app.put("/products/{product_id}")
def update_product(product_id: int, updated_product: Product):
    for index, product in enumerate(products):
        if product["id"] == product_id:

            products[index] = {
                "id": product_id,
                **updated_product.model_dump()
            }

            return products[index]

    raise HTTPException(status_code=404, detail="Product not found")


# 5. PATCH - Update specific fields
@app.patch("/products/{product_id}")
def patch_product(product_id: int, updated_data: ProductPatch):
    for product in products:
        if product["id"] == product_id:

            update_fields = updated_data.model_dump(
                exclude_unset=True
            )

            product.update(update_fields)

            return product

    raise HTTPException(status_code=404, detail="Product not found")


# 6. DELETE - Delete product
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    for product in products:
        if product["id"] == product_id:

            products.remove(product)

            return {"message": "Product deleted successfully"}

    raise HTTPException(status_code=404, detail="Product not found")
