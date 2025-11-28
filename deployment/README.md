# Deployment

Deploy the project on a Linux server (Ubuntu) with Docker and Nginx.

## Prerequisites

- [Docker](https://www.docker.com/get-started/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Nginx](https://nginx.org/)

## 1. Run the project with Docker

### 1.1 Download the project

```bash
git clone git@github.com:birongliu/investorly.git
```

### 1.2 Set up environment variables

Create the .env file in backend/ and set environment variables:

```
GROQ_TOKEN=[your_groq_token]
```

### 1.3 Build and run the project

```bash
# Build images
docker compose build

# Run containers in the background
docker compose up -d

# Stop containers
docker compose down
```


## 2. Configure Nginx as a reverse proxy

Check the [nginx-config.md](nginx-config.md) to set up Nginx as a reverse proxy.
