FROM python:3.7-slim-buster

COPY install-packages.sh .
RUN ./install-packages.sh

RUN useradd lsmoler

WORKDIR /home/lsmoler

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./colorcalibrator  ./colorcalibrator
COPY app.py .
COPY logging.conf .
COPY gunicorn_conf.py .

RUN chown -R lsmoler:lsmoler ./

USER lsmoler

CMD gunicorn -b 0.0.0.0:$PORT -c gunicorn_conf.py --log-config logging.conf app:server
