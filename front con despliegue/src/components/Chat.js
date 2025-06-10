// src/components/Chat.js
import React, { useEffect, useState, useCallback, useRef } from 'react';
import styles from './Chat.module.css';

const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
};

const Chat = () => {
    const [chats, setChats] = useState([]);
    const [currentChatId, setCurrentChatId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [messageInput, setMessageInput] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [users, setUsers] = useState([]);
    const [selectedUsers, setSelectedUsers] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    
    const userId = getCookie('user_id');
    const socketRef = useRef(null);
    const chatMessagesRef = useRef(null);
    const lastMessageRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    
    // Refs para controlar la reconexión
    const reconnectAttemptsRef = useRef(0);
    const maxReconnectAttempts = 5;
    const isManualDisconnectRef = useRef(false);
    
    // Ref para mantener el currentChatId actualizado en el WebSocket
    const currentChatIdRef = useRef(currentChatId);

    // Actualizar el ref cada vez que cambie currentChatId
    useEffect(() => {
        currentChatIdRef.current = currentChatId;
        console.log('currentChatIdRef actualizado a:', currentChatId);
    }, [currentChatId]);

    // Efecto para desplazamiento automático al final de los mensajes
    useEffect(() => {
        if (chatMessagesRef.current) {
            chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
        }
        
        if (lastMessageRef.current) {
            lastMessageRef.current.animate(
                [
                    { transform: 'translateY(10px)', opacity: 0 },
                    { transform: 'translateY(0)', opacity: 1 }
                ],
                {
                    duration: 300,
                    easing: 'ease-out'
                }
            );
        }
    }, [messages]);

    // Función para obtener nombre de usuario
    const getUserName = useCallback((userId) => {
        const user = users.find(u => String(u.id || u.user_id) === String(userId));
        return user ? `${user.first_name} ${user.last_name}` : `Usuario ${userId}`;
    }, [users]);

    // Crear loadChats primero para evitar problemas de dependencias
    const loadChats = useCallback(async () => {
        try {
            console.log('Cargando chats...');
            setIsLoading(true);
            const res = await fetch(`https://chats-service-production.up.railway.app/users/${userId}/chats`);
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            const data = await res.json();
            console.log('Chats cargados:', data);
            setChats(data.chats || []);
            setIsLoading(false);
        } catch (err) {
            console.error("Error loading chats:", err);
            setIsLoading(false);
        }
    }, [userId]);

    // Función para conectar WebSocket - CORREGIDA
    const connectWebSocket = useCallback(() => {
        if (!userId) return;
        
        // Limpiar timeout anterior si existe
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }

        // Cerrar conexión existente si la hay
        if (socketRef.current) {
            socketRef.current.close();
        }

        console.log('Conectando WebSocket...');
        socketRef.current = new WebSocket(`wss://polar-eyrie-72327-acedb53a74a0.herokuapp.com/ws?user_id=${userId}`);
        
        socketRef.current.onopen = () => {
            console.log("WebSocket connection established");
            setIsConnected(true);
            reconnectAttemptsRef.current = 0;
            
            // Enviar ping periódico para mantener la conexión
            const pingInterval = setInterval(() => {
                if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                    socketRef.current.send('ping');
                } else {
                    clearInterval(pingInterval);
                }
            }, 30000);
        };
        
        socketRef.current.onmessage = (event) => {
            try {
                console.log('Mensaje WebSocket recibido (raw):', event.data);
                
                if (event.data === 'pong') {
                    console.log('Pong recibido del servidor');
                    return;
                }

                const messageData = JSON.parse(event.data);
                console.log('Mensaje WebSocket parseado:', messageData);
                console.log('Chat actual desde ref:', currentChatIdRef.current);
                
                // Manejar pings del servidor
                if (messageData.type === 'ping') {
                    console.log('Ping del servidor recibido, enviando pong...');
                    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                        socketRef.current.send(JSON.stringify({type: 'pong', timestamp: Date.now()}));
                    }
                    return;
                }

                // AGREGAR MENSAJE SIEMPRE si es para el chat actual
                if (currentChatIdRef.current && String(messageData.chat_id) === String(currentChatIdRef.current)) {
                    console.log('✅ Agregando mensaje para chat actual:', messageData);
                    setMessages(prev => {
                        console.log('📝 Mensajes anteriores:', prev.length);
                        const newMessages = [...prev, messageData];
                        console.log('📝 Mensajes después de agregar:', newMessages.length);
                        return newMessages;
                    });
                } else {
                    console.log('❌ Mensaje no es para el chat actual');
                    console.log('   - currentChatIdRef.current:', currentChatIdRef.current);
                    console.log('   - messageData.chat_id:', messageData.chat_id);
                    console.log('   - Comparación String:', String(messageData.chat_id), '===', String(currentChatIdRef.current));
                }
                
                // Siempre actualizar la lista de chats para mostrar último mensaje
                console.log('Actualizando lista de chats...');
                loadChats();
                
            } catch (error) {
                console.error('❌ Error parsing WebSocket message:', error);
                console.error('   - Mensaje original:', event.data);
            }
        };

        socketRef.current.onerror = (error) => {
            console.error("❌ WebSocket error:", error);
            setIsConnected(false);
        };

        socketRef.current.onclose = (event) => {
            console.log("WebSocket closed:", event.code, event.reason);
            setIsConnected(false);
            
            // Solo reconectar si no fue un cierre manual y no hemos excedido el máximo de intentos
            if (!isManualDisconnectRef.current && 
                reconnectAttemptsRef.current < maxReconnectAttempts && 
                userId && 
                event.code !== 1000) {
                
                reconnectAttemptsRef.current++;
                const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
                
                console.log(`Reconectando WebSocket en ${delay}ms (intento ${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
                reconnectTimeoutRef.current = setTimeout(() => {
                    connectWebSocket();
                }, delay);
            } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
                console.log('Máximo número de intentos de reconexión alcanzado');
            }
        };
    }, [userId, loadChats]);

    // Inicializar WebSocket y cargar usuarios
    useEffect(() => {
        if (!userId) return;
        
        isManualDisconnectRef.current = false;
        
        const fetchUsers = async () => {
            try {
                console.log('Cargando usuarios...');
                const res = await fetch('https://users-service-production-6ca2.up.railway.app/users');
                if (res.ok) {
                    const data = await res.json();
                    console.log('Users API response:', data);
                    
                    if (Array.isArray(data)) {
                        setUsers(data);
                    } else if (data.users && Array.isArray(data.users)) {
                        setUsers(data.users);
                    } else if (data.data && Array.isArray(data.data)) {
                        setUsers(data.data);
                    } else {
                        console.error('Unexpected users API response format:', data);
                        setUsers([]);
                    }
                } else {
                    console.error('Failed to fetch users:', res.status);
                    setUsers([]);
                }
            } catch (err) {
                console.error("Error loading users:", err);
                setUsers([]);
            }
        };
        fetchUsers();

        connectWebSocket();

        return () => {
            isManualDisconnectRef.current = true;
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (socketRef.current) {
                socketRef.current.close(1000, 'Component unmounting');
            }
        };
    }, [userId, connectWebSocket]);

    const selectChat = async (chat) => {
        console.log('🔄 Cambiando a chat:', chat.chat_id);
        setCurrentChatId(chat.chat_id);
        try {
            setIsLoading(true);
            console.log('📥 Cargando mensajes para chat:', chat.chat_id);
            const res = await fetch(`https://messages-service-production.up.railway.app/chats/${chat.chat_id}/messages`);
            if (!res.ok) {
                throw new Error(`Error HTTP: ${res.status}`);
            }
            const data = await res.json();
            console.log('📥 Mensajes cargados:', data);
            setMessages(data.messages || []);
            setIsLoading(false);
        } catch (err) {
            console.error("❌ Error loading messages:", err);
            setIsLoading(false);
        }
    };

    const logout = () => {
        isManualDisconnectRef.current = true;
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        if (socketRef.current) {
            socketRef.current.close(1000, 'User logout');
        }
        document.cookie = 'user_id=; Max-Age=0; path=/;';
        window.location.href = '/';
    };

    // Función para reconectar manualmente
    const manualReconnect = () => {
        reconnectAttemptsRef.current = 0;
        isManualDisconnectRef.current = false;
        connectWebSocket();
    };

    const sendMessage = async () => {
        if (!messageInput.trim() || !currentChatId) {
            console.warn('⚠️ No se puede enviar: mensaje vacío o sin chat seleccionado');
            return;
        }
        
        console.log('📤 Enviando mensaje...');
        console.log('   - Contenido:', messageInput);
        console.log('   - Chat ID:', currentChatId);
        console.log('   - User ID:', userId);
        
        const payload = {
            sender_id: parseInt(userId),
            chat_id: currentChatId,
            content: messageInput,
        };

        const messageToSend = messageInput;
        
        try {
            setMessageInput('');
            
            console.log('📤 Enviando a API messages:', payload);
            const res = await fetch('https://messages-service-production.up.railway.app/messages', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            
            if (res.ok) {
                const responseData = await res.json();
                console.log('✅ Mensaje enviado exitosamente:', responseData);
                
                // Crear mensaje para WebSocket
                const messageData = {
                    sender_id: parseInt(userId),
                    chat_id: currentChatId,
                    content: messageToSend,
                    timestamp: new Date().toISOString()
                };
                
                console.log('📤 Enviando por WebSocket:', messageData);
                if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                    socketRef.current.send(JSON.stringify(messageData));
                    console.log('✅ Mensaje enviado por WebSocket');
                } else {
                    console.warn('⚠️ WebSocket no está conectado');
                }

                // Recargar mensajes para obtener la versión del servidor
                console.log('🔄 Recargando mensajes del servidor...');
                const messagesRes = await fetch(`https://messages-service-production.up.railway.app/chats/${currentChatId}/messages`);
                if (messagesRes.ok) {
                    const messagesData = await messagesRes.json();
                    console.log('📥 Mensajes recargados:', messagesData);
                    setMessages(messagesData.messages || []);
                } else {
                    console.error('❌ Error recargando mensajes:', await messagesRes.text());
                }
                
            } else {
                const errorText = await res.text();
                console.error("❌ Failed to send message:", errorText);
                setMessageInput(messageToSend);
            }
        } catch (err) {
            console.error("❌ Network error:", err);
            setMessageInput(messageToSend);
        }
    };

    const openCreateChatModal = () => {
        setIsModalOpen(true);
    };

    const closeCreateChatModal = () => {
        setIsModalOpen(false);
        setSelectedUsers([]);
    };

    const toggleUserSelection = (userId) => {
        setSelectedUsers(prev => {
            if (prev.includes(userId)) {
                return prev.filter(id => id !== userId);
            } else {
                return [...prev, userId];
            }
        });
    };

    const createChat = async () => {
        const chatName = document.getElementById("chatName").value;
        
        const payload = {
            creator_id: parseInt(userId),
            participant_ids: selectedUsers.map(id => parseInt(id)),
            name: chatName || undefined
        };
        
        try {
            console.log('🆕 Creando chat:', payload);
            const res = await fetch('https://chats-service-production.up.railway.app/chats', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const result = await res.json();
            console.log('🆕 Resultado crear chat:', result);
            
            if (result.error) {
                alert("Error: " + result.error);
            } else {
                closeCreateChatModal();
                loadChats();
                alert("¡Chat creado exitosamente!");
            }
        } catch (err) {
            console.error("❌ Error creating chat:", err);
            alert("Error al crear el chat");
        }
    };

    useEffect(() => {
        if (userId) {
            loadChats();
        }
    }, [userId, loadChats]);

    // Obtener inicial del nombre del remitente
    const getInitial = (userId) => {
        const name = getUserName(userId);
        return name.charAt(0).toUpperCase();
    };

    return (
        <div className={styles.chatContainer}>
            <div className={styles.sidebar}>
                <div className={styles.sidebarHeader}>
                    <div className={styles.appTitle}>
                        UPTC MESSENGER
                        <span className={`${styles.connectionStatus} ${isConnected ? styles.connected : styles.disconnected}`}>
                            {isConnected ? '●' : '○'}
                        </span>
                    </div>
                    <button className={styles.logoutBtn} onClick={logout}>
                        Cerrar sesión
                    </button>
                </div>
                
                <div className={styles.chatList}>
                    {isLoading ? (
                        <div className={styles.loadingContainer}>
                            <div className={styles.loadingSpinner}></div>
                            <p>Cargando chats...</p>
                        </div>
                    ) : chats.length === 0 ? (
                        <div className={styles.emptyState}>
                            <p>No tienes chats</p>
                            <button 
                                className={styles.createFirstChatBtn}
                                onClick={openCreateChatModal}
                            >
                                Crear primer chat
                            </button>
                        </div>
                    ) : (
                        chats.map(chat => (
                            <div 
                                key={chat.chat_id} 
                                className={`${styles.chatItem} ${currentChatId === chat.chat_id ? styles.activeChat : ''}`}
                                onClick={() => selectChat(chat)}
                            >
                                <div className={styles.avatar}>
                                    {chat.name ? chat.name.charAt(0).toUpperCase() : 'C'}
                                </div>
                                <div className={styles.chatInfo}>
                                    <div className={styles.name}>{chat.name || 'Chat'}</div>
                                    <div className={styles.lastMessage}>
                                        {chat.last_message
                                            ? chat.last_message.length > 30
                                                ? chat.last_message.slice(0, 30) + '...'
                                                : chat.last_message
                                            : 'No hay mensajes'}
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
            
            <div className={styles.chatWindow}>
                {currentChatId ? (
                    <>
                        <div className={styles.chatHeader}>
                            {chats.find(chat => chat.chat_id === currentChatId)?.name || 'Chat'}
                            {!isConnected && (
                                <div className={styles.connectionInfo}>
                                    <span className={styles.reconnectingText}>
                                        {reconnectAttemptsRef.current >= maxReconnectAttempts 
                                            ? 'Desconectado' 
                                            : 'Reconectando...'
                                        }
                                    </span>
                                    {reconnectAttemptsRef.current >= maxReconnectAttempts && (
                                        <button 
                                            className={styles.reconnectBtn}
                                            onClick={manualReconnect}
                                        >
                                            Reconectar
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                        
                        <div 
                            className={styles.chatMessages} 
                            ref={chatMessagesRef}
                        >
                            {isLoading ? (
                                <div className={styles.loadingContainer}>
                                    <div className={styles.loadingSpinner}></div>
                                    <p>Cargando mensajes...</p>
                                </div>
                            ) : messages.length === 0 ? (
                                <div className={styles.emptyChat}>
                                    <p>Envía un mensaje para comenzar la conversación</p>
                                </div>
                            ) : (
                                messages.map((msg, index) => {
                                    const isOwnMessage = String(msg.sender_id) === String(userId);
                                    
                                    return (
                                        <div 
                                            key={`${msg.sender_id}-${msg.timestamp}-${index}`} 
                                            className={`${styles.message} ${
                                                isOwnMessage ? styles.outgoing : styles.incoming
                                            }`}
                                            ref={index === messages.length - 1 ? lastMessageRef : null}
                                        >
                                            {/* Avatar para mensajes entrantes */}
                                            {!isOwnMessage && (
                                                <div 
                                                    className={styles.messageAvatar}
                                                    title={getUserName(msg.sender_id)}
                                                >
                                                    {getInitial(msg.sender_id)}
                                                </div>
                                            )}
                                            <div className={styles.bubble}>{msg.content}</div>
                                            
                                            <div className={styles.messageActions}>
                                                <span className={styles.time}>
                                                    {new Date(msg.timestamp).toLocaleTimeString([], { 
                                                        hour: '2-digit', 
                                                        minute: '2-digit' 
                                                    })}
                                                </span>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                        
                        <div className={styles.chatInput}>
                            <textarea 
                                value={messageInput} 
                                onChange={(e) => setMessageInput(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        sendMessage();
                                    }
                                }}
                                placeholder="Escribe un mensaje..." 
                                rows={1}
                                disabled={!isConnected}
                            />
                            <button 
                                onClick={sendMessage}
                                disabled={!messageInput.trim() || !isConnected}
                            >
                                Enviar
                            </button>
                        </div>
                    </>
                ) : (
                    <div className={styles.welcomeScreen}>
                        <h2>Bienvenido a UPTC Messenger</h2>
                        <p>Selecciona un chat o crea uno nuevo para comenzar</p>
                        <button 
                            className={styles.createChatWelcomeBtn}
                            onClick={openCreateChatModal}
                        >
                            Crear nuevo chat
                        </button>
                    </div>
                )}
            </div>

            <button 
                className={styles.createChatBtn} 
                onClick={openCreateChatModal}
            >
                +
            </button>

            {isModalOpen && (
                <div className={styles.modal}>
                    <div 
                        className={styles.modalContent}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <span 
                            className={styles.close} 
                            onClick={closeCreateChatModal}
                        >
                            &times;
                        </span>
                        <h2>Crear Nuevo Chat</h2>
                        <div className={styles.formGroup}>
                            <label htmlFor="chatName">Nombre del chat (opcional):</label>
                            <input 
                                type="text" 
                                id="chatName" 
                                placeholder="Nombre del chat" 
                            />
                        </div>
                        <div className={styles.formGroup}>
                            <label>Seleccionar participantes:</label>
                            <div className={styles.userList}>
                                {Array.isArray(users) && users.length > 0 ? (
                                    users
                                        .filter(user => String(user.id || user.user_id) !== String(userId))
                                        .map(user => (
                                            <div 
                                                key={user.id || user.user_id} 
                                                className={`${styles.userItem} ${selectedUsers.includes(user.id || user.user_id) ? styles.selected : ''}`}
                                                onClick={() => toggleUserSelection(user.id || user.user_id)}
                                            >
                                                <div className={styles.userAvatar}>
                                                    {user.first_name ? user.first_name.charAt(0) : 'U'}
                                                </div>
                                                <div className={styles.userInfo}>
                                                    <div className={styles.userName}>
                                                        {user.first_name || 'Usuario'} {user.last_name || ''}
                                                    </div>
                                                    <div className={styles.userUsername}>
                                                        @{user.username || 'usuario'}
                                                    </div>
                                                </div>
                                            </div>
                                        ))
                                ) : (
                                    <div className={styles.emptyUsers}>
                                        <p>No hay usuarios disponibles</p>
                                    </div>
                                )}
                            </div>
                        </div>
                        <button 
                            className={styles.createChatModalBtn}
                            onClick={createChat}
                            disabled={selectedUsers.length === 0}
                        >
                            Crear Chat
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Chat;

