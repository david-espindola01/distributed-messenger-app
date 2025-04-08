# UPTC Messenger

UPTC Messenger es una red de mensajería distribuida desarrollada como proyecto para la materia de Sistemas Distribuidos. Esta plataforma está diseñada para facilitar la comunicación en tiempo real entre los usuarios, integrando servicios de autenticación, gestión de chats, envío de mensajes y conexión mediante websockets.

## Integrantes

- **David Leonardo Espindola**
- **Juan David Muñoz**
- **Edwin David Martinez**

## Características

- **Comunicación en tiempo real:** Implementación de websockets para envíos y recepciones inmediatas.
- **Autenticación y gestión de usuarios:** Módulos dedicados para manejar el acceso y la seguridad de la aplicación.
- **Manejo de chats y mensajes:** Soporte para conversaciones en grupo y privadas.
- **Arquitectura distribuida:** Enfocada en la escalabilidad y eficiencia de los servicios.
- **Entorno Python:** Desarrollo y ejecución en un entorno virtual (.venv) para la gestión de dependencias.


### Descripción de Carpetas

- **controllers:**  
  Lógica para el manejo de las solicitudes y respuestas del servidor.

- **database:**  
  Configuraciones y scripts dedicados a la conexión e interacción con la base de datos.

- **models:**  
  Definiciones de estructuras de datos utilizadas en la aplicación.

- **public:**  
  Recursos estáticos de la aplicación, como archivos, imágenes y otros.

- **services:**  
  Componentes que gestionan la lógica de negocio específica:
  - **auth:** Módulo de autenticación y autorización.
  - **chats:** Gestión de salas de chat y administración de conversaciones.
  - **messages:** Procesamiento y envío de mensajes.
  - **users:** Manejo de información y perfiles de usuario.
  - **websocket:** Implementación de la comunicación en tiempo real a través de websockets.

## Requisitos del Sistema

- **Python 3.x**: Se recomienda usar Python 3 para asegurar la compatibilidad.
- **Pip:** Para la instalación de dependencias.
- **Entorno Virtual:** Se recomienda el uso de un entorno virtual para aislar las dependencias del proyecto (ya se incluye la carpeta `.venv`).
