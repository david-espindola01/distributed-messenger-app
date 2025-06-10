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

def create_chat_in_db(name):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        chat_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO chats (id, name, created_at, updated_at, is_active)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (chat_id, name, datetime.utcnow(), datetime.utcnow(), True))
        created_chat_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        logger.info(f"Chat creado exitosamente: {name} (ID: {created_chat_id})")
        return created_chat_id
    except Exception as e:
        logger.error(f"Error en create_chat_in_db: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            return_db_connection(conn)

def get_personalized_chat_name(chat_data, participants, for_user_id):
    if len(participants) == 2:
        other_participant = next((p for p in participants if p["id"] != for_user_id), None)
        if other_participant:
            return f"{other_participant['first_name']} {other_participant['last_name']}"
    return chat_data["name"]

def add_user_to_chat_in_db(user_id, chat_id, is_admin=False):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_chat (user_id, chat_id, is_admin)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, chat_id) DO NOTHING
        """, (user_id, chat_id, is_admin))
        conn.commit()
        cur.close()
        logger.info(f"Usuario {user_id} agregado al chat {chat_id} (admin: {is_admin})")
    except Exception as e:
        logger.error(f"Error en add_user_to_chat_in_db: {e}")
        if conn:
            conn.rollback()
        raise
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
        if not chat_data:
            return None
        cur.execute("""
            SELECT u.id, u.username, u.first_name, u.last_name, 
                   u.is_active, uc.is_admin
            FROM users u
            JOIN user_chat uc ON u.id = uc.user_id
            WHERE uc.chat_id = %s AND u.is_active = true
            ORDER BY uc.is_admin DESC, u.first_name
        """, (chat_id,))
        participants = cur.fetchall()
        cur.close()
        return {
            "chat": chat_data,
            "participants": participants
        }
    except Exception as e:
        logger.error(f"Error en get_chat_by_id: {e}")
        return None
    finally:
        if conn:
            return_db_connection(conn)

def get_user_chats(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT c.id, c.name, c.created_at, c.updated_at, c.is_active,
                   uc.is_admin
            FROM chats c
            JOIN user_chat uc ON c.id = uc.chat_id
            WHERE uc.user_id = %s AND c.is_active = true
            ORDER BY c.updated_at DESC
        """, (user_id,))
        chats = cur.fetchall()
        cur.close()
        return chats
    except Exception as e:
        logger.error(f"Error en get_user_chats: {e}")
        return []
    finally:
        if conn:
            return_db_connection(conn)

def get_chat_participants(chat_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT u.id, u.username, u.first_name, u.last_name, 
                   u.is_active, uc.is_admin
            FROM users u
            JOIN user_chat uc ON u.id = uc.user_id
            WHERE uc.chat_id = %s AND u.is_active = true
            ORDER BY uc.is_admin DESC, u.first_name
        """, (chat_id,))
        participants = cur.fetchall()
        cur.close()
        return participants
    except Exception as e:
        logger.error(f"Error en get_chat_participants: {e}")
        return []
    finally:
        if conn:
            return_db_connection(conn)

def remove_user_from_chat_in_db(user_id, chat_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM user_chat 
            WHERE user_id = %s AND chat_id = %s
        """, (user_id, chat_id))
        conn.commit()
        cur.close()
        logger.info(f"Usuario {user_id} removido del chat {chat_id}")
    except Exception as e:
        logger.error(f"Error en remove_user_from_chat_in_db: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            return_db_connection(conn)

def deactivate_chat_in_db(chat_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE chats 
            SET is_active = false, updated_at = %s
            WHERE id = %s
        """, (datetime.utcnow(), chat_id))
        conn.commit()
        cur.close()
        logger.info(f"Chat {chat_id} desactivado")
    except Exception as e:
        logger.error(f"Error en deactivate_chat_in_db: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            return_db_connection(conn)

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "Chats API - Servicio de gestión de chats",
        "version": "1.0.0",
        "endpoints": [
            "POST /chats - Crear nuevo chat",
            "GET /chats/<chat_id> - Obtener chat por ID",
            "GET /users/<user_id>/chats - Obtener chats de un usuario",
            "POST /chats/<chat_id>/participants - Agregar participante a chat",
            "DELETE /chats/<chat_id>/participants/<user_id> - Remover participante",
            "DELETE /chats/<chat_id> - Desactivar chat",
            "GET /health - Health check"
        ]
    })

@app.route('/chats', methods=['POST'])
def create_chat():
   try:
       data = request.json
       creator_id = data.get("creator_id")
       participant_ids = data.get("participant_ids", [])
       name = data.get("name", "")
       if not creator_id:
           return jsonify({"error": "creator_id es requerido"}), 400
       creator = get_user_by_id(creator_id)
       if not creator:
           return jsonify({"error": "Usuario creador no encontrado"}), 404
       valid_participants = [creator_id]
       for pid in participant_ids:
           if pid != creator_id:
               user = get_user_by_id(pid)
               if user:
                   valid_participants.append(pid)
               else:
                   return jsonify({"error": f"Participante con ID {pid} no encontrado"}), 404
       if not name:
           name = f"Chat de {creator['first_name']}"
       chat_id = create_chat_in_db(name)
       for user_id in valid_participants:
           is_admin = (user_id == creator_id)
           add_user_to_chat_in_db(user_id, chat_id, is_admin)
       chat_info = get_chat_by_id(chat_id)
       chat_name = get_personalized_chat_name(
           chat_info["chat"], 
           chat_info["participants"], 
           creator_id
       )
       response_data = {
           "chat_id": chat_info["chat"]["id"],
           "name": chat_name,
           "created_at": chat_info["chat"]["created_at"].isoformat(),
           "updated_at": chat_info["chat"]["updated_at"].isoformat(),
           "is_active": chat_info["chat"]["is_active"],
           "participants": []
       }
       for participant in chat_info["participants"]:
           response_data["participants"].append({
               "user_id": participant["id"],
               "username": participant["username"],
               "first_name": participant["first_name"],
               "last_name": participant["last_name"],
               "is_admin": participant["is_admin"]
           })
       return jsonify({
           "message": "Chat creado exitosamente",
           "chat": response_data
       }), 201
   except Exception as e:
       logger.error(f"Error creando chat: {e}")
       return jsonify({"error": "Error interno del servidor"}), 500
       
def get_last_message_for_chat(chat_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT content, timestamp
            FROM messages
            WHERE chat_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """, (chat_id,))
        last_msg = cur.fetchone()
        cur.close()
        return last_msg
    except Exception as e:
        logger.error(f"Error en get_last_message_for_chat: {e}")
        return None
    finally:
        if conn:
            return_db_connection(conn)

@app.route('/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    try:
        user_id = request.args.get('user_id', type=int)
        chat_info = get_chat_by_id(chat_id)
        if not chat_info:
            return jsonify({"error": "Chat no encontrado"}), 404
        chat_name = chat_info["chat"]["name"]
        if user_id:
            chat_name = get_personalized_chat_name(
                chat_info["chat"], 
                chat_info["participants"], 
                user_id
            )
        response_data = {
            "chat_id": chat_info["chat"]["id"],
            "name": chat_name,
            "created_at": chat_info["chat"]["created_at"].isoformat(),
            "updated_at": chat_info["chat"]["updated_at"].isoformat(),
            "is_active": chat_info["chat"]["is_active"],
            "participants": []
        }
        for participant in chat_info["participants"]:
            response_data["participants"].append({
                "user_id": participant["id"],
                "username": participant["username"],
                "first_name": participant["first_name"],
                "last_name": participant["last_name"],
                "is_admin": participant["is_admin"]
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.error(f"Error obteniendo chat: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/users/<int:user_id>/chats', methods=['GET'])
def get_user_chats_endpoint(user_id):
    try:
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        user_chats = get_user_chats(user_id)
        chats = []
        for chat in user_chats:
            participants = get_chat_participants(chat["id"])
            chat_name = get_personalized_chat_name(chat, participants, user_id)
            last_msg = get_last_message_for_chat(chat["id"])
            chats.append({
                "chat_id": chat["id"],
                "name": chat_name,
                "created_at": chat["created_at"].isoformat(),
                "updated_at": chat["updated_at"].isoformat(),
                "is_active": chat["is_active"],
                "is_admin": chat["is_admin"],
                "last_message": last_msg["content"] if last_msg else None,
                "last_message_time": last_msg["timestamp"].isoformat() if last_msg else None
            })
        return jsonify({
            "user_id": user_id,
            "chats": chats,
            "total": len(chats)
        }), 200
    except Exception as e:
        logger.error(f"Error obteniendo chats del usuario: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/chats/<chat_id>/participants', methods=['POST'])
def add_participant_to_chat(chat_id):
    try:
        data = request.json
        user_id = data.get("user_id")
        is_admin = data.get("is_admin", False)
        if not user_id:
            return jsonify({"error": "user_id es requerido"}), 400
        chat_info = get_chat_by_id(chat_id)
        if not chat_info:
            return jsonify({"error": "Chat no encontrado"}), 404
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        add_user_to_chat_in_db(user_id, chat_id, is_admin)
        return jsonify({
            "message": "Usuario agregado al chat exitosamente",
            "chat_id": chat_id,
            "user_id": user_id,
            "is_admin": is_admin
        }), 200
    except Exception as e:
        logger.error(f"Error agregando participante al chat: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/chats/<chat_id>/participants/<int:user_id>', methods=['DELETE'])
def remove_participant_from_chat(chat_id, user_id):
    try:
        chat_info = get_chat_by_id(chat_id)
        if not chat_info:
            return jsonify({"error": "Chat no encontrado"}), 404
        participants = get_chat_participants(chat_id)
        user_in_chat = any(p["id"] == user_id for p in participants)
        if not user_in_chat:
            return jsonify({"error": "Usuario no está en el chat"}), 404
        remove_user_from_chat_in_db(user_id, chat_id)
        return jsonify({
            "message": "Usuario removido del chat exitosamente",
            "chat_id": chat_id,
            "user_id": user_id
        }), 200
    except Exception as e:
        logger.error(f"Error removiendo participante del chat: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    try:
        chat_info = get_chat_by_id(chat_id)
        if not chat_info:
            return jsonify({"error": "Chat no encontrado"}), 404
        deactivate_chat_in_db(chat_id)
        return jsonify({
            "message": "Chat desactivado exitosamente",
            "chat_id": chat_id
        }), 200
    except Exception as e:
        logger.error(f"Error desactivando chat: {e}")
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
            "service": "chats-api"
        }), 200
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "service": "chats-api"
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
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
