from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os
import logging
import asyncio
import json
import random
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import threading
import time

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Models
class NetworkNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # server, router, switch, workstation
    ip_address: str
    status: str = "online"  # online, offline, warning, critical
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_latency: float = 0.0
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    location: Dict[str, float] = {"x": 0, "y": 0}

class NetworkAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_id: str
    alert_type: str  # connectivity, performance, security
    severity: str  # low, medium, high, critical
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    ai_analysis: Optional[str] = None

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    response: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DiagnosisRequest(BaseModel):
    query: str
    context: Optional[Dict] = None

# AI Chat instance
llm_chat = LlmChat(
    api_key=os.environ.get('EMERGENT_LLM_KEY'),
    session_id="network_monitor_session",
    system_message="""You are an expert network monitoring AI assistant specializing in enterprise network diagnosis and troubleshooting. 

Your capabilities include:
1. Analyzing network performance metrics (CPU, memory, disk, latency)
2. Diagnosing connectivity issues and root cause analysis
3. Identifying security threats and anomalies
4. Providing actionable remediation steps
5. Explaining complex network issues in clear, natural language

When analyzing network data:
- Consider the relationships between nodes and their dependencies
- Look for patterns that indicate systemic issues
- Prioritize critical alerts over minor performance variations
- Provide specific, actionable recommendations
- Explain technical concepts in accessible terms

Always be concise but thorough in your analysis and recommendations."""
).with_model("openai", "gpt-4o")

# Network simulation data
NETWORK_NODES = [
    {"name": "Core Router", "type": "router", "ip": "192.168.1.1", "location": {"x": 400, "y": 200}},
    {"name": "Web Server 1", "type": "server", "ip": "192.168.1.10", "location": {"x": 200, "y": 100}},
    {"name": "Web Server 2", "type": "server", "ip": "192.168.1.11", "location": {"x": 600, "y": 100}},
    {"name": "Database Server", "type": "server", "ip": "192.168.1.20", "location": {"x": 400, "y": 50}},
    {"name": "Load Balancer", "type": "server", "ip": "192.168.1.5", "location": {"x": 400, "y": 150}},
    {"name": "Switch 1", "type": "switch", "ip": "192.168.1.2", "location": {"x": 200, "y": 250}},
    {"name": "Switch 2", "type": "switch", "ip": "192.168.1.3", "location": {"x": 600, "y": 250}},
    {"name": "Workstation 1", "type": "workstation", "ip": "192.168.1.50", "location": {"x": 100, "y": 300}},
    {"name": "Workstation 2", "type": "workstation", "ip": "192.168.1.51", "location": {"x": 300, "y": 300}},
    {"name": "Firewall", "type": "security", "ip": "192.168.1.254", "location": {"x": 400, "y": 350}},
]

# Global variables for simulation
network_nodes = {}
is_simulation_running = False

async def initialize_network():
    """Initialize network nodes in database"""
    global network_nodes
    
    for node_data in NETWORK_NODES:
        node = NetworkNode(
            name=node_data["name"],
            type=node_data["type"],
            ip_address=node_data["ip"],
            location=node_data["location"],
            cpu_usage=random.uniform(10, 30),
            memory_usage=random.uniform(20, 40),
            disk_usage=random.uniform(15, 35),
            network_latency=random.uniform(1, 5)
        )
        
        # Store in memory for simulation
        network_nodes[node.id] = node
        
        # Store in database
        await db.network_nodes.replace_one(
            {"ip_address": node.ip_address},
            node.dict(),
            upsert=True
        )

def simulate_network_metrics():
    """Generate realistic network metrics with occasional issues"""
    global network_nodes
    
    for node_id, node in network_nodes.items():
        # Base metrics with random variation
        node.cpu_usage = max(0, min(100, node.cpu_usage + random.uniform(-5, 5)))
        node.memory_usage = max(0, min(100, node.memory_usage + random.uniform(-3, 3)))
        node.disk_usage = max(0, min(100, node.disk_usage + random.uniform(-1, 1)))
        node.network_latency = max(0.1, node.network_latency + random.uniform(-1, 1))
        
        # Simulate occasional issues
        if random.random() < 0.05:  # 5% chance of issues
            issue_type = random.choice(["cpu_spike", "memory_leak", "network_congestion", "disk_full"])
            
            if issue_type == "cpu_spike":
                node.cpu_usage = min(100, node.cpu_usage + random.uniform(20, 40))
            elif issue_type == "memory_leak":
                node.memory_usage = min(100, node.memory_usage + random.uniform(15, 30))
            elif issue_type == "network_congestion":
                node.network_latency = node.network_latency + random.uniform(10, 50)
            elif issue_type == "disk_full":
                node.disk_usage = min(100, node.disk_usage + random.uniform(10, 20))
        
        # Update status based on metrics
        if node.cpu_usage > 90 or node.memory_usage > 95 or node.disk_usage > 95:
            node.status = "critical"
        elif node.cpu_usage > 70 or node.memory_usage > 80 or node.disk_usage > 80:
            node.status = "warning"
        elif random.random() < 0.02:  # 2% chance of offline
            node.status = "offline"
        else:
            node.status = "online"
        
        node.last_seen = datetime.now(timezone.utc)

async def generate_alerts():
    """Generate alerts based on network conditions"""
    global network_nodes
    
    for node_id, node in network_nodes.items():
        alerts = []
        
        # Performance alerts
        if node.cpu_usage > 85:
            alert = NetworkAlert(
                node_id=node_id,
                alert_type="performance",
                severity="high" if node.cpu_usage > 95 else "medium",
                message=f"High CPU usage on {node.name}: {node.cpu_usage:.1f}%"
            )
            alerts.append(alert)
        
        if node.memory_usage > 90:
            alert = NetworkAlert(
                node_id=node_id,
                alert_type="performance",
                severity="critical" if node.memory_usage > 98 else "high",
                message=f"High memory usage on {node.name}: {node.memory_usage:.1f}%"
            )
            alerts.append(alert)
        
        if node.network_latency > 100:
            alert = NetworkAlert(
                node_id=node_id,
                alert_type="connectivity",
                severity="high",
                message=f"High network latency on {node.name}: {node.network_latency:.1f}ms"
            )
            alerts.append(alert)
        
        # Connectivity alerts
        if node.status == "offline":
            alert = NetworkAlert(
                node_id=node_id,
                alert_type="connectivity",
                severity="critical",
                message=f"Node {node.name} is offline"
            )
            alerts.append(alert)
        
        # Security alerts (random simulation)
        if random.random() < 0.01 and node.type in ["server", "firewall"]:
            alert = NetworkAlert(
                node_id=node_id,
                alert_type="security",
                severity="medium",
                message=f"Suspicious activity detected on {node.name}"
            )
            alerts.append(alert)
        
        # Store alerts in database
        for alert in alerts:
            await db.network_alerts.insert_one(alert.dict())

async def simulation_loop():
    """Main simulation loop"""
    global is_simulation_running
    
    while is_simulation_running:
        try:
            # Update metrics
            simulate_network_metrics()
            
            # Generate alerts
            await generate_alerts()
            
            # Update database
            for node_id, node in network_nodes.items():
                await db.network_nodes.replace_one(
                    {"id": node_id},
                    node.dict(),
                    upsert=True
                )
            
            # Broadcast updates to connected clients
            network_data = {
                "type": "network_update",
                "nodes": [node.dict() for node in network_nodes.values()],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await manager.broadcast(json.dumps(network_data))
            
            # Wait before next update
            await asyncio.sleep(2)  # Update every 2 seconds
            
        except Exception as e:
            logging.error(f"Simulation error: {e}")
            await asyncio.sleep(5)

# Routes
@api_router.get("/")
async def root():
    return {"message": "Network Monitoring AI Assistant API"}

@api_router.get("/nodes", response_model=List[NetworkNode])
async def get_network_nodes():
    nodes = await db.network_nodes.find().to_list(1000)
    return [NetworkNode(**node) for node in nodes]

@api_router.get("/alerts", response_model=List[NetworkAlert])
async def get_network_alerts():
    alerts = await db.network_alerts.find({"resolved": False}).sort("timestamp", -1).to_list(100)
    return [NetworkAlert(**alert) for alert in alerts]

@api_router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    result = await db.network_alerts.update_one(
        {"id": alert_id},
        {"$set": {"resolved": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert resolved"}

@api_router.post("/diagnosis")
async def diagnose_issue(request: DiagnosisRequest):
    try:
        # Get current network state
        nodes = await db.network_nodes.find().to_list(1000)
        alerts = await db.network_alerts.find({"resolved": False}).sort("timestamp", -1).to_list(20)
        
        # Prepare context for AI
        context = f"""
Current Network Status:
Nodes: {len(nodes)} total
Active Alerts: {len(alerts)}

Recent Network Metrics:
"""
        
        for node in nodes[:10]:  # Show top 10 nodes
            context += f"- {node['name']} ({node['type']}): Status={node['status']}, CPU={node['cpu_usage']:.1f}%, Memory={node['memory_usage']:.1f}%, Latency={node['network_latency']:.1f}ms\n"
        
        if alerts:
            context += "\nActive Alerts:\n"
            for alert in alerts[:5]:  # Show top 5 alerts
                context += f"- {alert['message']} (Severity: {alert['severity']})\n"
        
        # Add user's context if provided
        if request.context:
            context += f"\nAdditional Context: {json.dumps(request.context)}\n"
        
        # Query the AI
        full_query = f"{context}\n\nUser Query: {request.query}\n\nPlease provide a detailed analysis and recommendations."
        
        user_message = UserMessage(text=full_query)
        response = await llm_chat.send_message(user_message)
        
        # Store chat history
        chat_message = ChatMessage(
            message=request.query,
            response=response
        )
        await db.chat_history.insert_one(chat_message.dict())
        
        return {"response": response}
        
    except Exception as e:
        logging.error(f"Diagnosis error: {e}")
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")

@api_router.get("/chat/history", response_model=List[ChatMessage])
async def get_chat_history():
    history = await db.chat_history.find().sort("timestamp", -1).to_list(50)
    return [ChatMessage(**msg) for msg in history]

@api_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now - could handle real-time queries
            await manager.send_personal_message(f"Received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@api_router.post("/simulation/start")
async def start_simulation():
    global is_simulation_running
    if not is_simulation_running:
        is_simulation_running = True
        await initialize_network()
        asyncio.create_task(simulation_loop())
        return {"message": "Network simulation started"}
    return {"message": "Simulation already running"}

@api_router.post("/simulation/stop")
async def stop_simulation():
    global is_simulation_running
    is_simulation_running = False
    return {"message": "Network simulation stopped"}

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Start the simulation when the app starts"""
    global is_simulation_running
    if not is_simulation_running:
        is_simulation_running = True
        await initialize_network()
        asyncio.create_task(simulation_loop())
        logger.info("Network simulation started automatically")

@app.on_event("shutdown")
async def shutdown_db_client():
    global is_simulation_running
    is_simulation_running = False
    client.close()