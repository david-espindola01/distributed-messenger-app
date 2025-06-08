// src/components/Chat.js
import React, { useEffect, useState, useCallback } from 'react';
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
    const userId = getCookie('user_id');

    const initializeWebSocket = useCallback(() => {
        const socket = new WebSocket(`ws://localhost:5004/ws?user_id=${userId}`);
        socket.onopen = () => {
            console.log("Conexión WebSocket establecida.");
        };

        socket.onmessage = (event) => {
            const messageData = JSON.parse(event.data);
            if (String(messageData.chat_id) === String(currentChatId)) {
                addMessageToUI(messageData);
            } else {
                loadChats();
            }
        };

        socket.onerror = (error) => {
            console.error("Error en WebSocket:", error);
        };

        socket.onclose = () => {
            console.log("WebSocket cerrado. Reintentando conexión en 2 segundos...");
            setTimeout(initializeWebSocket, 2000);
        };
    }, [userId, currentChatId]);

    const loadChats = useCallback(async () => {
        try {
            const res = await fetch(`http://localhost:5002/user/${userId}/chats`);
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            const data = await res.json();
            setChats(data);
        } catch (err) {
            console.error("Error al cargar los chats:", err);
        }
    }, [userId]);

    const selectChat = async (chat) => {
        setCurrentChatId(chat.chat_id);
        await loadMessages(chat.chat_id);
    };

    const loadMessages = async (chatId) => {
        try {
            const res = await fetch(`http://localhost:5003/chat/${chatId}/messages`);
            const data = await res.json();
            setMessages(data);
        } catch (err) {
            console.error(err);
        }
    };

    const addMessageToUI = (messageData) => {
        const type = String(messageData.sender_id).trim() === String(userId).trim() ? 'outgoing' : 'incoming';
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'bubble';
        bubbleDiv.textContent = messageData.content;
        const timeSpan = document.createElement('span');
        timeSpan.className = 'time';
        timeSpan.textContent = new Date(messageData.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        if (type === 'outgoing') {
            messageDiv.appendChild(timeSpan);
            messageDiv.appendChild(bubbleDiv);
        } else {
            messageDiv.appendChild(bubbleDiv);
            messageDiv.appendChild(timeSpan);
        }

        const chatMessages = document.getElementById('chatMessages');
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    useEffect(() => {
        initializeWebSocket();
        loadChats();
    }, [initializeWebSocket, loadChats]);

    const logout = () => {
        document.cookie = 'user_id=; Max-Age=0; path=/;';
        window.location.href = '/';
    };

    const sendMessage = async () => {
        if (!messageInput || !currentChatId) return;
        const payload = {
            sender_id: userId,
            chat_id: currentChatId,
            content: messageInput,
            timestamp: new Date().toISOString(),
        };

        try {
            const res = await fetch('http://localhost:5003/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            await res.json();
            setMessageInput('');
        } catch (err) {
            console.error(err);
        }
    };

    const openCreateChatModal = () => {
        setIsModalOpen(true);
    };

    const closeCreateChatModal = () => {
        setIsModalOpen(false);
    };

    const createChat = async () => {
        const chatName = document.getElementById("chatName").value;
        const participantIdsString = document.getElementById("participantIds").value;
        let participantIds = [];
        if (participantIdsString.trim() !== "") {
            participantIds = participantIdsString.split(",").map(id => id.trim());
        }
        const payload = {
            creator_id: userId,
            participant_ids: participantIds,
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
                alert("Chat creado exitosamente!");
                closeCreateChatModal();
                loadChats();
            }
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className={styles.chatContainer}>
            <div className={styles.sidebar}>
                <div className={styles.sidebarHeader}>UPTC MESSENGER</div>
                <button id="logout-btn" onClick={logout}>Cerrar sesión</button>
                <div className={styles.chatList}>
                    {chats.map(chat => (
                        <div key={chat.chat_id} className={styles.chatItem} onClick={() => selectChat(chat)}>
                            <div className={styles.avatar}></div>
                            <div className={styles.chatInfo}>
                                <div className={styles.name}>{chat.name || 'Chat'}</div>
                                <div className={styles.lastMessage}>{chat.last_message || ''}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
            <div className={styles.chatWindow}>
                <div className={styles.chatHeader}>Chat</div>
                <div className={styles.chatMessages} id="chatMessages">
                    {messages.map((msg, index) => (
                        <div key={index} className={`${styles.message} ${msg.sender_id === userId ? styles.outgoing : styles.incoming}`}>
                            <div className={styles.bubble}>{msg.content}</div>
                            <span className={styles.time}>{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                    ))}
                </div>
                <div className={styles.chatInput}>
                    <input type="text" value={messageInput} onChange={(e) => setMessageInput(e.target.value)} placeholder="Escribe un mensaje" />
                    <button onClick={sendMessage}>Enviar</button>
                </div>
            </div>

            {/* Botón flotante para crear chat */}
            <button id="createChatBtn" onClick={openCreateChatModal}>+</button>

            {/* Modal para crear chat */}
            {isModalOpen && (
                <div className={styles.modal}>
                    <div className={styles.modalContent}>
                        <span className={styles.close} onClick={closeCreateChatModal}>&times;</span>
                        <h2>Crear Nuevo Chat</h2>
                        <label htmlFor="chatName">Nombre del chat (opcional):</label>
                        <input type="text" id="chatName" placeholder="Nombre del chat" />
                        <label htmlFor="participantIds">IDs de participantes (separados por comas):</label>
                        <input type="text" id="participantIds" placeholder="Ej. 2,3,4" />
                        <button onClick={createChat}>Crear Chat</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Chat;
