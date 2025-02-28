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

// Определяем базовый URL для API запросов
const backendUrl = window.location.origin;
// Определяем URL для WebSocket (учитываем протокол: wss для HTTPS, ws для HTTP)
const wsUrl = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/multiplayer';

// Функция для обновления позиции и размера canvas в соответствии с localVideo
function updateOverlayCanvas() {
  const rect = localVideo.getBoundingClientRect();
  overlayCanvas.style.left = rect.left + "px";
  overlayCanvas.style.top = rect.top + "px";
  overlayCanvas.width = rect.width;
  overlayCanvas.height = rect.height;
}
window.addEventListener('resize', updateOverlayCanvas);
localVideo.addEventListener('loadedmetadata', updateOverlayCanvas);

/**
 * Детекция жеста через модель.
 * Захватывает кадр из localVideo и отправляет на /model/detect.
 * Возвращает объект {gesture, bbox}. Если модель не обнаружила жест – gesture = "none".
 */
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
          resolve({
            gesture: data.gesture === "No detection" ? "none" : data.gesture,
            bbox: data.bbox // предполагается, что bbox имеет формат [x1, y1, x2, y2]
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

/**
 * Рисует прямоугольник на оверлее, если bbox передан.
 */
function drawBoundingBox(bbox) {
  updateOverlayCanvas();
  overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
  if (bbox && bbox.length === 4) {
    // Приводим координаты к размеру видео (если требуется масштабирование)
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

/**
 * Устанавливаем WebSocket-соединение для сигналинга и управления битвой.
 */
function connectWebSocket() {
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    statusDiv.innerText = "Подключено к серверу. Ожидание очереди...";
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
        statusDiv.innerText = "Битва окончена!";
        resultDiv.innerText = `Победитель: ${msg.winner}\nВаш жест: ${msg.gestures[user_id]}\nЖест противника: ${getOpponentGesture(msg.gestures)}`;
        clearInterval(battleCountdownInterval);
        clearInterval(gestureScanInterval);
        playAgainBtn.style.display = "inline-block";
        // Очищаем оверлей
        overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        break;
      case "player_unready":
        statusDiv.innerText = "Один из игроков отменил готовность.";
        break;
      case "replay":
        statusDiv.innerText = msg.message;
        readyBtn.disabled = false;
        unreadyBtn.disabled = false;
        playAgainBtn.style.display = "none";
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

/**
 * Инициализация WebRTC-соединения через SimplePeer.
 */
function initPeerConnection(match_id) {
  navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    .then(stream => {
      localStream = stream;
      localVideo.srcObject = stream;
      updateOverlayCanvas();
      const isInitiator = (user_id === match_id.split("_")[0]);
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

/**
 * Возвращает жест противника из объекта жестов.
 */
function getOpponentGesture(gestures) {
  for (let key in gestures) {
    if (key !== user_id) return gestures[key];
  }
  return "none";
}

/**
 * Обработка кнопок готовности.
 */
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

/**
 * Функция запуска битвы.
 * Запускается обратный отсчёт и параллельно каждые 2 секунды запускается детекция жеста,
 * результат которой отображается (с рамкой) и сохраняется как finalGesture.
 */
function startBattle() {
  battleTimer = battleDuration;
  battleTimerDiv.innerText = `Битва: ${battleTimer} сек`;

  // Запускаем обратный отсчёт каждую секунду
  battleCountdownInterval = setInterval(() => {
    battleTimer--;
    battleTimerDiv.innerText = `Битва: ${battleTimer} сек`;
    if (battleTimer <= 0) {
      clearInterval(battleCountdownInterval);
      clearInterval(gestureScanInterval);
      // Выполняем финальную детекцию жеста и отправляем результат
      detectGesture().then((detection) => {
        finalGesture = detection.gesture;
        ws.send(JSON.stringify({ action: "gesture", gesture: finalGesture, user_id: user_id }));
      }).catch(err => {
        console.error("Ошибка финальной детекции:", err);
        ws.send(JSON.stringify({ action: "gesture", gesture: finalGesture, user_id: user_id }));
      });
    }
  }, 1000);

  // Каждые 2 секунды запускаем детекцию и отрисовку рамки
  gestureScanInterval = setInterval(async () => {
    try {
      const detection = await detectGesture();
      finalGesture = detection.gesture;
      drawBoundingBox(detection.bbox);
      console.log("Детекция:", detection);
    } catch (err) {
      console.error("Ошибка детекции:", err);
    }
  }, 2000);
}

/**
 * При нажатии кнопки "Войти в очередь".
 */
joinQueueBtn.addEventListener("click", () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    connectWebSocket();
  } else {
    ws.send(JSON.stringify({ action: "join", user_id: user_id }));
  }
});

/**
 * При нажатии кнопки "Сыграть ещё" отправляем запрос на повторную игру.
 */
playAgainBtn.addEventListener("click", () => {
  playAgainBtn.style.display = "none";
  ws.send(JSON.stringify({ action: "play_again", user_id: user_id }));
});
