FROM python:3.8-alpine

COPY requirements.txt .

RUN apk add --no-cache gcc musl-dev && \
    pip3 install --no-cache-dir -r requirements.txt && \
    apk del gcc musl-dev

COPY . .

ENTRYPOINT ["python3" , "main.py"]
