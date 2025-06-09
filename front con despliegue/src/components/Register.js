import React, { useState } from 'react';

const Register = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [result, setResult] = useState('');
  

  const handleRegister = async () => {
    setError('');
    setResult('');

    try {
      const response = await fetch('https://users-service-production-6ca2.up.railway.app/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          username, 
          password, 
          first_name: firstName, 
          last_name: lastName, 
          email 
        }),
      });

      const data = await response.json();
      if (response.ok) {
        setResult('Registro exitoso.');
        setTimeout(() => {
          window.location.href = '/login';
        }, 2000);
      } else {
        setError('Error al registrarse: ' + (data.error || 'Desconocido'));
      }
    } catch (error) {
      setError('Error de conexión: ' + error);
    }
  };

  return (
    <div className="container">
      <h2>Registro de Usuario</h2>
      <div className="form-group">
        <label htmlFor="register-username">Usuario</label>
        <input
          type="text"
          id="register-username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Nombre de usuario"
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="register-password">Contraseña</label>
        <input
          type="password"
          id="register-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Contraseña"
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="register-first-name">Nombre</label>
        <input
          type="text"
          id="register-first-name"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          placeholder="Tu nombre"
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="register-last-name">Apellido</label>
        <input
          type="text"
          id="register-last-name"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          placeholder="Tu apellido"
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="register-email">Correo electrónico</label>
        <input
          type="email"
          id="register-email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="ejemplo@correo.com"
          required
        />
      </div>
      <button type="button" onClick={handleRegister}>
        Registrarse
      </button>
      {result && <div className="result">{result}</div>}
      {error && <div className="error">{error}</div>}
      <p>¿Ya tienes cuenta? <a href="/">Inicia sesión aquí</a>.</p>
    </div>
  );
};

export default Register;
