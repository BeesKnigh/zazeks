// Получаем форму и кнопку регистрации
const registerForm = document.getElementById('register-form');
const registerBtn = document.getElementById('register-btn');

const backendUrl = window.location.origin;

// Вешаем обработчик на отправку формы
registerForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  // Собираем данные формы
  const username = document.getElementById('login').value;
  const password = document.getElementById('password').value;

  // Формируем объект с теми же полями, что ожидает бэкенд
  const bodyData = { username, password };

  try {
    const response = await fetch(`${backendUrl}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyData)
    });

    if (!response.ok) {
      // Если ответ HTTP не в диапазоне 2xx, выбрасываем ошибку
      const errorData = await response.json();
      alert(`Ошибка регистрации: ${errorData.detail || response.statusText}`);
      return;
    }

    // Парсим ответ, например: {"msg":"User registered successfully","user_id":3}
    const data = await response.json();
    console.log('Регистрация успешна:', data);

    alert('Регистрация прошла успешно!');

    // Перенаправляем на страницу входа
    window.location.href = 'login.html';

  } catch (err) {
    console.error('Ошибка при выполнении запроса:', err);
    alert('Ошибка при попытке регистрации');
  }
});
