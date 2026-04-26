from pydantic import BaseModel, Field
from models.domain_models import Cadet, PastSimulation

class AppContext(BaseModel):
    role_description: str = ""
    weekly_theme: str = ""
    past_simulations: list[PastSimulation] = Field(default_factory=list)
    cadets: list[Cadet] = Field(default_factory=list)
    name_column: str = "name"

class ChatMessage(BaseModel):
    role: str
    content: str | dict[str, str]