document.addEventListener('DOMContentLoaded', () => {
  const backendUrl = window.location.origin;
  const token = localStorage.getItem('accessToken');
  if (!token) {
    alert("Необходима авторизация");
    window.location.href = 'login.html';
    return;
  }

  // Универсальная функция для обработки ответов
  async function handleResponse(response) {
    const data = await response.json();
    if (response.ok) {
      alert(data.msg);
    } else {
      alert(data.detail || "Произошла ошибка");
    }
  }

  // Удаление пользователя
  document.getElementById('delete-user-btn').addEventListener('click', async () => {
    const userId = document.getElementById('delete-user-id').value;
    if (!userId) {
      alert("Введите ID пользователя");
      return;
    }
    try {
      const response = await fetch(`${backendUrl}/admin/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      handleResponse(response);
    } catch (err) {
      console.error(err);
      alert("Ошибка при выполнении запроса");
    }
  });

  // Добавление админа (с JSON телом запроса)
  document.getElementById('add-admin-btn').addEventListener('click', async () => {
    const userId = document.getElementById('add-admin-id').value;
    if (!userId) {
      alert("Введите ID пользователя");
      return;
    }
    try {
      const response = await fetch(`${backendUrl}/admin/admins`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: parseInt(userId) })
      });
      handleResponse(response);
    } catch (err) {
      console.error(err);
      alert("Ошибка при выполнении запроса");
    }
  });

  // Удаление админа
  document.getElementById('delete-admin-btn').addEventListener('click', async () => {
    const userId = document.getElementById('delete-admin-id').value;
    if (!userId) {
      alert("Введите ID пользователя");
      return;
    }
    try {
      const response = await fetch(`${backendUrl}/admin/admins/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      handleResponse(response);
    } catch (err) {
      console.error(err);
      alert("Ошибка при выполнении запроса");
    }
  });

  // Удаление игры
  document.getElementById('delete-game-btn').addEventListener('click', async () => {
    const gameId = document.getElementById('delete-game-id').value;
    if (!gameId) {
      alert("Введите ID игры");
      return;
    }
    try {
      const response = await fetch(`${backendUrl}/admin/games/${gameId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      handleResponse(response);
    } catch (err) {
      console.error(err);
      alert("Ошибка при выполнении запроса");
    }
  });

  // Удаление фото пользователя
  document.getElementById('delete-photo-btn').addEventListener('click', async () => {
    const userId = document.getElementById('delete-photo-user-id').value;
    if (!userId) {
      alert("Введите ID пользователя");
      return;
    }
    try {
      const response = await fetch(`${backendUrl}/admin/users/${userId}/photo`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      handleResponse(response);
    } catch (err) {
      console.error(err);
      alert("Ошибка при выполнении запроса");
    }
  });

  // Смена никнейма пользователя
  document.getElementById('change-username-btn').addEventListener('click', async () => {
    const userId = document.getElementById('change-username-user-id').value;
    const newUsername = document.getElementById('new-username').value;
    if (!userId || !newUsername) {
      alert("Введите ID пользователя и новый никнейм");
      return;
    }
    try {
      const response = await fetch(`${backendUrl}/admin/users/${userId}/username`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ new_username: newUsername })
      });
      handleResponse(response);
    } catch (err) {
      console.error(err);
      alert("Ошибка при выполнении запроса");
    }
  });

  // Выход из админ панели
  document.getElementById('logout-btn').addEventListener('click', () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user_id');
    window.location.href = 'login.html';
  });
});
