FROM python:3.11-slim

WORKDIR /code

RUN mkdir /code/src
COPY LICENSE README.md pyproject.toml setup.py ./
COPY src /code/src
RUN pip install --no-cache-dir .

CMD ["python", "-u", "-m", "internal-acme-dns"]
