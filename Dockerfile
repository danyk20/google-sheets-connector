FROM python:3.11-slim
ARG ENVIRONMENT

WORKDIR /usr/src/app

# upgrade to latest pip
RUN pip install --upgrade pip

# install system dependencies
RUN apt-get update && \
    apt-get install -y git curl && \
    rm -rf /var/lib/apt/lists/*

# Install workflows-cdk package
RUN pip install git+https://github.com/stacksyncdata/workflows-cdk.git@prod

# install dependencies
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

# copy the scripts
COPY . .

# expose port
EXPOSE 8080

# make the entrypoint executable
RUN chmod +x ./entrypoint.sh

# run the entrypoint to start the Gunicorn server
ENTRYPOINT ["sh", "entrypoint.sh"]
