
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import os


app = FastAPI(title="Mini E-commerce API")


# =====================================
# 1. AUTHENTICATION CONFIGURATION
# =====================================

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = PasswordHasher()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# =====================================
# 2. USER DATABASE (DEMO)
# =====================================

fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123")
    }
}


# =====================================
# 3. PASSWORD FUNCTIONS
# =====================================

def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(
            hashed_password,
            plain_password
        )
    except VerifyMismatchError:
        return False


def authenticate_user(username, password):

    user = fake_users_db.get(username)

    if not user:
        return False

    if not verify_password(
        password,
        user["hashed_password"]
    ):
        return False

    return user


# =====================================
# 4. CREATE JWT ACCESS TOKEN
# =====================================

def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    token = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


# =====================================
# 5. VERIFY JWT TOKEN
# =====================================

def get_current_user(
    token: str = Depends(oauth2_scheme)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")

        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = fake_users_db.get(username)

    if user is None:
        raise credentials_exception

    return user


# =====================================
# 6. LOGIN API
# =====================================

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    user = authenticate_user(
        form_data.username,
        form_data.password
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(
        data={"sub": user["username"]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# =====================================
# 7. PRODUCT STORAGE
# =====================================

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


# =====================================
# 8. PYDANTIC MODELS
# =====================================

class Product(BaseModel):
    name: str
    price: float
    stock: int


class ProductPatch(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None


# =====================================
# 9. GET ALL PRODUCTS
# =====================================

@app.get("/products")
def get_products(
    current_user: dict = Depends(get_current_user)
):

    return products


# =====================================
# 10. GET PRODUCT BY ID
# =====================================

@app.get("/products/{product_id}")
def get_product(
    product_id: int,
    current_user: dict = Depends(get_current_user)
):

    for product in products:

        if product["id"] == product_id:
            return product

    raise HTTPException(
        status_code=404,
        detail="Product not found"
    )


# =====================================
# 11. CREATE PRODUCT
# =====================================

@app.post("/products", status_code=201)
def create_product(
    product: Product,
    current_user: dict = Depends(get_current_user)
):

    new_product = product.model_dump()

    new_product["id"] = max(
        (p["id"] for p in products),
        default=0
    ) + 1

    products.append(new_product)

    return new_product


# =====================================
# 12. UPDATE ENTIRE PRODUCT (PUT)
# =====================================

@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    updated_product: Product,
    current_user: dict = Depends(get_current_user)
):

    for index, product in enumerate(products):

        if product["id"] == product_id:

            products[index] = {
                "id": product_id,
                **updated_product.model_dump()
            }

            return products[index]

    raise HTTPException(
        status_code=404,
        detail="Product not found"
    )


# =====================================
# 13. PARTIAL UPDATE (PATCH)
# =====================================

@app.patch("/products/{product_id}")
def patch_product(
    product_id: int,
    updated_data: ProductPatch,
    current_user: dict = Depends(get_current_user)
):

    for product in products:

        if product["id"] == product_id:

            update_fields = updated_data.model_dump(
                exclude_unset=True
            )

            product.update(update_fields)

            return product

    raise HTTPException(
        status_code=404,
        detail="Product not found"
    )


# =====================================
# 14. DELETE PRODUCT
# =====================================

@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    current_user: dict = Depends(get_current_user)
):

    for product in products:

        if product["id"] == product_id:

            products.remove(product)

            return {
                "message": "Product deleted successfully"
            }

    raise HTTPException(
        status_code=404,
        detail="Product not found"
    )
