from pydantic import BaseModel
from typing import List, Optional

# Pydantic models для валидации входящих данных
class MovieEvent(BaseModel):
    movie_id: int
    title: str
    action: str
    user_id: int = None
    rating: float = None
    genres: Optional[List[str]] = None
    description: str = None

class UserEvent(BaseModel):
    user_id: int
    username: str = None
    email: str = None
    action: str
    timestamp: str

class PaymentEvent(BaseModel):
    payment_id: int
    user_id: int
    amount: float
    status: str
    timestamp: str
    method_type: str = None