FROM python:3.8

ENV OPENAI_API_BASE "https://api.openai-proxy.com/v1"

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]