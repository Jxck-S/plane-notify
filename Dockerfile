FROM python:3

WORKDIR /plane-notify

# Added needed folder for plane-notify process
RUN mkdir /home/plane-notify

# Set the Chrome repo.
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list

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
RUN pipenv install

COPY . .
CMD pipenv run python /plane-notify/__main__.py
