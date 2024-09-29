from pydantic import BaseModel
from typing import List


class ItemBase(BaseModel):
    name: str
    price: float


class ItemCreate(ItemBase):
    pass


class Item(BaseModel):
    id: int
    name: str
    price: float
    deleted: bool

    class Config:
        from_attributes = True


class CartItemBase(BaseModel):
    item_id: int
    quantity: int


class CartItemCreate(CartItemBase):
    pass


class CartItem(CartItemBase):
    id: int
    item: Item

    class Config:
        orm_mode = True


class CartBase(BaseModel):
    price: float


class CartCreate(CartBase):
    pass


class Cart(CartBase):
    id: int
    items: List[CartItem] = []

    class Config:
        orm_mode = True
