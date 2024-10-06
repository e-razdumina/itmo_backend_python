from fastapi import FastAPI, Depends, HTTPException, status, Query, WebSocket
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from prometheus_fastapi_instrumentator import Instrumentator
import psutil
from prometheus_client import Gauge
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .chat import websocket_endpoint
from . import schemas, crud
from .database import engine, Base, get_db


# Create a FastAPI instance and initialize the database
app = FastAPI()
Base.metadata.create_all(bind=engine)

# Instrument the app with Prometheus metrics
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app, endpoint="/metrics")

# System-level metrics
cpu_usage_gauge = Gauge('system_cpu_usage_percent', 'CPU usage percent')
memory_usage_gauge = Gauge('system_memory_usage_percent', 'Memory usage percent')
disk_usage_gauge = Gauge('system_disk_usage_percent', 'Disk usage percent')
network_io_gauge = Gauge('system_network_io_bytes', 'Network I/O bytes')


# Function to update system-level metrics
def update_system_metrics():
    cpu_usage_gauge.set(psutil.cpu_percent(interval=1))
    memory_usage_gauge.set(psutil.virtual_memory().percent)
    disk_usage_gauge.set(psutil.disk_usage('/').percent)
    network_io = psutil.net_io_counters()
    network_io_gauge.set(network_io.bytes_sent + network_io.bytes_recv)


# APScheduler for periodic task scheduling
scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def start_scheduler():
    scheduler.start()
    # Schedule the system metrics update every 5 seconds
    scheduler.add_job(update_system_metrics, "interval", seconds=5)


@app.on_event("shutdown")
async def shutdown_scheduler():
    scheduler.shutdown()


# Item Endpoints
@app.post("/item", response_model=schemas.Item, status_code=status.HTTP_201_CREATED)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item)


@app.get("/item", response_model=List[schemas.Item])
def list_items(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    min_price: Optional[float] = Query(None, ge=0.0),
    max_price: Optional[float] = Query(None, ge=0.0),
    show_deleted: bool = False
):
    items = crud.get_items(
        db,
        offset=offset,
        limit=limit,
        min_price=min_price,
        max_price=max_price,
        show_deleted=show_deleted,
    )
    if not items:
        raise HTTPException(status_code=404, detail="No items found")
    return items


@app.get("/item/{item_id}", response_model=schemas.Item)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if db_item is None or db_item.deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.put("/item/{item_id}", response_model=schemas.Item)
def update_item(item_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.update_item(db, item_id, item)


@app.patch("/item/{item_id}", response_model=schemas.Item)
def patch_item(item_id: int, item: dict, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if db_item.deleted:
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="Item is deleted and cannot be modified.")

    allowed_fields = set(schemas.Item.__fields__) - {"deleted"}
    invalid_fields = [key for key in item.keys() if key not in allowed_fields]

    if invalid_fields:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": f"Invalid fields: {invalid_fields}"}
        )

    for key, value in item.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@app.delete("/item/{item_id}", response_model=schemas.Item)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.soft_delete_item(db, item_id)


# Cart Endpoints
@app.post("/cart", response_model=schemas.Cart, status_code=status.HTTP_201_CREATED)
def create_cart(db: Session = Depends(get_db)):
    new_cart = crud.create_cart(db)
    cart_data = schemas.Cart.from_orm(new_cart)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=cart_data.dict(),
        headers={"Location": f"/cart/{new_cart.id}"}
    )


@app.get("/cart/{cart_id}", response_model=schemas.Cart)
def read_cart(cart_id: int, db: Session = Depends(get_db)):
    db_cart = crud.get_cart(db, cart_id)
    if db_cart is None:
        raise HTTPException(status_code=404, detail="Cart not found")
    return schemas.Cart.from_orm(db_cart)


@app.get("/cart", response_model=List[schemas.Cart])
def list_carts(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    min_price: Optional[float] = Query(None, ge=0.0),
    max_price: Optional[float] = Query(None, ge=0.0),
    min_quantity: Optional[int] = Query(None, ge=0),
    max_quantity: Optional[int] = Query(None, ge=0),
):
    return crud.get_carts(
        db,
        offset=offset,
        limit=limit,
        min_price=min_price,
        max_price=max_price,
        min_quantity=min_quantity,
        max_quantity=max_quantity
    )


@app.post("/cart/{cart_id}/add/{item_id}", response_model=schemas.Cart)
def add_item_to_cart(cart_id: int, item_id: int, db: Session = Depends(get_db)):
    return crud.add_item_to_cart(db, cart_id, item_id)


@app.websocket("/chat/{chat_name}")
async def websocket_chat(websocket: WebSocket, chat_name: str):
    await websocket_endpoint(websocket, chat_name)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
