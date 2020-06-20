FROM python:3.7-slim-buster

COPY install_packages.sh .
RUN ./install_packages.sh

RUN useradd lsmoler

WORKDIR /home/lsmoler

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./colorcalibrator  ./colorcalibrator
COPY run_app.py .
COPY logging.conf .
COPY config.py .
COPY gunicorn_conf.py .

RUN chown -R lsmoler:lsmoler ./

USER lsmoler

CMD gunicorn -b 0.0.0.0:$PORT -c gunicorn_conf.py run_app:server
