const backendUrl = window.location.origin;

const token = localStorage.getItem('accessToken');
if (!token) {
  alert('Пожалуйста, войдите в систему');
  window.location.href = 'login.html';
}

const user_id = localStorage.getItem('user_id');
if (!user_id) {
  alert('Не найден user_id. Возможно, вы не залогинены.');
  window.location.href = 'login.html';
}

// Объект для маппинга жестов с английского на русский
const gestureMapping = {
  "Rock": "Камень",
  "Paper": "Бумага",
  "Scissors": "Ножницы"
};

// Получаем элементы страницы
const video = document.getElementById('video');
const captureCanvas = document.getElementById('capture-canvas');
const captureCtx = captureCanvas.getContext('2d');
const overlayCanvas = document.getElementById('overlay-canvas');
const overlayCtx = overlayCanvas.getContext('2d');
const winnerDisplay = document.getElementById('winner');
const timerDisplay = document.getElementById('timer');
const playButton = document.getElementById('play-button');
const computerImg = document.getElementById('computer-img');

// Запуск видеопотока с камеры
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    video.srcObject = stream;
  })
  .catch(err => {
    console.error("Ошибка доступа к камере:", err);
    alert("Невозможно получить доступ к камере.");
  });

// Функция для захвата кадра и отправки его на сервер для детекции
// Ожидаем, что сервер вернет объект вида: { gesture: "Rock", bbox: [x1, y1, x2, y2] }
async function detectGesture() {
  captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);

  return new Promise((resolve, reject) => {
    captureCanvas.toBlob(async (blob) => {
      if (!blob) {
        reject("Ошибка преобразования кадра в Blob");
        return;
      }
      const formData = new FormData();
      formData.append('file', blob, 'frame.jpg');

      try {
        const response = await fetch(`${backendUrl}/model/detect`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        });

        if (!response.ok) {
          throw new Error(`Ошибка детекции: ${response.status}`);
        }
        const data = await response.json();
        // data: { gesture: "Rock", bbox: [x1, y1, x2, y2] }
        resolve(data);
      } catch (error) {
        console.error(error);
        reject(error);
      }
    }, 'image/jpeg');
  });
}

// Функция для определения результата игры
function determineResult(userGesture, computerGesture) {
  if (userGesture === computerGesture) return 'Ничья';
  if (
    (userGesture === 'Rock' && computerGesture === 'Scissors') ||
    (userGesture === 'Scissors' && computerGesture === 'Paper') ||
    (userGesture === 'Paper' && computerGesture === 'Rock')
  ) {
    return 'Победа';
  }
  return 'Поражение';
}

// Функция для генерации случайного выбора компьютера
function getRandomComputerGesture() {
  const gestures = ['Rock', 'Paper', 'Scissors'];
  return gestures[Math.floor(Math.random() * gestures.length)];
}

// Обновление таймера на экране
function updateTimer(seconds) {
  const min = String(Math.floor(seconds / 60)).padStart(2, '0');
  const sec = String(seconds % 60).padStart(2, '0');
  timerDisplay.innerText = `Таймер: ${min}:${sec}`;
}

function clearOverlay() {
  overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
}

function drawOverlay(bbox) {
  clearOverlay();
  if (bbox && bbox.length === 4) {
    const [x1, y1, x2, y2] = bbox;
    overlayCtx.strokeStyle = "red";
    overlayCtx.lineWidth = 2;
    overlayCtx.strokeRect(x1, y1, x2 - x1, y2 - y1);
  }
}

// Функция для завершения раунда: генерирует выбор компьютера, определяет результат,
// выводит его, отправляет на сервер и обновляет окно компьютера картинкой.
async function finishRound(finalUserGesture) {
  const computerGesture = getRandomComputerGesture();

  // Выбираем картинку для компьютера в зависимости от его жеста
  let computerImageSrc = '/images/placeholder.png';
  if (computerGesture === 'Rock') {
    computerImageSrc = '/images/rock.png';
  } else if (computerGesture === 'Paper') {
    computerImageSrc = '/images/paper.png';
  } else if (computerGesture === 'Scissors') {
    computerImageSrc = '/images/scissors.png';
  }
  computerImg.src = computerImageSrc;

  const result = determineResult(finalUserGesture, computerGesture);

  const finalUserGestureRu = gestureMapping[finalUserGesture] || finalUserGesture;
  const computerGestureRu = gestureMapping[computerGesture] || computerGesture;

  winnerDisplay.innerText = `Победитель: ${result.toUpperCase()} (Ваш: ${finalUserGestureRu}, Компьютера: ${computerGestureRu})`;

  // Отправляем результат игры на сервер
  try {
    const gameResponse = await fetch(`${backendUrl}/game/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        user_choice: finalUserGesture.toLowerCase(),
        computer_choice: computerGesture.toLowerCase(),
        result: result
      })
    });
    if (!gameResponse.ok) {
      console.error("Ошибка при сохранении игры");
    } else {
      const gameData = await gameResponse.json();
      console.log("Игра сохранена:", gameData);
    }
  } catch (error) {
    console.error("Ошибка при отправке результатов игры:", error);
  }

  setTimeout(clearOverlay, 1000);
}

function startGame() {
  let countdown = 5;
  updateTimer(countdown);
  clearOverlay();
  winnerDisplay.innerText = "";
  computerImg.src = '/images/placeholder.png';

  let finalUserGesture = null;
  const countdownInterval = setInterval(async () => {
    try {
      const detection = await detectGesture();
      finalUserGesture = detection.gesture;
      drawOverlay(detection.bbox);
      countdown--;
      updateTimer(countdown);
      if (countdown <= 0) {
        clearInterval(countdownInterval);
        finishRound(finalUserGesture);
      }
    } catch (err) {
      console.error("Ошибка в процессе детекции:", err);
    }
  }, 1000);
}

playButton.addEventListener('click', startGame);
