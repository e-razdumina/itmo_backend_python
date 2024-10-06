from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from prometheus_client import Counter, Histogram
import time

# Prometheus Metrics
query_counter = Counter('db_queries_total', 'Total number of database queries', ['operation'])
query_duration_histogram = Histogram('db_query_duration_seconds', 'Histogram of query durations', ['operation'])


# CRUD for Item
def get_item(db: Session, item_id: int) -> Optional[models.Item]:
    query_counter.labels(operation="get_item").inc()
    start_time = time.time()

    item = db.query(models.Item).filter(models.Item.id == item_id).first()

    duration = time.time() - start_time
    query_duration_histogram.labels(operation="get_item").observe(duration)

    return item


def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    query_counter.labels(operation="create_item").inc()
    start_time = time.time()

    db_item = models.Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    duration = time.time() - start_time
    query_duration_histogram.labels(operation="create_item").observe(duration)

    return db_item


def update_item(db: Session, item_id: int, item: schemas.ItemCreate) -> Optional[models.Item]:
    query_counter.labels(operation="update_item").inc()
    start_time = time.time()

    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item:
        db_item.name = item.name
        db_item.price = item.price
        db.commit()
        db.refresh(db_item)

    duration = time.time() - start_time
    query_duration_histogram.labels(operation="update_item").observe(duration)

    return db_item


def soft_delete_item(db: Session, item_id: int) -> Optional[models.Item]:
    query_counter.labels(operation="soft_delete_item").inc()
    start_time = time.time()

    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item:
        db_item.deleted = True
        db.commit()
        db.refresh(db_item)

    duration = time.time() - start_time
    query_duration_histogram.labels(operation="soft_delete_item").observe(duration)

    return db_item


def get_items(
        db: Session,
        offset: int = 0,
        limit: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        show_deleted: bool = False,
) -> List[models.Item]:
    query_counter.labels(operation="get_items").inc()
    start_time = time.time()

    query = db.query(models.Item)

    if min_price is not None:
        query = query.filter(models.Item.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Item.price <= max_price)

    if not show_deleted:
        query = query.filter(models.Item.deleted.is_(False))

    items = query.offset(offset).limit(limit).all()

    duration = time.time() - start_time
    query_duration_histogram.labels(operation="get_items").observe(duration)

    return items


# CRUD for Cart
def create_cart(db: Session) -> models.Cart:
    query_counter.labels(operation="create_cart").inc()
    start_time = time.time()

    db_cart = models.Cart(price=0.0)
    db.add(db_cart)
    db.commit()
    db.refresh(db_cart)

    duration = time.time() - start_time
    query_duration_histogram.labels(operation="create_cart").observe(duration)

    return db_cart


def get_cart(db: Session, cart_id: int) -> Optional[models.Cart]:
    query_counter.labels(operation="get_cart").inc()
    start_time = time.time()

    cart = db.query(models.Cart).filter(models.Cart.id == cart_id).first()

    duration = time.time() - start_time
    query_duration_histogram.labels(operation="get_cart").observe(duration)

    return cart


def add_item_to_cart(db: Session, cart_id: int, item_id: int, quantity: int = 1) -> Optional[models.Cart]:
    query_counter.labels(operation="add_item_to_cart").inc()
    start_time = time.time()

    cart = db.query(models.Cart).filter(models.Cart.id == cart_id).first()
    item = db.query(models.Item).filter(models.Item.id == item_id).first()

    if cart and item:
        cart_item = models.CartItem(cart_id=cart_id, item_id=item_id, quantity=quantity, price=item.price)
        db.add(cart_item)
        db.commit()

        # Recalculate cart total price
        total_price = sum(ci.price * ci.quantity for ci in cart.items)
        cart.price = total_price
        db.commit()
        db.refresh(cart)

    duration = time.time() - start_time
    query_duration_histogram.labels(operation="add_item_to_cart").observe(duration)

    return cart


def get_carts(
        db: Session,
        offset: int = 0,
        limit: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_quantity: Optional[int] = None,
        max_quantity: Optional[int] = None,
) -> List[models.Cart]:
    query_counter.labels(operation="get_carts").inc()
    start_time = time.time()

    query = db.query(models.Cart).join(models.CartItem)

    # Apply price filters
    if min_price is not None:
        query = query.filter(models.Cart.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Cart.price <= max_price)

    query = query.group_by(models.Cart.id)

    # Apply quantity filters
    if min_quantity is not None:
        query = query.having(func.sum(models.CartItem.quantity) >= min_quantity)
    if max_quantity is not None:
        query = query.having(func.sum(models.CartItem.quantity) <= max_quantity)

    carts = query.offset(offset).limit(limit).all()

    duration = time.time() - start_time
    query_duration_histogram.labels(operation="get_carts").observe(duration)

    return carts
