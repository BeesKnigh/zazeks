const user_id = localStorage.getItem('user_id');
const token = localStorage.getItem('accessToken');

if (!user_id || !token) {
  alert("Необходимо войти в систему");
  window.location.href = "login.html";
}

const joinQueueBtn = document.getElementById("joinQueue");
const readyBtn = document.getElementById("readyBtn");
const unreadyBtn = document.getElementById("unreadyBtn");
const playAgainBtn = document.getElementById("playAgainBtn");
const statusDiv = document.getElementById("status");
const battleTimerDiv = document.getElementById("battleTimer");
const resultDiv = document.getElementById("result");

const localVideo = document.getElementById("localVideo");
const remoteVideo = document.getElementById("remoteVideo");
const blackoutOverlay = document.getElementById("blackoutOverlay");

// Создаем canvas-оверлей для отрисовки рамок
const overlayCanvas = document.createElement('canvas');
overlayCanvas.style.position = 'absolute';
overlayCanvas.style.pointerEvents = 'none';
document.body.appendChild(overlayCanvas);
const overlayCtx = overlayCanvas.getContext('2d');

let ws;
let peer;
let localStream;
let battleCountdownInterval;
let gestureScanInterval;
let battleDuration = 10; // секунд
let battleTimer = battleDuration;
let finalGesture = "none"; // итоговый жест

// Переменная для хранения последнего корректно распознанного жеста
let lastValidGesture = "none";

// Глобальная переменная для хранения идентификаторов игроков матча
let currentMatchPlayers = [];
// Флаг для предотвращения множественного сохранения результата матча
let resultSaved = false;

const backendUrl = window.location.origin;
const wsUrl = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/multiplayer';

function updateOverlayCanvas() {
  const rect = localVideo.getBoundingClientRect();
  overlayCanvas.style.left = rect.left + "px";
  overlayCanvas.style.top = rect.top + "px";
  overlayCanvas.width = rect.width;
  overlayCanvas.height = rect.height;
}
window.addEventListener('resize', updateOverlayCanvas);
localVideo.addEventListener('loadedmetadata', updateOverlayCanvas);

async function detectGesture() {
  return new Promise((resolve, reject) => {
    try {
      const tempCanvas = document.createElement('canvas');
      const width = localVideo.videoWidth || 640;
      const height = localVideo.videoHeight || 480;
      tempCanvas.width = width;
      tempCanvas.height = height;
      const tempCtx = tempCanvas.getContext('2d');
      tempCtx.drawImage(localVideo, 0, 0, width, height);
      tempCanvas.toBlob(async (blob) => {
        if (!blob) {
          return reject("Ошибка преобразования кадра в Blob");
        }
        const formData = new FormData();
        formData.append('file', blob, 'frame.jpg');
        try {
          const response = await fetch(`${backendUrl}/model/detect`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
          });
          if (!response.ok) {
            return reject(`Ошибка детекции: ${response.status}`);
          }
          const data = await response.json();
          let detected = data.gesture === "No detection" ? "none" : data.gesture;
          // Если обнаружен корректный жест, обновляем lastValidGesture
          if (detected !== "none") {
            lastValidGesture = detected;
          }
          resolve({
            gesture: detected,
            bbox: data.bbox
          });
        } catch (err) {
          reject(err);
        }
      }, 'image/jpeg');
    } catch (e) {
      reject(e);
    }
  });
}

function drawBoundingBox(bbox) {
  updateOverlayCanvas();
  overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
  if (bbox && bbox.length === 4) {
    const [x1, y1, x2, y2] = bbox;
    const videoWidth = localVideo.videoWidth || overlayCanvas.width;
    const videoHeight = localVideo.videoHeight || overlayCanvas.height;
    const scaleX = overlayCanvas.width / videoWidth;
    const scaleY = overlayCanvas.height / videoHeight;
    overlayCtx.strokeStyle = "red";
    overlayCtx.lineWidth = 3;
    overlayCtx.strokeRect(x1 * scaleX, y1 * scaleY, (x2 - x1) * scaleX, (y2 - y1) * scaleY);
  }
}

function connectWebSocket() {
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    statusDiv.innerText = "Подключено к серверу. Ожидание очереди...";
    // Сбрасываем флаг сохранения результата при новом подключении
    resultSaved = false;
    ws.send(JSON.stringify({ action: "join", user_id: user_id }));
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    console.log("Получено:", msg);
    switch (msg.action) {
      case "status":
        statusDiv.innerText = msg.message;
        break;
      case "match_found":
        statusDiv.innerText = "Матч найден! Игроки: " + msg.players.join(", ");
        readyBtn.style.display = "inline-block";
        unreadyBtn.style.display = "inline-block";
        // Сохраняем идентификаторы игроков для дальнейшего сохранения матча
        currentMatchPlayers = msg.players;
        // Сбрасываем флаг сохранения результата при новом матче
        resultSaved = false;
        initPeerConnection(msg.match_id);
        break;
      case "signal":
        if (peer) {
          peer.signal(msg.data);
        }
        break;
      case "battle_start":
        statusDiv.innerText = "Битва начинается!";
        battleDuration = msg.duration;
        startBattle();
        break;
      case "blackout":
        statusDiv.innerText = "Последние секунды битвы: экран противника затемняется.";
        blackoutOverlay.style.opacity = 1;
        setTimeout(() => {
          blackoutOverlay.style.opacity = 0;
        }, msg.duration * 1000);
        break;
      case "battle_end":
        // Если жест, полученный от сервера, равен "none" для текущего игрока и у нас есть последний валидный жест,
        // подставляем его.
        if (msg.gestures[user_id] === "none" && lastValidGesture !== "none") {
          msg.gestures[user_id] = lastValidGesture;
        }
        statusDiv.innerText = "Битва окончена!";
        resultDiv.innerText = `Победитель: ${msg.winner}\nВаш жест: ${msg.gestures[user_id]}\nЖест противника: ${getOpponentGesture(msg.gestures)}`;
        clearInterval(battleCountdownInterval);
        clearInterval(gestureScanInterval);
        playAgainBtn.style.display = "inline-block";
        overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        // Сохраняем результат только если текущий клиент является инициатором (первым игроком)
        if (parseInt(user_id) === parseInt(currentMatchPlayers[0]) && !resultSaved) {
          saveMultiplayerResult(msg.gestures, msg.winner);
          resultSaved = true;
        }
        break;
      case "player_unready":
        statusDiv.innerText = "Один из игроков отменил готовность.";
        break;
      case "replay":
        statusDiv.innerText = msg.message;
        readyBtn.disabled = false;
        unreadyBtn.disabled = false;
        playAgainBtn.style.display = "none";
        // Сбрасываем флаг для нового матча
        resultSaved = false;
        break;
      case "opponent_play_again":
        statusDiv.innerText = msg.message;
        break;
      case "disconnect":
        statusDiv.innerText = msg.message;
        break;
      default:
        console.log("Неизвестное действие:", msg);
    }
  };

  ws.onclose = () => {
    statusDiv.innerText = "Соединение закрыто.";
  };

  ws.onerror = (err) => {
    console.error("Ошибка WebSocket:", err);
  };
}

function initPeerConnection(match_id) {
  navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    .then(stream => {
      localStream = stream;
      localVideo.srcObject = stream;
      updateOverlayCanvas();
      const isInitiator = (parseInt(user_id) === parseInt(match_id.split("_")[0]));
      peer = new SimplePeer({
        initiator: isInitiator,
        trickle: true,
        stream: localStream,
        config: { iceServers: [{ urls: "stun:stun.l.google.com:19302" }] }
      });

      peer.on('signal', data => {
        ws.send(JSON.stringify({ action: "signal", data: data }));
      });

      peer.on('stream', stream => {
        remoteVideo.srcObject = stream;
      });

      peer.on('error', err => {
        console.error("Ошибка в SimplePeer:", err);
      });
    })
    .catch(err => {
      console.error("Ошибка получения видеопотока:", err);
    });
}

function getOpponentGesture(gestures) {
  for (let key in gestures) {
    if (key !== user_id) return gestures[key];
  }
  return "none";
}

readyBtn.addEventListener("click", () => {
  ws.send(JSON.stringify({ action: "ready", user_id: user_id }));
  readyBtn.disabled = true;
  unreadyBtn.disabled = false;
});

unreadyBtn.addEventListener("click", () => {
  ws.send(JSON.stringify({ action: "unready", user_id: user_id }));
  readyBtn.disabled = false;
  unreadyBtn.disabled = true;
});

function startBattle() {
  battleTimer = battleDuration;
  battleTimerDiv.innerText = `Битва: ${battleTimer} сек`;

  battleCountdownInterval = setInterval(() => {
    battleTimer--;
    battleTimerDiv.innerText = `Битва: ${battleTimer} сек`;
    if (battleTimer <= 0) {
      clearInterval(battleCountdownInterval);
      clearInterval(gestureScanInterval);
      // Проводим финальную детекцию
      detectGesture().then((detection) => {
        finalGesture = (detection.gesture === "none" && lastValidGesture !== "none") ? lastValidGesture : detection.gesture;
        ws.send(JSON.stringify({ action: "gesture", gesture: finalGesture, user_id: user_id }));
      }).catch(err => {
        console.error("Ошибка финальной детекции:", err);
        ws.send(JSON.stringify({ action: "gesture", gesture: finalGesture, user_id: user_id }));
      });
    }
  }, 1000);

  gestureScanInterval = setInterval(async () => {
    try {
      const detection = await detectGesture();
      if (detection.gesture !== "none") {
        lastValidGesture = detection.gesture;
      }
      finalGesture = detection.gesture;
      drawBoundingBox(detection.bbox);
      console.log("Детекция:", detection);
    } catch (err) {
      console.error("Ошибка детекции:", err);
    }
  }, 2000);
}

joinQueueBtn.addEventListener("click", () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    connectWebSocket();
  } else {
    ws.send(JSON.stringify({ action: "join", user_id: user_id }));
  }
});

playAgainBtn.addEventListener("click", () => {
  playAgainBtn.style.display = "none";
  ws.send(JSON.stringify({ action: "play_again", user_id: user_id }));
});

// Функция для сохранения результатов онлайн матча через API
async function saveMultiplayerResult(gestures, winner) {
  if (!currentMatchPlayers || currentMatchPlayers.length < 2) {
    console.error("Недостаточно данных о матче для сохранения результата.");
    return;
  }
  const resultValue = (winner === "draw") 
    ? "draw" 
    : (parseInt(winner) === parseInt(currentMatchPlayers[0]) ? "player1" : "player2");
  const payload = {
    player1_id: parseInt(currentMatchPlayers[0]),
    player2_id: parseInt(currentMatchPlayers[1]),
    player1_gesture: gestures[currentMatchPlayers[0]].toLowerCase(),
    player2_gesture: gestures[currentMatchPlayers[1]].toLowerCase(),
    result: resultValue
  };
  
  try {
    const response = await fetch(`${backendUrl}/multiplayer/result`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      console.error("Ошибка сохранения результата матча");
    } else {
      const data = await response.json();
      console.log("Результат матча сохранён:", data);
    }
  } catch (err) {
    console.error("Ошибка при сохранении результата матча:", err);
  }
}
