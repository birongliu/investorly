# Investorly

Investorly is an investment portfolio dashboard, which aims to empower beginner investors who may feel overwhelmed by complex financial language and uncertain about where to start.

Investorly provides a clear, beginner-friendly dashboard that simplifies investing, builds confidence, and turns learning about finance into an approachable experience.

![Investorly Dashboard](https://github.com/user-attachments/assets/0fa3e93e-c681-4a70-8076-1dcaf4a1167c)

## Tech Stack

![Tech Stack](https://github.com/user-attachments/assets/5249cf14-4076-45d1-af60-be6afb59fd61)

## Contributions

Please review the [Contributing Guidelines](CONTRIBUTING.md) for more information.

## Run the Project (with Docker)

### 1. Install Docker
https://www.docker.com/

### 2. Build and run the project

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
