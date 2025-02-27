// login.js
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
    const response = await fetch('http://localhost:8000/auth/login', {
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
    console.log('Login success:', data);
    // Тут важно: сохраняем и access_token, и user_id
    localStorage.setItem('accessToken', data.access_token);
    localStorage.setItem('user_id', data.user_id);

    alert('Вход успешный!');
    window.location.href = 'profile.html';

  } catch (err) {
    console.error('Fetch error:', err);
    alert('Ошибка при попытке входа');
  }
});
