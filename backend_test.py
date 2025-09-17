#!/usr/bin/env python3

import requests
import json
import time
import sys
from datetime import datetime
import websocket
import threading

class SecureWatchAPITester:
    def __init__(self, base_url="https://securewatch-11.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.ws_connected = False
        self.ws_messages = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'No message')}"
            return self.log_test("API Root", success, details)
        except Exception as e:
            return self.log_test("API Root", False, f"Error: {str(e)}")

    def test_get_nodes(self):
        """Test getting network nodes"""
        try:
            response = requests.get(f"{self.api_url}/nodes", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                nodes = response.json()
                details += f", Nodes count: {len(nodes)}"
                
                # Validate node structure
                if nodes and len(nodes) > 0:
                    node = nodes[0]
                    required_fields = ['id', 'name', 'type', 'ip_address', 'status', 'cpu_usage', 'memory_usage']
                    missing_fields = [field for field in required_fields if field not in node]
                    if missing_fields:
                        details += f", Missing fields: {missing_fields}"
                        success = False
                    else:
                        details += f", Sample node: {node['name']} ({node['type']})"
                
            return self.log_test("Get Network Nodes", success, details)
        except Exception as e:
            return self.log_test("Get Network Nodes", False, f"Error: {str(e)}")

    def test_get_alerts(self):
        """Test getting network alerts"""
        try:
            response = requests.get(f"{self.api_url}/alerts", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                alerts = response.json()
                details += f", Alerts count: {len(alerts)}"
                
                # Validate alert structure if alerts exist
                if alerts and len(alerts) > 0:
                    alert = alerts[0]
                    required_fields = ['id', 'node_id', 'alert_type', 'severity', 'message', 'timestamp']
                    missing_fields = [field for field in required_fields if field not in alert]
                    if missing_fields:
                        details += f", Missing fields: {missing_fields}"
                        success = False
                    else:
                        details += f", Sample alert: {alert['severity']} - {alert['alert_type']}"
                
            return self.log_test("Get Network Alerts", success, details)
        except Exception as e:
            return self.log_test("Get Network Alerts", False, f"Error: {str(e)}")

    def test_ai_diagnosis(self):
        """Test AI diagnosis functionality"""
        try:
            test_query = "Analyze current network performance and identify any issues"
            payload = {
                "query": test_query,
                "context": {"test": True}
            }
            
            print(f"🤖 Testing AI diagnosis with query: '{test_query}'")
            response = requests.post(f"{self.api_url}/diagnosis", 
                                   json=payload, 
                                   timeout=30)  # AI calls can take longer
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                ai_response = data.get('response', '')
                details += f", Response length: {len(ai_response)} chars"
                
                # Check if response contains meaningful content
                if len(ai_response) > 50:  # Reasonable response length
                    details += f", Sample: '{ai_response[:100]}...'"
                else:
                    details += f", Short response: '{ai_response}'"
                    if len(ai_response) < 10:
                        success = False
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"
                
            return self.log_test("AI Diagnosis", success, details)
        except Exception as e:
            return self.log_test("AI Diagnosis", False, f"Error: {str(e)}")

    def test_chat_history(self):
        """Test chat history endpoint"""
        try:
            response = requests.get(f"{self.api_url}/chat/history", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                history = response.json()
                details += f", History count: {len(history)}"
                
                # Validate history structure if history exists
                if history and len(history) > 0:
                    chat = history[0]
                    required_fields = ['id', 'message', 'response', 'timestamp']
                    missing_fields = [field for field in required_fields if field not in chat]
                    if missing_fields:
                        details += f", Missing fields: {missing_fields}"
                        success = False
                    else:
                        details += f", Latest message: '{chat['message'][:50]}...'"
                
            return self.log_test("Chat History", success, details)
        except Exception as e:
            return self.log_test("Chat History", False, f"Error: {str(e)}")

    def test_simulation_control(self):
        """Test simulation start/stop endpoints"""
        try:
            # Test start simulation
            response = requests.post(f"{self.api_url}/simulation/start", timeout=10)
            start_success = response.status_code == 200
            start_details = f"Start status: {response.status_code}"
            
            if start_success:
                data = response.json()
                start_details += f", Message: {data.get('message', 'No message')}"
            
            # Wait a moment for simulation to initialize
            time.sleep(2)
            
            # Test stop simulation
            response = requests.post(f"{self.api_url}/simulation/stop", timeout=10)
            stop_success = response.status_code == 200
            stop_details = f"Stop status: {response.status_code}"
            
            if stop_success:
                data = response.json()
                stop_details += f", Message: {data.get('message', 'No message')}"
            
            overall_success = start_success and stop_success
            details = f"{start_details} | {stop_details}"
            
            return self.log_test("Simulation Control", overall_success, details)
        except Exception as e:
            return self.log_test("Simulation Control", False, f"Error: {str(e)}")

    def test_alert_resolution(self):
        """Test alert resolution functionality"""
        try:
            # First get alerts to find one to resolve
            alerts_response = requests.get(f"{self.api_url}/alerts", timeout=10)
            if alerts_response.status_code != 200:
                return self.log_test("Alert Resolution", False, "Could not fetch alerts")
            
            alerts = alerts_response.json()
            if not alerts:
                return self.log_test("Alert Resolution", True, "No alerts to resolve (expected)")
            
            # Try to resolve the first alert
            alert_id = alerts[0]['id']
            response = requests.post(f"{self.api_url}/alerts/{alert_id}/resolve", timeout=10)
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}, Alert ID: {alert_id}"
            
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'No message')}"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:100]}"
            
            return self.log_test("Alert Resolution", success, details)
        except Exception as e:
            return self.log_test("Alert Resolution", False, f"Error: {str(e)}")

    def on_ws_message(self, ws, message):
        """WebSocket message handler"""
        try:
            data = json.loads(message)
            self.ws_messages.append(data)
            print(f"📡 WebSocket message received: {data.get('type', 'unknown')}")
        except Exception as e:
            print(f"📡 WebSocket message error: {e}")

    def on_ws_error(self, ws, error):
        """WebSocket error handler"""
        print(f"📡 WebSocket error: {error}")

    def on_ws_close(self, ws, close_status_code, close_msg):
        """WebSocket close handler"""
        print(f"📡 WebSocket closed: {close_status_code} - {close_msg}")

    def on_ws_open(self, ws):
        """WebSocket open handler"""
        self.ws_connected = True
        print("📡 WebSocket connected")

    def test_websocket_connection(self):
        """Test WebSocket connectivity"""
        try:
            ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://') + '/api/ws'
            print(f"📡 Testing WebSocket connection to: {ws_url}")
            
            ws = websocket.WebSocketApp(ws_url,
                                      on_open=self.on_ws_open,
                                      on_message=self.on_ws_message,
                                      on_error=self.on_ws_error,
                                      on_close=self.on_ws_close)
            
            # Run WebSocket in a separate thread
            ws_thread = threading.Thread(target=ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection
            time.sleep(3)
            
            success = self.ws_connected
            details = f"Connected: {self.ws_connected}, Messages received: {len(self.ws_messages)}"
            
            if self.ws_messages:
                sample_msg = self.ws_messages[0]
                details += f", Sample message type: {sample_msg.get('type', 'unknown')}"
            
            # Close connection
            ws.close()
            
            return self.log_test("WebSocket Connection", success, details)
        except Exception as e:
            return self.log_test("WebSocket Connection", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting SecureWatch AI Backend Tests")
        print("=" * 50)
        
        # Basic API tests
        self.test_api_root()
        self.test_get_nodes()
        self.test_get_alerts()
        self.test_chat_history()
        
        # Simulation control
        self.test_simulation_control()
        
        # Alert management
        self.test_alert_resolution()
        
        # WebSocket connectivity
        self.test_websocket_connection()
        
        # AI functionality (test last as it takes longer)
        self.test_ai_diagnosis()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All backend tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = SecureWatchAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())