FROM python:3

WORKDIR /plane-notify

COPY . .

# Add pipenv
RUN pip install pipenv==2021.5.29

# Install dependencies
RUN pipenv install

# Added needed folder for plane-notify process
RUN mkdir /var/run/plane-notify

CMD pipenv run python /plane-notify/__main__.py
