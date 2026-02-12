FROM python:3.11

# Crear carpeta de trabajo
WORKDIR /code

# Copiar todos los archivos desde ./calendarios_procesos al contenedor
COPY . .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y gnupg curl unixodbc-dev gcc g++ && \
    mkdir -p /etc/apt/keyrings && \
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg && \
    echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Muy importante: añadir /code al PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/code"

# Y ejecutar uvicorn indicando el punto de entrada correcto
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8022", "--reload"]
