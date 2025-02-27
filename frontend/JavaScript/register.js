document.getElementById('registerForm').addEventListener('submit', function(e) {
    e.preventDefault();
    let username = document.getElementById('username').value;
    let password = document.getElementById('password').value;
    // Здесь будет код для отправки данных на сервер
    console.log('Registering:', username, password);
});
