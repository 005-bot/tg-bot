# Build stage
FROM python:3.11-slim as builder

# Set the working directory in the container
WORKDIR /usr/src

# Install system dependencies and Pipenv
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install pipenv

ENV PIPENV_VENV_IN_PROJECT=1

# Copy the Pipfile and Pipfile.lock into the container
COPY Pipfile Pipfile.lock ./

# Install project dependencies
RUN pipenv install --dev --deploy

# Final stage
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install timezone data and locales
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    locales \
    && rm -rf /var/lib/apt/lists/* \
    && echo "ru_RU.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && locale-gen ru_RU.UTF-8 \
    && locale-gen en_US.UTF-8 \
    && update-locale

ENV TZ=Asia/Krasnoyarsk

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False

# Copy only the necessary files from the builder stage
COPY --from=builder /usr/src/.venv/ /app/.venv/

# Copy the project files into the container
COPY . .

# Set the entrypoint command
CMD ["/app/.venv/bin/python", "-m", "app"]
