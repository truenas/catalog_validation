FROM python:3.8.6-slim-buster

ENV PYTHONUNBUFFERED 1
ENV WORK_DIR /app
RUN mkdir -p ${WORK_DIR}
WORKDIR ${WORK_DIR}

# install our app requirements
ADD requirements.txt ${WORK_DIR}
RUN pip install --disable-pip-version-check --exists-action w -r requirements.txt && \
    rm -rf ~/.cache/pip /tmp/pip-build-root

ADD . ${WORK_DIR}/
RUN pip install -U .
