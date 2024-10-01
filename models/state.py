from pydantic import BaseModel, PositiveInt
from websockets.asyncio.server import serve, ServerConnection

from connect4 import Connect4
class GameStore(BaseModel):
    join_state: dict[str, (Connect4, dict[ServerConnection])] = {}