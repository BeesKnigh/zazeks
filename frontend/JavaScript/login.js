document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    let username = document.getElementById('username').value;
    let password = document.getElementById('password').value;
    // Здесь будет код для аутентификации пользователя
    console.log('Logging in:', username, password);
});
