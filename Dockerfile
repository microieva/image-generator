FROM python:3.9

# Install prerequisites
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft repository using modern approach (without apt-key)
RUN mkdir -p /etc/apt/keyrings \
    && wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list

# Install SQL Server drivers
RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get install -y unixodbc unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY .env .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]