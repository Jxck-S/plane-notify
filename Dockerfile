FROM python:3.14

WORKDIR /plane-notify

# Added needed folder for plane-notify process
RUN mkdir /home/plane-notify

# Set the Chrome repo.
RUN wget -q -O /usr/share/keyrings/google-chrome.asc https://dl-ssl.google.com/linux/linux_signing_key.pub \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.asc] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Install Chrome.
RUN apt-get update && apt-get -y install --no-install-recommends \
    google-chrome-stable \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add pipenv
RUN pip install pipenv

# Install dependencies
COPY Pipfile* .
RUN pipenv install --deploy

COPY . .
CMD pipenv run python /plane-notify/__main__.py
