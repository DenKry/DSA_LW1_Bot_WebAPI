# DSA_LW1_Bot_WebAPI

Laboratory Work 1 — **Distributed Systems and Algorithms**

## Overview
This project implements a **Web API** that integrates with **Azure Bot Service**.  
The API handles job creation, message routing to the Azure bot, and state management between client requests.

## Structure
```
src/
├── app.py              # FastAPI main application
├── models.py           # Pydantic models (Job, NewJob, State)
├── service.py          # Azure Bot Service call logic
├── store_rate_limit.py # Rate limiting and job storage
└── config.py           # Environment variable setup
```

## How to run
1. Create `.env` file:
MicrosoftAppId=<your_bot_app_id>
MicrosoftAppPassword=<your_bot_password>

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start server:
```bash
python app.py
```

4. Open Swagger docs: http://127.0.0.1:8081/docs