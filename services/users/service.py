from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import bcrypt
import re
from datetime import datetime
import logging
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

def validate_password_strength(password):
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe contener al menos una letra mayúscula"
    
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe contener al menos una letra minúscula"
    
    if not re.search(r"\d", password):
        return False, "La contraseña debe contener al menos un número"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "La contraseña debe contener al menos un carácter especial"
    
    return True, "Contraseña válida"

def hash_password(password):
    if isinstance(password, bytes):
        password = password.decode('utf-8')
    salt = bcrypt.gensalt()
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def get_user_by_username(username):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, username, password_hash, first_name, last_name, 
                   email, is_active, created_at, last_login
            FROM users 
            WHERE username = %s
        """, (username,))
        row = cur.fetchone()
        cur.close()
        return row
    except Exception as e:
        logger.error(f"Error en get_user_by_username: {e}")
        return None
    finally:
        if conn:
            return_db_connection(conn)

def get_user_by_id(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, username, first_name, last_name, 
                   email, is_active, created_at, last_login
            FROM users 
            WHERE id = %s
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

def get_all_users():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, username, first_name, last_name, 
                   email, is_active, created_at, last_login
            FROM users 
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        logger.error(f"Error en get_all_users: {e}")
        return []
    finally:
        if conn:
            return_db_connection(conn)

def create_user_in_db(username, password, first_name, last_name, email):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        password_hash = hash_password(password)
        
        cur.execute("""
            INSERT INTO users (username, password_hash, first_name, last_name, email, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (username, password_hash, first_name, last_name, email, True, datetime.utcnow()))
        
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        
        logger.info(f"Usuario creado exitosamente: {username} (ID: {user_id})")
        return user_id
        
    except psycopg2.IntegrityError as e:
        logger.error(f"Error de integridad en create_user_in_db: {e}")
        if conn:
            conn.rollback()
        raise ValueError("El usuario o email ya existe")
    except Exception as e:
        logger.error(f"Error en create_user_in_db: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            return_db_connection(conn)

def activate_user_in_db(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE users 
            SET is_active = true 
            WHERE id = %s
        """, (user_id,))
        conn.commit()
        cur.close()
        logger.info(f"Usuario activado: ID {user_id}")
    except Exception as e:
        logger.error(f"Error en activate_user_in_db: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            return_db_connection(conn)

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "Users API - Servicio de gestión de usuarios",
        "version": "1.0.0",
        "endpoints": [
            "GET /users - Listar todos los usuarios",
            "GET /users/<user_id> - Obtener usuario por ID",
            "POST /register - Registrar nuevo usuario",
            "POST /users/<user_id>/activate - Activar usuario",
            "GET /health - Health check"
        ]
    })

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        
        username = data.get("username", "").strip()
        password = data.get("password", "")
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        email = data.get("email", "").strip()

        if not all([username, password, first_name, last_name, email]):
            return jsonify({"error": "Todos los campos son requeridos"}), 400

        if len(username) < 3:
            return jsonify({"error": "El nombre de usuario debe tener al menos 3 caracteres"}), 400

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({"error": "Email inválido"}), 400

        is_valid, message = validate_password_strength(password)
        if not is_valid:
            return jsonify({"error": message}), 400

        existing_user = get_user_by_username(username)
        if existing_user:
            return jsonify({"error": "El nombre de usuario ya está en uso"}), 409

        user_id = create_user_in_db(username, password, first_name, last_name, email)
        
        user_data = get_user_by_id(user_id)
        
        return jsonify({
            "message": "Usuario registrado exitosamente",
            "user": {
                "id": user_data["id"],
                "username": user_data["username"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "email": user_data["email"],
                "is_active": user_data["is_active"],
                "created_at": user_data["created_at"].isoformat() if user_data["created_at"] else None
            }
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        logger.error(f"Error en registro: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user_data = get_user_by_id(user_id)
        
        if not user_data:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        return jsonify({
            "user": {
                "id": user_data["id"],
                "username": user_data["username"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "email": user_data["email"],
                "is_active": user_data["is_active"],
                "created_at": user_data["created_at"].isoformat() if user_data["created_at"] else None,
                "last_login": user_data["last_login"].isoformat() if user_data["last_login"] else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo usuario: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/users', methods=['GET'])
def list_all_users():
    try:
        users_data = get_all_users()
        
        users = []
        for user_data in users_data:
            users.append({
                "id": user_data["id"],
                "username": user_data["username"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "email": user_data["email"],
                "is_active": user_data["is_active"],
                "created_at": user_data["created_at"].isoformat() if user_data["created_at"] else None,
                "last_login": user_data["last_login"].isoformat() if user_data["last_login"] else None
            })
        
        return jsonify({
            "users": users,
            "total": len(users)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listando usuarios: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/users/<int:user_id>/activate', methods=['POST'])
def activate(user_id):
    try:
        user_data = get_user_by_id(user_id)
        if not user_data:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        activate_user_in_db(user_id)
        
        return jsonify({
            "message": "Usuario activado exitosamente",
            "user_id": user_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error activando usuario: {e}")
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
            "service": "users-api"
        }), 200
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "service": "users-api"
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
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
