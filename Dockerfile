FROM python:3

WORKDIR /plane-notify
USER root 

COPY . .

RUN set -ex && \
    apt-get update -qq && \
    apt-get -y -qq install --no-install-recommends \
      ca-certificates \
      gnupg && \
    curl -sSL https://dl-ssl.google.com/linux/linux_signing_key.pub  | apt-key add -  && \ 
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list && \
    apt-get -y -qq update \
    && apt-get -y -qq install --no-install-recommends \
        bash \
        curl \
        google-chrome-stable \
        python3 \
        python3-dev \
        python3-pip \
        python3-setuptools \
        python3-wheel \
    && rm -rf \
     /var/lib/apt/lists/* \
     /var/cache/apt/archives



# Add pipenv
RUN pip install pipenv==2021.5.29

# Install dependencies
RUN pipenv install

# Added needed folder for plane-notify process
RUN mkdir  /home/plane-notify

CMD pipenv run python /plane-notify/__main__.py