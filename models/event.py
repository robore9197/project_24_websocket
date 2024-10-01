from pydantic import BaseModel, PositiveInt
class GameEvent(BaseModel):
    type: str = 'init'
    player: str = ""
    column: int | None = None
    row: int | None = None
    message: str = ""
    join: str = ""