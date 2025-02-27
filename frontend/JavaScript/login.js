// Получаем форму входа
const loginForm = document.getElementById('login-form');

// Обработчик отправки формы
loginForm.addEventListener('submit', function (e) {
    e.preventDefault(); // Отменяем стандартное поведение формы

    // Получаем данные с формы
    const login = document.getElementById('login').value;
    const password = document.getElementById('password').value;

    // Получаем данные пользователя из localStorage
    const storedUser = JSON.parse(localStorage.getItem('user'));

    // Проверяем, совпадают ли логин и пароль
    if (storedUser && storedUser.login === login && storedUser.password === password) {
        // Если данные правильные, перенаправляем на страницу профиля
        window.location.href = "profile.html";
    } else {
        // Если данные неверные, выводим ошибку
        alert("Неверный логин или пароль.");
    }
});
