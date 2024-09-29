from sqlalchemy.orm import Session
from . import models, schemas


# CRUD for Item
def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_item(db: Session, item_id: int, item: schemas.ItemCreate):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item:
        for key, value in item.dict().items():
            setattr(db_item, key, value)
        db.commit()
        db.refresh(db_item)
    return db_item


# CRUD for Cart
def create_cart(db: Session):
    db_cart = models.Cart()
    db.add(db_cart)
    db.commit()
    db.refresh(db_cart)
    return db_cart


def get_cart(db: Session, cart_id: int):
    return db.query(models.Cart).filter(models.Cart.id == cart_id).first()


def add_item_to_cart(db: Session, cart_id: int, item_id: int):
    cart = db.query(models.Cart).filter(models.Cart.id == cart_id).first()
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if cart and item:
        cart_item = models.CartItem(cart_id=cart_id, item_id=item_id, quantity=1)
        db.add(cart_item)
        cart.price += item.price
        db.commit()
        db.refresh(cart)
    return cart
