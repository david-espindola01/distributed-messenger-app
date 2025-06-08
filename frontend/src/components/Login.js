import React, { useState } from 'react';
import styles from './Login.module.css';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [result, setResult] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResult('');

    try {
      const response = await fetch('http://localhost:5001/login', { // Cambia la URL según tu configuración
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();
      if (response.ok) {
        const userId = data.id || data.user_id;
        document.cookie = `user_id=${encodeURIComponent(userId)}; path=/; max-age=86400`;
        document.cookie = "auth_token=valid; path=/; max-age=86400";
        window.location.href = '/chat';
      } else {
        setError('Error al iniciar sesión: ' + (data.error || 'Desconocido'));
      }
    } catch (error) {
      setError('Error de conexión: ' + error);
    }
  };

  return (
    <div className={styles.loginContainer}>
      <h2>Iniciar Sesión</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="login-username">Usuario</label>
          <input type="text" id="login-username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Nombre de usuario" required />
        </div>
        <div className="form-group">
          <label htmlFor="login-password">Contraseña</label>
          <input type="password" id="login-password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Contraseña" required />
        </div>
        <button type="submit">Iniciar Sesión</button>
      </form>
      {result && <div className="result">{result}</div>}
      {error && <div className="error">{error}</div>}
      <p>¿No tienes cuenta? <a href="/register">Regístrate aquí</a>.</p>
    </div>
  );
};

export default Login;
