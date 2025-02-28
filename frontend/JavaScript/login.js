const backendUrl = window.location.origin;
const loginForm = document.getElementById('login-form');

loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const username = document.getElementById('login').value;
  const password = document.getElementById('password').value;

  const bodyData = {
    username,
    password
  };

  try {
    const response = await fetch(`${backendUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyData)
    });

    if (!response.ok) {
      const errorData = await response.json();
      alert(`Ошибка входа: ${errorData.detail || response.statusText}`);
      return;
    }

    const data = await response.json();
    console.log('Успешный вход:', data);
    localStorage.setItem('accessToken', data.access_token);
    localStorage.setItem('user_id', data.user_id);

    alert('Вход успешный!');
    window.location.href = 'profile.html';

  } catch (err) {
    console.error('Ошибка при выполнении запроса:', err);
    alert('Ошибка при попытке входа');
  }
});
