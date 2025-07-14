#!/usr/bin/env python3
"""
CLI tool for testing the MiniVault API.
"""

import requests
import json
import argparse
import sys
from datetime import datetime


class MiniVaultCLI:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
    
    def test_health(self):
        """Test the health endpoint."""
        print("🔍 Testing health endpoint...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ Health check passed!")
                print(f"   Status: {data['status']}")
                print(f"   Ollama: {data['ollama_status']}")
                if data.get('available_models'):
                    print(f"   Models: {', '.join(data['available_models'])}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def generate_response(self, prompt: str, model: str = None):
        """Generate a response for the given prompt."""
        print(f"🤖 Generating response for: '{prompt[:50]}{'...' if len(prompt) > 50 else ''}'")
        
        payload = {"prompt": prompt}
        if model:
            payload["model"] = model
        
        try:
            start_time = datetime.now()
            response = requests.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=60
            )
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Response generated successfully!")
                print(f"   Model: {data['model']}")
                print(f"   Duration: {duration:.2f}s")
                print(f"   Response: {data['response']}")
                return True
            else:
                print(f"❌ Generation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   Raw response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Generation error: {e}")
            return False
    
    def get_recent_logs(self, limit: int = 5):
        """Get recent interaction logs."""
        print(f"📋 Getting {limit} recent logs...")
        try:
            response = requests.get(f"{self.base_url}/logs/recent?limit={limit}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logs = data.get("logs", [])
                print(f"✅ Retrieved {len(logs)} logs:")
                
                for i, log in enumerate(logs, 1):
                    status = "✅" if log.get("success", True) else "❌"
                    print(f"   {i}. {status} [{log.get('timestamp', 'N/A')}]")
                    print(f"      Prompt: {log.get('prompt', '')[:60]}...")
                    print(f"      Model: {log.get('model', 'N/A')}")
                    print(f"      Duration: {log.get('duration_ms', 0)}ms")
                    if not log.get("success", True):
                        print(f"      Error: {log.get('error_reason', 'Unknown')}")
                    print()
                
                return True
            else:
                print(f"❌ Failed to get logs: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Logs error: {e}")
            return False
    
    def get_stats(self):
        """Get interaction statistics."""
        print("📊 Getting interaction statistics...")
        try:
            response = requests.get(f"{self.base_url}/logs/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                print("✅ Statistics retrieved:")
                print(f"   Total interactions: {stats.get('total_interactions', 0)}")
                print(f"   Successful: {stats.get('successful_interactions', 0)}")
                print(f"   Failed: {stats.get('failed_interactions', 0)}")
                print(f"   Average duration: {stats.get('average_duration_ms', 0)}ms")
                return True
            else:
                print(f"❌ Failed to get stats: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Stats error: {e}")
            return False
    
    def run_interactive_mode(self):
        """Run in interactive mode."""
        print("🚀 MiniVault API Interactive Mode")
        print("Commands: generate, health, logs, stats, quit")
        print("-" * 50)
        
        while True:
            try:
                command = input("\n> ").strip().lower()
                
                if command in ["quit", "exit", "q"]:
                    print("👋 Goodbye!")
                    break
                elif command == "health":
                    self.test_health()
                elif command == "logs":
                    self.get_recent_logs()
                elif command == "stats":
                    self.get_stats()
                elif command.startswith("generate"):
                    if len(command) > 8:
                        prompt = command[9:]  # Remove "generate "
                        self.generate_response(prompt)
                    else:
                        prompt = input("Enter prompt: ").strip()
                        if prompt:
                            self.generate_response(prompt)
                elif command == "help":
                    print("Available commands:")
                    print("  health - Check API health")
                    print("  generate [prompt] - Generate response")
                    print("  logs - Show recent logs")
                    print("  stats - Show statistics")
                    print("  quit - Exit")
                else:
                    print("Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="MiniVault API CLI Test Tool")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--health", action="store_true", help="Test health endpoint")
    parser.add_argument("--prompt", help="Generate response for prompt")
    parser.add_argument("--model", help="Model to use for generation")
    parser.add_argument("--logs", action="store_true", help="Show recent logs")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    cli = MiniVaultCLI(args.url)
    
    if args.interactive:
        cli.run_interactive_mode()
    elif args.health:
        success = cli.test_health()
        sys.exit(0 if success else 1)
    elif args.prompt:
        success = cli.generate_response(args.prompt, args.model)
        sys.exit(0 if success else 1)
    elif args.logs:
        success = cli.get_recent_logs()
        sys.exit(0 if success else 1)
    elif args.stats:
        success = cli.get_stats()
        sys.exit(0 if success else 1)
    else:
        # Default: run a quick test suite
        print("🧪 Running MiniVault API Test Suite")
        print("=" * 50)
        
        all_passed = True
        
        # Test health
        all_passed &= cli.test_health()
        print()
        
        # Test generation with a simple prompt
        all_passed &= cli.generate_response("Hello, how are you?")
        print()
        
        # Show recent logs
        cli.get_recent_logs(3)
        print()
        
        # Show stats
        cli.get_stats()
        
        print("\n" + "=" * 50)
        if all_passed:
            print("✅ All tests passed!")
            sys.exit(0)
        else:
            print("❌ Some tests failed!")
            sys.exit(1)


if __name__ == "__main__":
    main()
