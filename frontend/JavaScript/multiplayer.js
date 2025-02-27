const user_id = localStorage.getItem('user_id');
const token = localStorage.getItem('accessToken');

if (!user_id || !token) {
  alert("Необходимо войти в систему");
  window.location.href = "login.html";
}

const joinQueueBtn = document.getElementById("joinQueue");
const readyBtn = document.getElementById("readyBtn");
const unreadyBtn = document.getElementById("unreadyBtn");
const statusDiv = document.getElementById("status");
const battleTimerDiv = document.getElementById("battleTimer");
const resultDiv = document.getElementById("result");

const localVideo = document.getElementById("localVideo");
const remoteVideo = document.getElementById("remoteVideo");
const blackoutOverlay = document.getElementById("blackoutOverlay");

let ws;
let peer;
let localStream;
let battleCountdownInterval;
let battleDuration = 10; // секунд
let battleTimer = battleDuration;
let finalGesture = null; // итоговый жест, полученный после детекции

// Функция-«заглушка» для детекции жеста (замените её на реальную модель)
function detectGesture() {
  const gestures = ["Rock", "Paper", "Scissors"];
  return gestures[Math.floor(Math.random() * gestures.length)];
}

// Устанавливаем WebSocket-соединение для сигналинга и управления битвой
function connectWebSocket() {
  ws = new WebSocket("ws://localhost:8000/ws/multiplayer");
  
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
        // Инициализируем WebRTC-соединение
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
        break;
      case "player_unready":
        statusDiv.innerText = "Один из игроков отменил готовность.";
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

// Функция для инициализации WebRTC-соединения с помощью SimplePeer
function initPeerConnection(match_id) {
  navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    .then(stream => {
      localStream = stream;
      localVideo.srcObject = stream;
      // Определяем инициатора (например, первый ID в match_id)
      const isInitiator = (user_id === match_id.split("_")[0]);
      peer = new SimplePeer({
        initiator: isInitiator,
        trickle: false,
        stream: localStream
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

// Возвращает жест противника из объекта жестов
function getOpponentGesture(gestures) {
  for (let key in gestures) {
    if (key !== user_id) return gestures[key];
  }
  return "none";
}

// Обработка кнопок готовности
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

// Функция запуска битвы: стартует отсчет и выполняется детекция жеста
function startBattle() {
  battleTimer = battleDuration;
  battleTimerDiv.innerText = `Битва: ${battleTimer} сек`;
  battleCountdownInterval = setInterval(() => {
    battleTimer--;
    battleTimerDiv.innerText = `Битва: ${battleTimer} сек`;
    if (battleTimer <= 0) {
      clearInterval(battleCountdownInterval);
      // Выполняем детекцию финального жеста (в реальном варианте здесь вызов модели)
      finalGesture = detectGesture();
      // Отправляем результат через WebSocket
      ws.send(JSON.stringify({ action: "gesture", gesture: finalGesture, user_id: user_id }));
    }
  }, 1000);
}

// При загрузке страницы устанавливаем соединение
connectWebSocket();

// При нажатии кнопки "Войти в очередь"
joinQueueBtn.addEventListener("click", () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    connectWebSocket();
  } else {
    ws.send(JSON.stringify({ action: "join", user_id: user_id }));
  }
});
