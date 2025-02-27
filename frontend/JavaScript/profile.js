window.onload = function() {
    // Simulate fetching user data from the server
    let user = {
        username: 'Player1',
        email: 'player1@example.com'
    };
    document.getElementById('profileInfo').innerHTML = `
        <p>Username: ${user.username}</p>
        <p>Email: ${user.email}</p>
    `;
};

function logout() {
    // Handle logout functionality here
    console.log('Logged out');
}
