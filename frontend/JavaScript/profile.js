// Функция для предварительного отображения фото профиля
function previewProfilePic(event) {
    const file = event.target.files[0];
    const reader = new FileReader();

    reader.onload = function(e) {
        // Изменяем изображение на выбранное
        document.getElementById('profile-pic').src = e.target.result;
    }

    if (file) {
        reader.readAsDataURL(file);
    }
}

// Загрузка никнейма из localStorage
window.onload = function() {
    const user = JSON.parse(localStorage.getItem('user'));

    // Если пользователь не найден в localStorage, перенаправляем на страницу входа
    if (!user) {
        window.location.href = "login.html";
    } else {
        document.getElementById('nickname').innerText = "Ваш Никнейм: " + user.login;
    }
}

// Функция изменения никнейма
function editNickname() {
    document.getElementById('nickname-input-container').style.display = 'block';
}

// Функция подтверждения изменения никнейма
function changeNickname() {
    const newNickname = document.getElementById('new-nickname').value;

    if (newNickname) {
        const user = JSON.parse(localStorage.getItem('user'));
        user.login = newNickname;
        localStorage.setItem('user', JSON.stringify(user));

        // Обновляем отображаемый никнейм
        document.getElementById('nickname').innerText = "Ваш Никнейм: " + newNickname;

        // Закрываем поле ввода
        document.getElementById('nickname-input-container').style.display = 'none';
    }
}
