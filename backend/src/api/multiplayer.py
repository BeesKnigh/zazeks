from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List
import asyncio

router = APIRouter()

# In-memory структуры для очереди и матчей
waiting_players: List[Dict] = []  # Каждый элемент: { "user_id": str, "websocket": WebSocket, "ready": bool, "gesture": None }
active_matches: Dict[str, dict] = {}  # Ключ: match_id, значение: информация о матче

def determine_result(gesture1: str, gesture2: str) -> str:
    """Возвращает 'draw', 'win' или 'loss' для первого игрока."""
    if gesture1 == gesture2:
        return "draw"
    if (gesture1 == "Rock" and gesture2 == "Scissors") or \
       (gesture1 == "Scissors" and gesture2 == "Paper") or \
       (gesture1 == "Paper" and gesture2 == "Rock"):
        return "win"
    return "loss"

@router.websocket("/ws/multiplayer")
async def multiplayer_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # При подключении ожидаем сообщение вида: {"action": "join", "user_id": "..."}
        join_data = await websocket.receive_json()
        if join_data.get("action") != "join" or "user_id" not in join_data:
            await websocket.close(code=1008)
            return
        user_id = join_data["user_id"]
        waiting_players.append({"user_id": user_id, "websocket": websocket, "ready": False, "gesture": None})
        await websocket.send_json({"action": "status", "message": "Вы в очереди на игру."})
        
        # Если в очереди два игрока, создаём матч
        if len(waiting_players) >= 2:
            player1 = waiting_players.pop(0)
            player2 = waiting_players.pop(0)
            match_id = f"{player1['user_id']}_{player2['user_id']}"
            active_matches[match_id] = {
                "players": [player1, player2],
                "battle_started": False,
                "gestures": {}
            }
            match_msg = {"action": "match_found", "match_id": match_id, "players": [player1["user_id"], player2["user_id"]]}
            for p in [player1, player2]:
                await p["websocket"].send_json(match_msg)
        
        # Главный цикл обработки сообщений от клиента
        while True:
            data = await websocket.receive_json()
            # Если получено сообщение сигнала для WebRTC, пересылаем его другому игроку
            if data.get("action") == "signal":
                # Найти матч, где этот websocket участвует
                match = None
                for mid, m in active_matches.items():
                    for p in m["players"]:
                        if p["websocket"] == websocket:
                            match = m
                            break
                    if match:
                        break
                if match:
                    # Пересылаем сигнал другому игроку
                    for p in match["players"]:
                        if p["websocket"] != websocket:
                            await p["websocket"].send_json({"action": "signal", "data": data.get("data")})
                continue

            # Находим матч, в котором участвует данный websocket
            match = None
            current_match_id = None
            for mid, m in active_matches.items():
                for p in m["players"]:
                    if p["websocket"] == websocket:
                        match = m
                        current_match_id = mid
                        break
                if match:
                    break
            if not match:
                continue

            action = data.get("action")
            if action == "ready":
                for p in match["players"]:
                    if p["websocket"] == websocket:
                        p["ready"] = True
                # Если оба игрока готовы, запускаем битву
                if all(p["ready"] for p in match["players"]):
                    match["battle_started"] = True
                    start_msg = {"action": "battle_start", "duration": 10}
                    for p in match["players"]:
                        await p["websocket"].send_json(start_msg)
                    # Запускаем асинхронную задачу, которая через 7 секунд отправит blackout, а через 10 секунд завершит битву
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
                # Если оба игрока отправили свои жесты – определяем победителя
                if len(match["gestures"]) == 2:
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
                    del active_matches[current_match_id]
            # Другие действия можно расширять здесь

    except WebSocketDisconnect:
        waiting_players[:] = [p for p in waiting_players if p["websocket"] != websocket]
        for mid, m in list(active_matches.items()):
            for p in m["players"]:
                if p["websocket"] == websocket:
                    del active_matches[mid]
                    break

async def send_blackout_and_end(match, match_id):
    await asyncio.sleep(7)  # 7 секунд до blackout
    blackout_msg = {"action": "blackout", "duration": 3}
    for p in match["players"]:
        await p["websocket"].send_json(blackout_msg)
    await asyncio.sleep(3)  # оставшиеся 3 секунды (итого 10 секунд)
    # Если какой-либо игрок не отправил жест, присваиваем "none"
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
    if match_id in active_matches:
        del active_matches[match_id]
