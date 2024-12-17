# Usa una imagen base de Python
FROM python:3.12.6-slim

# Establece el directorio de trabajo
WORKDIR /app

# Crea y activa el entorno virtual
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copia solo requirements.txt primero
COPY requirements.txt .

# Instala dependencias de Python en el entorno virtual
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del proyecto
COPY . .

# Expone el puerto
EXPOSE 3000

# Instala Gunicorn
RUN pip install gunicorn

# Comando para ejecutar la aplicación con Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3000", "app:app"]
