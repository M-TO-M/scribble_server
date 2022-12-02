FROM python:3.10.2-slim

ARG WORKING_DIR
RUN echo $WORKING_DIR
RUN mkdir /$WORKING_DIR

ADD requirements.txt /$WORKING_DIR/requirements.txt

ADD . /$WORKING_DIR
WORKDIR /$WORKING_DIR

RUN set -ex \
    && python -m venv /env \
    && /env/bin/pip install --upgrade pip \
    && /env/bin/pip install --no-cache-dir -r /$WORKING_DIR/requirements.txt \
    && /env/bin/pip install gunicorn

ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

ARG PORT

RUN ["chmod", "+x", "./scripts/backend.sh"]
ENV WORKING_DIR ${WORKING_DIR}
ENV PORT ${PORT}
CMD ["./scripts/backend.sh"]
