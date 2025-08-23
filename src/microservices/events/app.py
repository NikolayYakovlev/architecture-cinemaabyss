import os
import logging
import asyncio
import contextlib
from fastapi import FastAPI
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from models.models import MovieEvent, UserEvent, PaymentEvent
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
app = FastAPI()

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")
EVENT_TOPICS = {
    "movie": "movie-events",
    "user": "user-events",
    "payment": "payment-events"
}

producer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
    await producer.start()
    consumer_task = asyncio.create_task(consume_events())   # Запуск consumer'а в фоне
    yield
    await producer.stop()
    consumer_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await consumer_task

app = FastAPI(lifespan=lifespan)

@app.get("/api/events/health")
async def health():
    return {"status": True}

async def send_event(topic: str, event: dict):
    value = str(event).encode()
    result = await producer.send_and_wait(topic, value)
    logging.info(f"Produced event to {topic}: {event}")
    return result

@app.post("/api/events/movie", status_code=201)
async def create_movie_event(event: MovieEvent):
    result = await send_event(EVENT_TOPICS["movie"], event.model_dump())
    return {"status": "success", "partition": result.partition, "offset": result.offset, "event": event.model_dump()}

@app.post("/api/events/user", status_code=201)
async def create_user_event(event: UserEvent):
    result = await send_event(EVENT_TOPICS["user"], event.model_dump())
    return {"status": "success", "partition": result.partition, "offset": result.offset, "event": event.model_dump()}

@app.post("/api/events/payment", status_code=201)
async def create_payment_event(event: PaymentEvent):
    result = await send_event(EVENT_TOPICS["payment"], event.model_dump())
    return {"status": "success", "partition": result.partition, "offset": result.offset, "event": event.model_dump()}

async def consume_events():
    consumer = AIOKafkaConsumer(
        *EVENT_TOPICS.values(),
        bootstrap_servers=KAFKA_BROKERS,
        group_id="events-service-group",
        auto_offset_reset="earliest"
    )
    await consumer.start()
    try:
        async for msg in consumer:
            logging.info(f"Consumed from {msg.topic}: {msg.value.decode()}")
    finally:
        await consumer.stop()