FROM python:3.11-slim

EXPOSE 8501

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    wget xvfb unzip \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set up the Chrome PPA
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list

# Update the package list and install chrome
RUN apt-get update -y
RUN apt-get install -y google-chrome-stable

RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

RUN git clone https://github.com/jonoharms/carsales.git .

RUN pip3 install -r requirements.txt

ENTRYPOINT ["streamlit", "run", "01_🏠_Home.py", "--server.port=8501", "--server.address=0.0.0.0"]