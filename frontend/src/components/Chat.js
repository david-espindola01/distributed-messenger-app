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
    const userId = getCookie('user_id');
    const socketRef = useRef(null);
    const chatMessagesRef = useRef(null);
    const lastMessageRef = useRef(null);

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

    // Inicializar WebSocket y cargar usuarios
    useEffect(() => {
        if (!userId) return;
        
        // Cargar lista de usuarios
        const fetchUsers = async () => {
            try {
                const res = await fetch('http://localhost:5005/users');
                if (res.ok) {
                    const data = await res.json();
                    setUsers(data);
                }
            } catch (err) {
                console.error("Error loading users:", err);
            }
        };
        fetchUsers();

        // Configurar WebSocket
        socketRef.current = new WebSocket(`ws://localhost:5004/ws?user_id=${userId}`);
        
        socketRef.current.onopen = () => {
            console.log("WebSocket connection established");
        };
        
        socketRef.current.onmessage = (event) => {
            const messageData = JSON.parse(event.data);
            
            // Si el mensaje es para el chat actual
            if (String(messageData.chat_id) === String(currentChatId)) {
                setMessages(prev => [...prev, messageData]);
            }
            // Actualizar lista de chats en todos los casos
            loadChats();
        };

        socketRef.current.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        socketRef.current.onclose = () => {
            console.log("WebSocket closed. Reconnecting in 2 seconds...");
            setTimeout(() => {
                if (userId) {
                    socketRef.current = new WebSocket(`ws://localhost:5004/ws?user_id=${userId}`);
                }
            }, 2000);
        };

        return () => {
            if (socketRef.current) {
                socketRef.current.close();
            }
        };
    }, [userId, currentChatId]);

    const loadChats = useCallback(async () => {
        try {
            setIsLoading(true);
            const res = await fetch(`http://localhost:5002/user/${userId}/chats`);
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            const data = await res.json();
            setChats(data);
            setIsLoading(false);
        } catch (err) {
            console.error("Error loading chats:", err);
            setIsLoading(false);
        }
    }, [userId]);

    const selectChat = async (chat) => {
        setCurrentChatId(chat.chat_id);
        try {
            setIsLoading(true);
            const res = await fetch(`http://localhost:5003/chat/${chat.chat_id}/messages`);
            const data = await res.json();
            setMessages(data);
            setIsLoading(false);
        } catch (err) {
            console.error("Error loading messages:", err);
            setIsLoading(false);
        }
    };

    const logout = () => {
        document.cookie = 'user_id=; Max-Age=0; path=/;';
        window.location.href = '/';
    };

    const sendMessage = async () => {
        if (!messageInput.trim() || !currentChatId) return;
        
        const payload = {
            sender_id: userId,
            chat_id: currentChatId,
            content: messageInput,
            timestamp: new Date().toISOString(),
        };

        try {
            setMessageInput('');
            // Mensaje optimista
            setMessages(prev => [...prev, payload]);
            
            const res = await fetch('http://localhost:5003/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            
            if (!res.ok) {
                console.error("Failed to send message:", await res.text());
                setMessages(prev => prev.slice(0, -1));
            }
        } catch (err) {
            console.error("Network error:", err);
            setMessages(prev => prev.slice(0, -1));
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
            creator_id: userId,
            participant_ids: selectedUsers,
            name: chatName
        };
        
        try {
            const res = await fetch('http://localhost:5002/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const result = await res.json();
            if (result.error) {
                alert("Error: " + result.error);
            } else {
                closeCreateChatModal();
                loadChats();
                alert("¡Chat creado exitosamente!");
            }
        } catch (err) {
            console.error("Error creating chat:", err);
            alert("Error al crear el chat");
        }
    };

    useEffect(() => {
        if (userId) {
            loadChats();
        }
    }, [userId, loadChats]);

    return (
        <div className={styles.chatContainer}>
            <div className={styles.sidebar}>
                <div className={styles.sidebarHeader}>
                    <div className={styles.appTitle}>UPTC MESSENGER</div>
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
                                        {chat.last_message || 'No hay mensajes'}
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
                                messages.map((msg, index) => (
                                    <div 
                                        key={index} 
                                        className={`${styles.message} ${
                                            String(msg.sender_id) === String(userId) ? styles.outgoing : styles.incoming
                                        }`}
                                        ref={index === messages.length - 1 ? lastMessageRef : null}
                                    >
                                        <div className={styles.bubble}>{msg.content}</div>
                                        <span className={styles.time}>
                                            {new Date(msg.timestamp).toLocaleTimeString([], { 
                                                hour: '2-digit', 
                                                minute: '2-digit' 
                                            })}
                                        </span>
                                    </div>
                                ))
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
                            />
                            <button 
                                onClick={sendMessage}
                                disabled={!messageInput.trim()}
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
                                {users.filter(user => user.user_id !== userId).map(user => (
                                    <div 
                                        key={user.user_id} 
                                        className={`${styles.userItem} ${selectedUsers.includes(user.user_id) ? styles.selected : ''}`}
                                        onClick={() => toggleUserSelection(user.user_id)}
                                    >
                                        <div className={styles.userAvatar}>
                                            {user.first_name.charAt(0)}
                                        </div>
                                        <div className={styles.userInfo}>
                                            <div className={styles.userName}>
                                                {user.first_name} {user.last_name}
                                            </div>
                                            <div className={styles.userUsername}>
                                                @{user.username}
                                            </div>
                                        </div>
                                    </div>
                                ))}
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