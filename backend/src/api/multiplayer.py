from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List
import asyncio

router = APIRouter()

# In-memory структуры для очереди и матчей
waiting_players: List[Dict] = []  # Каждый элемент: { "user_id": str, "websocket": WebSocket, "ready": bool }
active_matches: Dict[str, dict] = {}  # Ключ: match_id, значение: { players, battle_started, gestures, play_again }

def determine_result(gesture1: str, gesture2: str) -> str:
    # Приводим оба жеста к нижнему регистру и убираем лишние пробелы
    gesture1 = gesture1.strip().lower()
    gesture2 = gesture2.strip().lower()
    
    if gesture1 != "none" and gesture2 == "none":
        return "win"
    if gesture1 == "none" and gesture2 != "none":
        return "loss"
    if gesture1 == gesture2:
        return "draw"
    if (gesture1 == "rock" and gesture2 == "scissors") or \
       (gesture1 == "scissors" and gesture2 == "paper") or \
       (gesture1 == "paper" and gesture2 == "rock"):
        return "win"
    return "loss"



@router.websocket("/ws/multiplayer")
async def multiplayer_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_id = None
    current_match_id = None
    try:
        join_data = await websocket.receive_json()
        if join_data.get("action") != "join" or "user_id" not in join_data:
            await websocket.close(code=1008)
            return
        user_id = join_data["user_id"]
        waiting_players.append({"user_id": user_id, "websocket": websocket, "ready": False})
        await websocket.send_json({"action": "status", "message": "Вы в очереди на игру."})

        if len(waiting_players) >= 2:
            player1 = waiting_players.pop(0)
            player2 = waiting_players.pop(0)
            match_id = f"{player1['user_id']}_{player2['user_id']}"
            current_match_id = match_id
            active_matches[match_id] = {
                "players": [player1, player2],
                "battle_started": False,
                "gestures": {},
                "play_again": {}
            }
            match_msg = {"action": "match_found", "match_id": match_id, "players": [player1["user_id"], player2["user_id"]]}
            for p in [player1, player2]:
                await p["websocket"].send_json(match_msg)

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "signal":
                match = find_match_by_websocket(websocket)
                if match:
                    for p in match["players"]:
                        if p["websocket"] != websocket:
                            await p["websocket"].send_json({"action": "signal", "data": data.get("data")})
                continue

            match, current_match_id = find_match_by_websocket_and_id(websocket)
            if not match:
                continue

            if action == "ready":
                for p in match["players"]:
                    if p["websocket"] == websocket:
                        p["ready"] = True
                if all(p["ready"] for p in match["players"]):
                    match["battle_started"] = True
                    start_msg = {"action": "battle_start", "duration": 10}
                    for p in match["players"]:
                        await p["websocket"].send_json(start_msg)
                    asyncio.create_task(send_blackout_and_end(match, current_match_id))
            elif action == "unready":
                for p in match["players"]:
                    if p["websocket"] == websocket:
                        p["ready"] = False
                unready_msg = {"action": "player_unready", "user_id": user_id}
                for p in match["players"]:
                    await p["websocket"].send_json(unready_msg)
            elif action == "gesture":
                gesture_value = data.get("gesture")
                if gesture_value:
                    match["gestures"][user_id] = gesture_value
                if len(match["gestures"]) == 2:
                    await conclude_battle(match, current_match_id)
            elif action == "play_again":
                # Обработка повторной игры
                match["play_again"][user_id] = True
                # Немедленно уведомляем оппонента о желании сыграть ещё
                for p in match["players"]:
                    if p["user_id"] != user_id:
                        await p["websocket"].send_json({
                            "action": "opponent_play_again",
                            "message": f"Игрок {user_id} хочет сыграть ещё."
                        })
                if len(match["play_again"]) == 2:
                    # Сбрасываем состояние для новой битвы
                    for p in match["players"]:
                        p["ready"] = False
                    match["gestures"] = {}
                    match["play_again"] = {}
                    match["battle_started"] = False
                    replay_msg = {"action": "replay", "message": "Начните новую битву, нажмите 'Готов'."}
                    for p in match["players"]:
                        await p["websocket"].send_json(replay_msg)
            # Остальные действия...
    except WebSocketDisconnect:
        waiting_players[:] = [p for p in waiting_players if p["websocket"] != websocket]
        match, current_match_id = find_match_by_websocket_and_id(websocket)
        if match:
            disconnect_msg = {"action": "disconnect", "message": f"Игрок {user_id} отключился."}
            for p in match["players"]:
                if p["websocket"] != websocket:
                    try:
                        await p["websocket"].send_json(disconnect_msg)
                    except Exception:
                        pass
            if current_match_id in active_matches:
                del active_matches[current_match_id]

def find_match_by_websocket(ws: WebSocket):
    for m in active_matches.values():
        for p in m["players"]:
            if p["websocket"] == ws:
                return m
    return None

def find_match_by_websocket_and_id(ws: WebSocket):
    for mid, m in active_matches.items():
        for p in m["players"]:
            if p["websocket"] == ws:
                return m, mid
    return None, None

async def conclude_battle(match, match_id):
    for p in match["players"]:
        if p["user_id"] not in match["gestures"]:
            match["gestures"][p["user_id"]] = "none"
    g1 = match["gestures"][match["players"][0]["user_id"]]
    g2 = match["gestures"][match["players"][1]["user_id"]]
    res = determine_result(g1, g2)
    if res == "win":
        winner = match["players"][0]["user_id"]
    elif res == "loss":
        winner = match["players"][1]["user_id"]
    else:
        winner = "draw"
    end_msg = {"action": "battle_end", "winner": winner, "gestures": match["gestures"]}
    for p in match["players"]:
        await p["websocket"].send_json(end_msg)
    # Важно: не удаляем матч, чтобы позволить rematch через "play_again".
    match["battle_started"] = False

async def send_blackout_and_end(match, match_id):
    await asyncio.sleep(7)
    blackout_msg = {"action": "blackout", "duration": 3}
    for p in match["players"]:
        await p["websocket"].send_json(blackout_msg)
    await asyncio.sleep(3)
    if len(match["gestures"]) < 2:
        await conclude_battle(match, match_id)
