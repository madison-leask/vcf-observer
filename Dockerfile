FROM python:3.10

RUN pip install --upgrade pip

COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir --upgrade -r /requirements.txt

COPY ./requirements-deployment.txt /requirements-deployment.txt
RUN pip install --no-cache-dir --upgrade -r /requirements-deployment.txt

COPY ./app /app

WORKDIR /app

CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--timeout", "600", "app:server"]
