document.addEventListener('DOMContentLoaded', () => {
  const token = localStorage.getItem('accessToken');
  if (!token) {
    alert('Пожалуйста, войдите в систему');
    window.location.href = 'login.html';
    return;
  }

  const offlineBtn = document.getElementById('offline-btn');
  const onlineBtn = document.getElementById('online-btn');

  // Функция для загрузки лидерборда с нужным эндпоинтом
  async function loadLeaderboard(type) {
    try {
      const backendUrl = window.location.origin;
      const response = await fetch(`${backendUrl}/user/leaderboard/${type}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error('Ошибка получения лидерборда');
      }
      const leaderboard = await response.json();
      const tbody = document.querySelector('#leaderboard-table tbody');
      tbody.innerHTML = '';

      leaderboard.forEach(user => {
        const row = document.createElement('tr');

        const photoCell = document.createElement('td');
        const img = document.createElement('img');
        img.src = user.photo ? user.photo : '../images/placeholder.png';
        photoCell.appendChild(img);

        const usernameCell = document.createElement('td');
        usernameCell.textContent = user.username;

        const winsCell = document.createElement('td');
        winsCell.textContent = type === 'offline' ? user.wins : user.online_wins;

        row.appendChild(photoCell);
        row.appendChild(usernameCell);
        row.appendChild(winsCell);

        tbody.appendChild(row);
      });
    } catch (error) {
      console.error(error);
      alert('Ошибка при загрузке лидерборда');
    }
  }

  loadLeaderboard('offline');

  offlineBtn.addEventListener('click', () => {
    offlineBtn.classList.add('active');
    onlineBtn.classList.remove('active');
    loadLeaderboard('offline');
  });

  onlineBtn.addEventListener('click', () => {
    onlineBtn.classList.add('active');
    offlineBtn.classList.remove('active');
    loadLeaderboard('online');
  });
});
