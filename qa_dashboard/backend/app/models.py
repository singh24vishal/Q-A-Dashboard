from pydantic import BaseModel, Field
from datetime import datetime
import bcrypt  

class User(BaseModel):
    user_id: int
    username: str
    email: str
    password_hash: str  

    def verify_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


class Question(BaseModel):
    question_id: int
    user_id: int
    message: str
    status: str
    timestamp: datetime
