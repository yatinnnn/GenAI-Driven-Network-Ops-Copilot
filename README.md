# GenAI-Driven-Network-Ops-Copilot

GenAI-Driven-Network-Ops-Copilot is an AI-powered tool designed to enhance **network operations** by providing intelligent insights, automation, and monitoring capabilities.  
The project includes a **backend service**, a **frontend interface**, and **automated tests** for reliable deployment.

---

## 🚀 Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/yatinnnn/GenAI-Driven-Network-Ops-Copilot.git
cd GenAI-Driven-Network-Ops-Copilot
```
Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Frontend Setup

```bash
cd frontend
npm install
```

⚙️ Environment Variables
Create a .env.local file in the root directory and add:

```bash
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL=your-database-url
REDIS_URL=your-redis-url
NEXT_PUBLIC_API_URL=http://localhost:8000
```

🖥️ Running Locally
Backend

```bash
cd backend
python main.py
```
Frontend

```bash
cd frontend
npm run dev
```

🐳 Run using Docker
Build and run the application with Docker:


```bash
# Build image
docker build -t network-copilot .

# Run container
docker run -p 3000:3000 --env-file .env network-copilot
```

📌 Usage
The application offers the following features:

AI-Powered Insights – Get real-time suggestions for network optimization.

Incident Automation – Automate troubleshooting and recovery.

Monitoring Dashboard – Visualize logs, alerts, and performance metrics.

Integration Support – Connect with APIs, databases, and cloud systems.

✨ Key Features
Intelligent incident detection and resolution.

Real-time analytics for network health.

Secure user authentication.

Extendable backend with modular services.

🧪 Testing
Run tests with:

```bash
pytest tests/
```
