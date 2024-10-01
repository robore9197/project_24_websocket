#!/usr/bin/env python
import asyncio
import itertools
import json

import websockets
from websockets.asyncio.server import serve, ServerConnection

from connect4 import PLAYER1, PLAYER2, Connect4

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

async def handler(websocket: ServerConnection):
    # Initialize a Connect Four game.
    game = Connect4()

    # Players take alternate turns, using the same browser.
    turns = itertools.cycle([PLAYER1, PLAYER2])
    player = next(turns)

    async for message in websocket:
        # Parse a "play" event from the UI.
        event = json.loads(message)
        assert event["type"] == "play"
        column = event["column"]

        try:
            # Play the move.
            row = game.play(player, column)
        except ValueError as exc:
            # Send an "error" event if the move was illegal.
            event = {
                "type": "error",
                "message": str(exc),
            }
            await websocket.send(json.dumps(event))
            continue

        # Send a "play" event to update the UI.
        event = {
            "type": "play",
            "player": player,
            "column": column,
            "row": row,
        }

        await websocket.send(json.dumps(event))

        # If move is winning, send a "win" event.
        if game.winner is not None:
            event = {
                "type": "win",
                "player": game.winner,
            }
            await websocket.send(json.dumps(event))

        # Alternate turns.
        player = next(turns)

async def main():
    try:
        async with serve(handler, "", 8001):
            await asyncio.get_running_loop().create_future()  # run forever
    except KeyboardInterrupt as ki:
        exit(0)
        pass


if __name__ == "__main__":
    asyncio.run(main())