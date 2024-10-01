#!/usr/bin/env python
import asyncio
import itertools
import json
from websockets.asyncio.server import broadcast
import websockets
from websockets.asyncio.server import serve, ServerConnection

from connect4 import PLAYER1, PLAYER2, Connect4
import secrets

from constants.game_values import GameValue
from constants.messages import GameMessage
from models.event import GameEvent

JOIN = {}

# async def handler(websocket):
#     async for message in websocket:
#         print(message)

# async def handler(websocket: ServerConnection):
#     for player, column, row in [
#         (PLAYER1, 3, 0),
#         (PLAYER2, 3, 1),
#         (PLAYER1, 4, 0),
#         (PLAYER2, 4, 1),
#         (PLAYER1, 2, 0),
#         (PLAYER2, 1, 0),
#         (PLAYER1, 5, 0),
#     ]:
#         event = {
#             "type": "play",
#             "player": player,
#             "column": column,
#             "row": row,
#         }
#         await websocket.send(json.dumps(event))
#         await asyncio.sleep(0.5)
#         await asyncio.sleep(0.5)
#     event = {
#         "type": "win",
#         "player": PLAYER1,
#     }
#     await websocket.send(json.dumps(event))

# async def handler(websocket: ServerConnection):
#     # Initialize a Connect Four game.
#     game = Connect4()

async def error(websocket: ServerConnection, 
                message: str):
    event = GameEvent(type=GameValue.ERROR, message=message)
    await websocket.send(json.dumps(event.model_dump()))

async def start(websocket: ServerConnection):
    # Initialize a Connect Four game, the set of WebSocket connections
    # receiving moves from this game, and secret access token.
    game = Connect4()
    connected: set = {websocket}

    join_key = secrets.token_urlsafe(12)
    JOIN[join_key] = game, connected

    try:
        # Send the secret access token to the browser of the first player,
        # where it'll be used for building a "join" link.

        event = GameEvent(type=GameValue.INIT.value, join=join_key)
        await websocket.send(json.dumps(event.model_dump()))

        print(GameMessage.FIRST_START.value, id(game))
        print(join_key)
        async for message in websocket:
            print(GameMessage.FIRST_MOVE, message)
            await play(websocket, game, PLAYER1, connected)

    finally:
        del JOIN[join_key]

async def play(websocket: ServerConnection, 
            game: Connect4, 
            player: str, 
            connected: set[ServerConnection]):
    """
    Receive and process moves from a player.

    """
    async for message in websocket:
        # Parse a "play" event from the UI.
        event = json.loads(message)
        event = GameEvent(**event)
        assert event.type == GameValue.PLAY.value
        column = event.column

        try:
            # Play the move.
            row = game.play(player, column)
        except ValueError as exc:
            # Send an "error" event if the move was illegal.
            await error(websocket, str(exc))
            continue

        # Send a "play" event to update the UI.

        event = GameEvent(type=GameValue.PLAY.value, 
                        player=player, 
                        column=column, 
                        row=row)

        broadcast(connected, json.dumps(event.model_dump()))

        # If move is winning, send a "win" event.
        if game.winner is not None:

            event = GameEvent(type=GameValue.WIN.value, player=game.winner)

            broadcast(connected, json.dumps(event.model_dump()))

async def join(websocket: ServerConnection, join_key: str):
    # Find the Connect Four game.
    connected: set
    try:
        game, connected = JOIN[join_key]
    except KeyError:
        await error(websocket, GameMessage.GAME_NOT_FOUND)
        return

    # Register to receive moves from this game.
    connected.add(websocket)
    try:

        # Temporary - for testing.
        print(GameMessage.SECOND_JOIN, id(game))
        async for message in websocket:
            print(GameMessage.SECOND_MOVE, message)
            await play(websocket, game, PLAYER2, connected)

    finally:
        connected.remove(websocket)

async def handler(websocket: ServerConnection):
    # Receive and parse the "init" event from the UI.
    message = await websocket.recv()
    event = GameEvent(**json.loads(message))
    assert event.type == GameValue.INIT.value

    if event.join != '':
        await join(websocket, event.join)
    else:
        # First player starts a new game.
        await start(websocket)

# async def handler(websocket: ServerConnection):
#     # Initialize a Connect Four game.
#     game = Connect4()

#     # Players take alternate turns, using the same browser.
#     turns = itertools.cycle([PLAYER1, PLAYER2])
#     player = next(turns)

#     async for message in websocket:
#         # Parse a "play" event from the UI.
#         event = json.loads(message)
#         assert event["type"] == "play"
#         column = event["column"]

#         try:
#             # Play the move.
#             row = game.play(player, column)
#         except ValueError as exc:
#             # Send an "error" event if the move was illegal.
#             event = {
#                 "type": "error",
#                 "message": str(exc),
#             }
#             await websocket.send(json.dumps(event))
#             continue

#         # Send a "play" event to update the UI.
#         event = {
#             "type": "play",
#             "player": player,
#             "column": column,
#             "row": row,
#         }

#         await websocket.send(json.dumps(event))

#         # If move is winning, send a "win" event.
#         if game.winner is not None:
#             event = {
#                 "type": "win",
#                 "player": game.winner,
#             }
#             await websocket.send(json.dumps(event))

#         # Alternate turns.
#         player = next(turns)


async def main():
    async with serve(handler, "", 8001):
        await asyncio.get_running_loop().create_future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())