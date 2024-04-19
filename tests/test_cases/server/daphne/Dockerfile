ARG PYTHON_VERSION=xxx

FROM python:${PYTHON_VERSION}-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /code

WORKDIR /code

COPY requirements.txt /tmp/requirements.txt
RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/
COPY . /code

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "daphne_app.asgi:application"]
