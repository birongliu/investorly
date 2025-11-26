# Investorly

Investorly — An investment portfolio dashboard for beginners to learn investing.

![Investorly Dashboard](https://github.com/user-attachments/assets/fac1c10b-511b-43a0-8e44-1af07b427b15)

## Tech Stack

- Frontend/UI:
  - Streamlit
- Backend/API:
  - Python
  - Flask
  - LLM
- Deployment:
  - Docker
  - Linux
  - Nginx

## Contributions

Please review the [Contributing Guidelines](CONTRIBUTING.md) for more information.

## Run the Project (with Docker)

### 1. Set up environment variables

Create the .env file in backend/ and set environment variables:

```
GROQ_TOKEN=[your_groq_token]
```

### 2. Install Docker
https://www.docker.com/

### 3. Build and run the project

```bash
# Build images
docker compose build

# Run containers
docker compose up
```

```bash
# Run containers in the background
docker compose up -d

# Stop containers
docker compose down
```

## Run the Project (without Docker)

### 1. Install dependencies
```
# create and activate a virtual environment (macOS/Linux)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the backend

1. Create the .env file in backend/ and set environment variables:

```
GROQ_TOKEN=[your_groq_token]
```

2. Run the backend server:
```bash
python ./backend/app.py
```

### 3. Run the frontend

```bash
streamlit run ./frontend/app.py
```
