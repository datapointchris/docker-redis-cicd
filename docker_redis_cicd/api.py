import json
import logging

import redis
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(filename='cache_app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Redis and SQLAlchemy connections
redis_host = 'localhost'
redis_port = 6379
pg_url = 'postgresql://your_pg_user:your_pg_password@localhost:5432/your_pg_database'

try:
    redis_conn = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    engine = create_engine(pg_url)
    Base = declarative_base()
    Session = sessionmaker(bind=engine)
except Exception as e:
    logging.error(f"Error while initializing connections: {str(e)}")
    exit(1)


# Define your SQLAlchemy model
class Person(Base):
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    email = Column(String)
    address = Column(String)


# Create a FastAPI app
app = FastAPI()


# Pydantic model for request and response
class ClientRequest(BaseModel):
    name: str


class ClientResponse(BaseModel):
    name: str
    age: int
    email: str
    address: str


# FastAPI endpoint to fetch person data
@app.post("/client_key", response_model=ClientResponse)
def fetch_data_from_redis_or_postgres(client_request: ClientRequest):
    name = client_request.name

    try:
        # Check Redis cache first
        cached_data = redis_conn.get(name)
        if cached_data:
            logging.info(f"Found data in Redis cache for name: {name}")
            return json.loads(cached_data)

        # If data not found in Redis, fetch from PostgreSQL
        session = Session()
        result = session.query(Person).filter_by(name=name).first()
        session.close()

        if result:
            data = {"name": result.name, "age": result.age, "email": result.email, "address": result.address}
            # Store the data in Redis cache for future requests
            redis_conn.set(name, json.dumps(data))
            logging.info(f"Fetched data from PostgreSQL for name: {name}")
            return data
        else:
            logging.info(f"Data not found in PostgreSQL for name: {name}")
            return None

    except Exception as e:
        logging.error(f"Error while fetching data: {str(e)}")
        return None


# Example usage:
# Send a POST request to http://localhost:8000/client_key with JSON data like: {"name": "John Doe"}
# The response will contain the person's data, including name, age, email, and address.
