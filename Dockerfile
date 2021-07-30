FROM python:3

WORKDIR /plane-notify

COPY . .

# Set the Chrome repo.
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list

# Install Chrome.
RUN apt-get update && apt-get -y install google-chrome-stable

# Add pipenv
RUN pip install pipenv==2021.5.29

# Install dependencies
RUN pipenv install

# Added needed folder for plane-notify process
RUN mkdir  /home/plane-notify

CMD pipenv run python /plane-notify/__main__.py