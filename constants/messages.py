from enum import Enum


class GameMessage(Enum):
    GAME_NOT_FOUND = "Game not found."
    FIRST_START = "first player started game"
    FIRST_MOVE = "first player sent"

    SECOND_JOIN = "second player joined game"
    SECOND_MOVE = "second player sent"
    WIN = "win"