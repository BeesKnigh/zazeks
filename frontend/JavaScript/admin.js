// Пример взаимодействия с API для загрузки пользователей и вызова операций
document.addEventListener("DOMContentLoaded", () => {
    const usersTableBody = document.querySelector("#users-table tbody");
    const refreshBtn = document.getElementById("refresh-btn");
    const modal = document.getElementById("modal");
    const closeModal = document.getElementById("close-modal");
    const confirmUsernameBtn = document.getElementById("confirm-username");
    const newUsernameInput = document.getElementById("new-username");
    let selectedUserId = null; // ID пользователя для изменения никнейма
  
    // Загрузка списка пользователей
    async function loadUsers() {
      // Замените URL на актуальный эндпоинт для получения списка пользователей
      try {
        const response = await fetch("/api/users"); // пример запроса
        const users = await response.json();
        usersTableBody.innerHTML = "";
        users.forEach(user => {
          const row = document.createElement("tr");
          row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td><img src="${user.photo || '/images/default-avatar.jpg'}" alt="Avatar" style="width:40px; height:40px; border-radius:50%;"></td>
            <td>${user.wins}</td>
            <td>
              <button class="action-btn delete-btn" data-id="${user.id}">Удалить</button>
              <button class="action-btn add-admin-btn" data-id="${user.id}">Сделать админом</button>
              <button class="action-btn delete-photo-btn" data-id="${user.id}">Удалить фото</button>
              <button class="action-btn change-name-btn" data-id="${user.id}">Изменить ник</button>
            </td>
          `;
          usersTableBody.appendChild(row);
        });
        addEventListeners();
      } catch (err) {
        console.error("Ошибка загрузки пользователей", err);
      }
    }
  
    refreshBtn.addEventListener("click", loadUsers);
  
    // Назначение слушателей для кнопок действий
    function addEventListeners() {
      document.querySelectorAll(".delete-btn").forEach(btn => {
        btn.addEventListener("click", async (e) => {
          const userId = e.target.dataset.id;
          if (confirm("Удалить пользователя?")) {
            await fetch(`/admin/users/${userId}`, {
              method: "DELETE",
              headers: {
                "Authorization": "Bearer " + localStorage.getItem("access_token")
              }
            });
            loadUsers();
          }
        });
      });
  
      document.querySelectorAll(".add-admin-btn").forEach(btn => {
        btn.addEventListener("click", async (e) => {
          const userId = e.target.dataset.id;
          if (confirm("Назначить этого пользователя администратором?")) {
            await fetch(`/admin/admins`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + localStorage.getItem("access_token")
              },
              body: JSON.stringify({ user_id: parseInt(userId) })
            });
            loadUsers();
          }
        });
      });
  
      document.querySelectorAll(".delete-photo-btn").forEach(btn => {
        btn.addEventListener("click", async (e) => {
          const userId = e.target.dataset.id;
          if (confirm("Удалить фото пользователя?")) {
            await fetch(`/admin/users/${userId}/photo`, {
              method: "DELETE",
              headers: {
                "Authorization": "Bearer " + localStorage.getItem("access_token")
              }
            });
            loadUsers();
          }
        });
      });
  
      document.querySelectorAll(".change-name-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
          selectedUserId = e.target.dataset.id;
          newUsernameInput.value = "";
          modal.style.display = "block";
        });
      });
    }
  
    // Обработка закрытия модального окна
    closeModal.addEventListener("click", () => {
      modal.style.display = "none";
    });
  
    // Подтверждение изменения никнейма
    confirmUsernameBtn.addEventListener("click", async () => {
      if (newUsernameInput.value.trim() && selectedUserId) {
        await fetch(`/admin/users/${selectedUserId}/username?new_username=${encodeURIComponent(newUsernameInput.value.trim())}`, {
          method: "PUT",
          headers: {
            "Authorization": "Bearer " + localStorage.getItem("access_token")
          }
        });
        modal.style.display = "none";
        loadUsers();
      }
    });
  
    // Начальная загрузка пользователей
    loadUsers();
  });
  