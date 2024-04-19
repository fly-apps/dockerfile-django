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

ENV SECRET_KEY #s2%hf!exrt3q9z=oc$xytk429g#jdug#xoc!8t%c$2&i2kd#9
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "collectstatic_app.wsgi"]
