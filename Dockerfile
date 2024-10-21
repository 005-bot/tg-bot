# Build stage
FROM python:3.11-alpine as builder

# Set the working directory in the container
WORKDIR /usr/src

# Install Git
RUN apk add --no-cache git

# Install system dependencies and Pipenv
RUN pip install pipenv

ENV PIPENV_VENV_IN_PROJECT=1

# Copy the Pipfile and Pipfile.lock into the container
COPY Pipfile Pipfile.lock ./

# Install project dependencies
RUN pipenv install --dev --deploy

# Final stage
FROM python:3.11-alpine

# Set the working directory in the container
WORKDIR /app

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
