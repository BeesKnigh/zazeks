// Пример таймера, который будет работать
let timer = 0;
let timerInterval;
let winner = "";

// Функция для обновления таймера
function updateTimer() {
    let minutes = Math.floor(timer / 60);
    let seconds = timer % 60;
    document.getElementById('timer').innerText = `Таймер: ${pad(minutes)}:${pad(seconds)}`;
    timer++;
}

// Функция для добавления ведущего нуля
function pad(num) {
    return num < 10 ? "0" + num : num;
}

// Функция для обновления победителя
function setWinner(name) {
    winner = name;
    document.getElementById('winner').innerText = `Победитель: ${winner}`;
}

// Запуск таймера при старте игры
timerInterval = setInterval(updateTimer, 1000);

// Пример установки победителя через 30 секунд
setTimeout(() => {
    setWinner("Пользователь");
}, 30000);
