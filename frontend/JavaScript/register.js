// Получаем форму регистрации
const registerForm = document.getElementById('register-form');

// Обработчик отправки формы
registerForm.addEventListener('submit', function (e) {
    e.preventDefault(); // Отменяем стандартное поведение формы

    // Получаем данные с формы
    const login = document.getElementById('login').value;
    const password = document.getElementById('password').value;

    // Проверяем, если логин и пароль не пустые
    if (login && password) {
        // Сохраняем данные в localStorage (или в backend через API)
        localStorage.setItem('user', JSON.stringify({ login, password }));

        // Перенаправляем на страницу входа
        window.location.href = "login.html";
    } else {
        alert("Пожалуйста, заполните все поля.");
    }
});
