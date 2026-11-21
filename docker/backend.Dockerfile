FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.3.0 \
    && pip install --no-cache-dir -r requirements.txt bcrypt==4.0.1
COPY backend/ backend/
COPY database/ database/
COPY ml/ ml/
RUN mkdir -p database/data ml/checkpoints
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
