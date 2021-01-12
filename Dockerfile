# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:3.0-python3.7-appservice
FROM mcr.microsoft.com/azure-functions/python:3.0-python3.8-appservice

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

# RUN apt-get update && apt-get install --quiet --assume-yes unzip wget
# 0. Install essential packages


RUN apt-get update \
    && apt-get install -y \
        build-essential \
        cmake \
        git \
        wget \
        unzip \
    && rm -rf /var/lib/apt/lists/*

# 1. Install Chrome (root image is debian)
# See https://stackoverflow.com/questions/49132615/installing-chrome-in-docker-file
ARG CHROME_VERSION="google-chrome-stable"
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
  && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
  && apt-get update -qqy \
  && apt-get -qqy install \
    ${CHROME_VERSION:-google-chrome-stable} \
  && rm /etc/apt/sources.list.d/google-chrome.list \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# 2. Install Chrome driver used by Selenium
RUN LATEST=$(wget -q -O - http://chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget --output-document /tmp/chromedriver_linux64.zip http://chromedriver.storage.googleapis.com/$LATEST/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver_linux64.zip -d /opt && \
    ln -s /opt/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver

ENV PATH="/usr/local/bin/chromedriver:${PATH}"

# 3. Install selenium in Python
# RUN pip install -U selenium
RUN pip install -U playwright
# RUN pip install -U pyppeteer


COPY requirements.txt /
RUN pip install -r /requirements.txt

RUN python -m playwright install

COPY . /home/site/wwwroot

RUN cd /home/site/wwwroot && /bin/bash

RUN apt update \
    && apt-get install -y \
        cabextract



RUN #!/bin/bash \
  [ ! -f /usr/share/fonts/truetype/msttcorefonts/tahoma.ttf -o ! -f /usr/share/fonts/truetype/msttcorefonts/tahomabd.ttf ]

RUN wget https://sourceforge.net/projects/corefonts/files/OldFiles/IELPKTH.CAB 

RUN cabextract -F 'tahoma*ttf' IELPKTH.CAB

RUN mkdir -p /usr/share/fonts/truetype/msttcorefonts/

RUN mv -f tahoma*ttf /usr/share/fonts/truetype/msttcorefonts/

RUN chmod 644 /usr/share/fonts/truetype/msttcorefonts/tahoma*

RUN fc-cache -v
RUN rm -f IELPKTH.CAB
RUN echo "Installed Tahoma"

EXPOSE 2222 80 8888
