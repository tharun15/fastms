from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.background import BackgroundTasks
from redis_om import get_redis_connection, HashModel
import redis
from starlette.requests import Request
import requests, time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_methods=['*'],
    allow_headers=['*']
)


@app.get("/")
async def root():
    return {"message": "Hello World"}

redis = redis.Redis(
  host='redis-11933.c16.us-east-1-3.ec2.redns.redis-cloud.com',
  port=11933,
  password='EIADD5b4HqdmtsB3FmHqyz98KcAwgily')


class Order(HashModel):
    product_id: str
    price: float
    fee: float
    total: float
    quantity: int
    status: str # pending, completed, refunded

    class Meta:
        database = redis


@app.get('/orders/{pk}')
def get(pk: str):
    order = Order.get(pk)
    #redis.xadd('refund_order', order.dict(), '*')
    return order

@app.post('/orders')
async def create(request: Request, background_tasks: BackgroundTasks): #id, quantity
    body = await request.json()
    req = requests.get('https://localhost:8000/products/%s' & body['id'])
    product = req.json()

    order = Order(
        product_id = body['id'],
        price=product['price'],
        fee=0.2 * product['price'],
        total=1.2 * product['price'],
        quantity=body['quantity'],
        status='pending'
    )

    order.save()
    background_tasks.add_tasks(order_completed, order)
    return order


def order_completed(order: Order):
    time.sleep(5)
    order.sattus = 'completed'
    order.save()
    redis.xadd('order_completed', order.dict(), '*')