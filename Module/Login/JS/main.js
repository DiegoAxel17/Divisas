document.getElementById("loginForm").addEventListener("submit", function (e) {
  e.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();
  const message = document.getElementById("message");

  const validUser = "admin";
  const validPass = "1234";

  if (username === validUser && password === validPass) {
    message.style.color = "#00ff9d";
    message.textContent = "¡Inicio de sesión exitoso!";
  } else {
    message.style.color = "#ff6b6b";
    message.textContent = "Usuario o contraseña incorrectos.";
  }
});


