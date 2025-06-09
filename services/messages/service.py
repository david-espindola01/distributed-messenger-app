from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from datetime import datetime
import logging
import uuid
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'	
)
logger = logging.getLogger(__name__)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_USER = os.environ.get("DB_USER", "admin")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME", "message-app-db")

if not DB_PASSWORD:
    raise ValueError("DB_PASSWORD debe estar configurada en las variables de entorno")

try:
    db_pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )
    logger.info("Pool de conexiones a DB creado correctamente")
except Exception as e:
    logger.error(f"Error creando pool de conexiones: {e}")
    raise

def get_db_connection():
    try:
        return db_pool.getconn()
    except Exception as e:
        logger.error(f"Error obteniendo conexión del pool: {e}")
        raise

def return_db_connection(conn):
    try:
        db_pool.putconn(conn)
    except Exception as e:
        logger.error(f"Error devolviendo conexión al pool: {e}")

def get_user_by_id(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, username, first_name, last_name, 
                   is_active, created_at
            FROM users 
            WHERE id = %s AND is_active = true
        """, (user_id,))
        row = cur.fetchone()
        cur.close()
        return row
    except Exception as e:
        logger.error(f"Error en get_user_by_id: {e}")
        return None
    finally:
        if conn:
            return_db_connection(conn)

def get_chat_by_id(chat_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, name, created_at, updated_at, is_active
            FROM chats 
            WHERE id = %s AND is_active = true
        """, (chat_id,))
        chat_data = cur.fetchone()
        cur.close()
        return chat_data
    except Exception as e:
        logger.error(f"Error en get_chat_by_id: {e}")
        return None
    finally:
        if conn:
            return_db_connection(conn)

def user_is_in_chat(user_id, chat_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 1 FROM user_chat 
            WHERE user_id = %s AND chat_id = %s
        """, (user_id, chat_id))
        result = cur.fetchone()
        cur.close()
        return result is not None
    except Exception as e:
        logger.error(f"Error en user_is_in_chat: {e}")
        return False
    finally:
        if conn:
            return_db_connection(conn)

def create_message_in_db(sender_id, chat_id, content):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Insertar mensaje
        cur.execute("""
            INSERT INTO messages (sender_id, chat_id, content, timestamp)
            VALUES (%s, %s, %s, %s)
            RETURNING id, sender_id, chat_id, content, timestamp
        """, (sender_id, chat_id, content, datetime.utcnow()))
        
        message_data = cur.fetchone()
        
        # Actualizar timestamp del chat
        cur.execute("""
            UPDATE chats 
            SET updated_at = %s 
            WHERE id = %s
        """, (datetime.utcnow(), chat_id))
        
        conn.commit()
        cur.close()
        
        logger.info(f"Mensaje creado exitosamente: Usuario {sender_id} en chat {chat_id}")
        return message_data
        
    except Exception as e:
        logger.error(f"Error en create_message_in_db: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            return_db_connection(conn)

def get_messages_for_chat(chat_id, limit=50, offset=0):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT m.id, m.sender_id, m.chat_id, m.content, m.timestamp,
                   u.username, u.first_name, u.last_name
            FROM messages m
            LEFT JOIN users u ON m.sender_id = u.id
            WHERE m.chat_id = %s
            ORDER BY m.timestamp DESC
            LIMIT %s OFFSET %s
        """, (chat_id, limit, offset))
        
        messages = cur.fetchall()
        cur.close()
        
        # Revertir orden para tener los más antiguos primero
        return list(reversed(messages))
        
    except Exception as e:
        logger.error(f"Error en get_messages_for_chat: {e}")
        return []
    finally:
        if conn:
            return_db_connection(conn)

def get_message_by_id(message_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT m.id, m.sender_id, m.chat_id, m.content, m.timestamp,
                   u.username, u.first_name, u.last_name
            FROM messages m
            LEFT JOIN users u ON m.sender_id = u.id
            WHERE m.id = %s
        """, (message_id,))
        
        message = cur.fetchone()
        cur.close()
        return message
        
    except Exception as e:
        logger.error(f"Error en get_message_by_id: {e}")
        return None
    finally:
        if conn:
            return_db_connection(conn)

def delete_message_in_db(message_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM messages 
            WHERE id = %s
            RETURNING id
        """, (message_id,))
        
        deleted_id = cur.fetchone()
        conn.commit()
        cur.close()
        
        if deleted_id:
            logger.info(f"Mensaje eliminado exitosamente: ID {message_id}")
            return True
        return False
        
    except Exception as e:
        logger.error(f"Error en delete_message_in_db: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            return_db_connection(conn)

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "Messages API - Servicio de gestión de mensajes",
        "version": "1.0.0",
        "endpoints": [
            "POST /messages - Enviar nuevo mensaje",
            "GET /chats/<chat_id>/messages - Obtener mensajes de un chat",
            "GET /messages/<message_id> - Obtener mensaje por ID",
            "DELETE /messages/<message_id> - Eliminar mensaje",
            "GET /health - Health check"
        ]
    })

@app.route('/messages', methods=['POST'])
def send_message():
    try:
        data = request.json
        sender_id = data.get("sender_id")
        chat_id = data.get("chat_id")
        content = data.get("content", "").strip()
        
        if not sender_id or not chat_id or not content:
            return jsonify({"error": "sender_id, chat_id y content son requeridos"}), 400
        
        # Verificar que el usuario existe
        sender = get_user_by_id(sender_id)
        if not sender:
            return jsonify({"error": "Usuario remitente no encontrado"}), 404
        
        # Verificar que el chat existe
        chat = get_chat_by_id(chat_id)
        if not chat:
            return jsonify({"error": "Chat no encontrado"}), 404
        
        # Verificar que el usuario está en el chat
        if not user_is_in_chat(sender_id, chat_id):
            return jsonify({"error": "Usuario no pertenece al chat"}), 403
        
        # Crear mensaje
        message_data = create_message_in_db(sender_id, chat_id, content)
        
        response_data = {
            "message_id": message_data["id"],
            "sender_id": message_data["sender_id"],
            "chat_id": message_data["chat_id"],
            "content": message_data["content"],
            "timestamp": message_data["timestamp"].isoformat(),
            "sender": {
                "user_id": sender["id"],
                "username": sender["username"],
                "first_name": sender["first_name"],
                "last_name": sender["last_name"]
            }
        }
        
        return jsonify({
            "message": "Mensaje enviado exitosamente",
            "data": response_data
        }), 201
        
    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/chats/<chat_id>/messages', methods=['GET'])
def get_chat_messages(chat_id):
    try:
        # Parámetros de paginación
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        user_id = request.args.get('user_id', type=int)
        
        # Verificar que el chat existe
        chat = get_chat_by_id(chat_id)
        if not chat:
            return jsonify({"error": "Chat no encontrado"}), 404
        
        # Si se proporciona user_id, verificar que está en el chat
        if user_id and not user_is_in_chat(user_id, chat_id):
            return jsonify({"error": "Usuario no pertenece al chat"}), 403
        
        # Obtener mensajes
        messages_data = get_messages_for_chat(chat_id, limit, offset)
        
        messages = []
        for message_data in messages_data:
            message_dict = {
                "message_id": message_data["id"],
                "sender_id": message_data["sender_id"],
                "chat_id": message_data["chat_id"],
                "content": message_data["content"],
                "timestamp": message_data["timestamp"].isoformat()
            }
            
            # Agregar información del remitente si está disponible
            if message_data["username"]:
                message_dict["sender"] = {
                    "user_id": message_data["sender_id"],
                    "username": message_data["username"],
                    "first_name": message_data["first_name"],
                    "last_name": message_data["last_name"]
                }
            else:
                message_dict["sender"] = None  # Usuario eliminado
            
            messages.append(message_dict)
        
        return jsonify({
            "chat_id": chat_id,
            "messages": messages,
            "total": len(messages),
            "limit": limit,
            "offset": offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo mensajes del chat: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/messages/<int:message_id>', methods=['GET'])
def get_message(message_id):
    try:
        message_data = get_message_by_id(message_id)
        
        if not message_data:
            return jsonify({"error": "Mensaje no encontrado"}), 404
        
        response_data = {
            "message_id": message_data["id"],
            "sender_id": message_data["sender_id"],
            "chat_id": message_data["chat_id"],
            "content": message_data["content"],
            "timestamp": message_data["timestamp"].isoformat()
        }
        
        # Agregar información del remitente si está disponible
        if message_data["username"]:
            response_data["sender"] = {
                "user_id": message_data["sender_id"],
                "username": message_data["username"],
                "first_name": message_data["first_name"],
                "last_name": message_data["last_name"]
            }
        else:
            response_data["sender"] = None  # Usuario eliminado
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo mensaje: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    try:
        # Verificar que el mensaje existe
        message_data = get_message_by_id(message_id)
        if not message_data:
            return jsonify({"error": "Mensaje no encontrado"}), 404
        
        # Eliminar mensaje
        deleted = delete_message_in_db(message_id)
        
        if deleted:
            return jsonify({
                "message": "Mensaje eliminado exitosamente",
                "message_id": message_id
            }), 200
        else:
            return jsonify({"error": "No se pudo eliminar el mensaje"}), 500
        
    except Exception as e:
        logger.error(f"Error eliminando mensaje: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        return_db_connection(conn)
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "service": "messages-api"
        }), 200
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "service": "messages-api"
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint no encontrado"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Método no permitido"}), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error interno del servidor: {error}")
    return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
