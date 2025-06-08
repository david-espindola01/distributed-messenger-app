import React, { useEffect, useState } from 'react'; // Asegúrate de importar useEffect y useState
import { BrowserRouter as Router, Route, Routes, useNavigate } from 'react-router-dom';
import Chat from './components/Chat';
import Login from './components/Login';
import Register from './components/Register';

function Welcome() {
    const navigate = useNavigate();
    const [showMessage, setShowMessage] = useState(true);
    const [isHidden, setIsHidden] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setIsHidden(true); // Inicia la animación de ocultar
            setTimeout(() => {
                setShowMessage(false);
                navigate('/login'); // Redirige a la página de inicio de sesión
            }, 1000); // Espera a que la animación termine
        }, 2000); // Espera 3 segundos antes de iniciar la animación

        return () => clearTimeout(timer); // Limpia el temporizador al desmontar
    }, [navigate]);

    return (
        <div>
            {showMessage && (
                <h1 className={`welcome-message ${isHidden ? 'hidden' : ''}`}>
                    Bienvenido a UPTC Messenger
                </h1>
            )}
        </div>
    );
}

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/" element={<Welcome />} />
            </Routes>
        </Router>
    );
}

export default App;
