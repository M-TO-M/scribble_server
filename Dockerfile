FROM python:3.10.2-slim

RUN mkdir /app

ADD requirements.txt /app/requirements.txt

ADD . /app
WORKDIR /app

RUN set -ex \
    && python -m venv /env \
    && /env/bin/pip install --upgrade pip \
    && /env/bin/pip install --no-cache-dir -r /app/requirements.txt \
    && /env/bin/pip install gunicorn

ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

RUN ["chmod", "+x", "start.sh"]
ENTRYPOINT ["sh", "./start.sh"]
