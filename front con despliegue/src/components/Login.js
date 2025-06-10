import React, { useState } from 'react';
import styles from './Login.module.css';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResult('');
    setLoading(true);

    try {
      // Asegúrate de usar el protocolo correcto (http o https)
      const response = await fetch('https://18.218.82.108.nip.io/login', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();
      
      if (response.ok) {
        // Guardar tokens y datos del usuario
        const accessToken = data.access_token;
        const refreshToken = data.refresh_token;
        const userId = data.user.user_id;
        const userData = data.user;
        
        // Guardar en cookies (considera usar localStorage para tokens)
        document.cookie = `user_id=${encodeURIComponent(userId)}; path=/; max-age=86400; secure; samesite=strict`;
        document.cookie = `access_token=${encodeURIComponent(accessToken)}; path=/; max-age=${data.expires_in}; secure; samesite=strict`;
        document.cookie = `refresh_token=${encodeURIComponent(refreshToken)}; path=/; max-age=604800; secure; samesite=strict`; // 7 días
        
        // También puedes guardar en localStorage si prefieres
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        localStorage.setItem('user_data', JSON.stringify(userData));
        
        setResult('Login exitoso. Redirigiendo...');
        
        // Redirigir después de un breve delay
        setTimeout(() => {
          window.location.href = '/chat';
        }, 1000);
        
      } else {
        // Manejo específico de errores del backend
        setError(data.error || 'Error desconocido al iniciar sesión');
      }
    } catch (error) {
      console.error('Error de conexión:', error);
      setError('Error de conexión. Verifica que el servidor esté funcionando.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.loginContainer}>
      <h2>Iniciar Sesión</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="login-username">Usuario</label>
          <input 
            type="text" 
            id="login-username" 
            value={username} 
            onChange={(e) => setUsername(e.target.value)} 
            placeholder="Nombre de usuario" 
            required 
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label htmlFor="login-password">Contraseña</label>
          <input 
            type="password" 
            id="login-password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            placeholder="Contraseña" 
            required 
            disabled={loading}
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
        </button>
      </form>
      {result && <div className="result" style={{color: 'green'}}>{result}</div>}
      {error && <div className="error" style={{color: 'red'}}>{error}</div>}
      <p>¿No tienes cuenta? <a href="/register">Regístrate aquí</a>.</p>
    </div>
  );
};

export default Login;
