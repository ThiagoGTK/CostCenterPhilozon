FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc \
    unixodbc-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# TODO: Instalar driver Firebird ODBC (IBPhoenix ou Firebird Project)
# RUN apt-get install -y firebird-dev ...

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Por padrão, executa o pipeline do mês atual
CMD ["python", "pipeline.py"]
