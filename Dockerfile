FROM python:3.10.2-slim

RUN mkdir /${HOME}

ADD requirements.txt /${HOME}/requirements.txt

ADD . /${HOME}
WORKDIR /${HOME}

RUN set -ex \
    && python -m venv /env \
    && /env/bin/pip install --upgrade pip \
    && /env/bin/pip install --no-cache-dir -r /${HOME}/requirements.txt \
    && /env/bin/pip install gunicorn

ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

RUN ["chmod", "+x", "scripts/${SCRIPT_FILENAME}"]
ENTRYPOINT ["sh", "./scripts/${SCRIPT_FILENAME}"]
