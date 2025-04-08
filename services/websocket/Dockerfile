# Usa una imagen base de Python
FROM python:3.9-slim

# Crea un directorio de trabajo
WORKDIR /app

# Copia los archivos requirements y los instala
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . /app/

# Expone el puerto 5000 (el contenedor escuchará en este puerto)
EXPOSE 5000

# Ejecuta el servidor WebSocket con uvicorn, haciendo que escuche en todas las interfaces en el puerto 5000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
