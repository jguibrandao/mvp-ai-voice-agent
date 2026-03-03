FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ agent/
COPY main.py api.py agent_config.json ./

RUN python main.py download-files

EXPOSE 8001

CMD ["python", "api.py"]
