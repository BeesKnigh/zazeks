// Получаем форму и кнопку
const registerForm = document.getElementById('register-form');
const registerBtn = document.getElementById('register-btn');

// Вешаем обработчик на отправку формы
registerForm.addEventListener('submit', async (event) => {
  event.preventDefault(); // отменяем стандартное поведение (перезагрузку)

  // Собираем данные формы
  const username = document.getElementById('login').value;
  const password = document.getElementById('password').value;

  // Формируем объект с теми же полями, что ожидает бэкенд
  const bodyData = {
    username, 
    password
  };

  try {
    const response = await fetch('http://localhost:8000/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(bodyData)
    });

    if (!response.ok) {
      // Если ответ HTTP не 2xx, выбросим ошибку
      const errorData = await response.json();
      alert(`Ошибка регистрации: ${errorData.detail || response.statusText}`);
      return;
    }

    // Парсим ответ — например, {"msg":"User registered successfully","user_id":3}
    const data = await response.json();
    console.log('Registration success:', data);

    alert('Регистрация прошла успешно!');

    // Можно сразу перенаправить на страницу логина:
    window.location.href = 'login.html';

  } catch (err) {
    console.error('Fetch error:', err);
    alert('Ошибка при попытке регистрации');
  }
});
