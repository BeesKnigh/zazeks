document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
      alert('Пожалуйста, войдите в систему');
      window.location.href = 'login.html';
      return;
    }
  
    try {
      const response = await fetch('http://localhost:8000/user/leaderboard', {
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
        winsCell.textContent = user.wins;
  
        row.appendChild(photoCell);
        row.appendChild(usernameCell);
        row.appendChild(winsCell);
  
        tbody.appendChild(row);
      });
    } catch (error) {
      console.error(error);
      alert('Ошибка при загрузке лидерборда');
    }
  });
  