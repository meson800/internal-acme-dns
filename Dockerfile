FROM python:3.11-slim

WORKDIR /code

RUN mkdir src
COPY LICENSE README.md .
COPY setup.py setup.py
COPY src src
RUN pip install --no-cache-dir .

CMD ["python", "-m", "local-acme-dns"]
