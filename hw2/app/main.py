from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import schemas, crud
from .database import engine, Base, get_db

# Create a FastAPI instance
app = FastAPI()
Base.metadata.create_all(bind=engine)


@app.post("/item", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item)


@app.get("/item/{item_id}", response_model=schemas.Item)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.put("/item/{item_id}", response_model=schemas.Item)
def update_item(item_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.update_item(db, item_id, item)


@app.patch("/item/{item_id}", response_model=schemas.Item)
def patch_item(item_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.update_item(db, item_id, item)


@app.delete("/item/{item_id}", response_model=schemas.Item)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.soft_delete_item(db, item_id)


@app.post("/cart", response_model=schemas.Cart)
def create_cart(db: Session = Depends(get_db)):
    return crud.create_cart(db)


@app.get("/cart/{cart_id}", response_model=schemas.Cart)
def read_cart(cart_id: int, db: Session = Depends(get_db)):
    db_cart = crud.get_cart(db, cart_id)
    if db_cart is None:
        raise HTTPException(status_code=404, detail="Cart not found")
    return db_cart


@app.post("/cart/{cart_id}/add/{item_id}", response_model=schemas.Cart)
def add_item_to_cart(cart_id: int, item_id: int, db: Session = Depends(get_db)):
    return crud.add_item_to_cart(db, cart_id, item_id)


# Ensure the app can run directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
