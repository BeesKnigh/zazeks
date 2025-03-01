document.addEventListener('DOMContentLoaded', async () => {
  const backendUrl = window.location.origin;

  const token = localStorage.getItem('accessToken');
  if (!token) {
    alert('Пожалуйста, войдите в систему');
    window.location.href = 'login.html';
    return;
  }

  const user_id = localStorage.getItem('user_id');
  if (!user_id) {
    alert('Не найден user_id. Возможно, вы не залогинены.');
    window.location.href = 'login.html';
    return;
  }

  try {
    const response = await fetch(`${backendUrl}/user/${user_id}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      if (response.status === 401) {
        alert('Время сессии истекло. Пожалуйста, войдите снова.');
        window.location.href = 'login.html';
        return;
      }
      throw new Error('Ошибка при получении профиля');
    }

    const userData = await response.json();
    console.log('Профиль пользователя:', userData);

    document.getElementById('nickname').innerText = userData.username;
    if (userData.photo) {
      document.getElementById('profile-pic').src = userData.photo;
    }
    document.getElementById('wins').innerText = userData.wins;
    document.getElementById('games-played').innerText = userData.games_played;

  } catch (err) {
    console.error(err);
    alert('Не удалось загрузить профиль');
    window.location.href = 'login.html';
    return;
  }

  const editNicknameBtn = document.getElementById('edit-nickname-btn');
  const nicknameInputContainer = document.getElementById('nickname-input-container');
  const confirmNicknameBtn = document.getElementById('confirm-nickname-btn');
  const newNicknameInput = document.getElementById('new-nickname');

  editNicknameBtn.addEventListener('click', () => {
    nicknameInputContainer.style.display = 'block';
  });

  confirmNicknameBtn.addEventListener('click', async () => {
    const newNickname = newNicknameInput.value;
    if (!newNickname.trim()) {
      alert('Введите никнейм');
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/user/${user_id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username: newNickname })
      });

      if (!response.ok) {
        throw new Error('Ошибка при обновлении никнейма');
      }

      const data = await response.json();
      console.log('Никнейм обновлён:', data);

      document.getElementById('nickname').innerText = newNickname;
      nicknameInputContainer.style.display = 'none';
      newNicknameInput.value = '';

    } catch (err) {
      console.error(err);
      alert('Ошибка при обновлении никнейма');
    }
  });

  const changePhotoBtn = document.getElementById('change-photo-btn');
  const profilePicInput = document.getElementById('profile-pic-input');
  const profilePic = document.getElementById('profile-pic');

  changePhotoBtn.addEventListener('click', () => {
    profilePicInput.click();
  });

  profilePicInput.addEventListener('change', async () => {
    const file = profilePicInput.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      const base64URL = e.target.result; // data:image/png;base64,....
      console.log('Изображение в base64:', base64URL);

      try {
        const response = await fetch(`${backendUrl}/user/${user_id}`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ photo: base64URL })
        });

        if (!response.ok) {
          throw new Error('Ошибка при обновлении фото');
        }

        const data = await response.json();
        console.log('Фото обновлено:', data);

        profilePic.src = base64URL;

      } catch (err) {
        console.error(err);
        alert('Ошибка при обновлении фото');
      }
    };
    reader.readAsDataURL(file);
  });
});
