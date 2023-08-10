FROM python:3.11

ENV DEBIAN_FRONTEND noninteractive
ENV GECKODRIVER_VER v0.32.0
ENV FIREFOX_VER 108.0

EXPOSE 8501

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    git \
    firefox-esr\
    && rm -rf /var/lib/apt/lists/*

# Add latest FireFox
RUN set -x \
    && apt install -y \
    libx11-xcb1 \
    libdbus-glib-1-2 \
    && curl -sSLO https://download-installer.cdn.mozilla.net/pub/firefox/releases/${FIREFOX_VER}/linux-x86_64/en-US/firefox-${FIREFOX_VER}.tar.bz2 \
    && tar -jxf firefox-* \
    && mv firefox /opt/ \
    && chmod 755 /opt/firefox \
    && chmod 755 /opt/firefox/firefox

# Add geckodriver
RUN set -x \
    && curl -sSLO https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VER}/geckodriver-${GECKODRIVER_VER}-linux64.tar.gz \
    && tar zxf geckodriver-*.tar.gz \
    && mv geckodriver /usr/bin/

RUN git clone https://github.com/jonoharms/carsales.git

RUN pip3 install -r carsales/requirements.txt

WORKDIR /app/carsales

# ENTRYPOINT ["streamlit", "run", "carsales/01_🏠_Home.py", "--server.port", ${PORT}, "--server.address", "0.0.0.0"]
CMD ["sh", "-c", "streamlit run --server.port $PORT --server.address 0.0.0.0 01_🏠_Home.py"]