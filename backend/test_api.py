import httpx
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_lifecycle():
    print("="*60)
    print("🚀 STARTING BACKEND LIFE-CYCLE INTEGRATION TEST")
    print("="*60)
    
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Health check
        print("\n🔍 Checking API /health...")
        try:
            r = client.get("/health")
            print(f"Health Response: {r.status_code} - {r.json()}")
            assert r.status_code == 200
        except Exception as e:
            print(f"❌ Failed to reach backend: {e}")
            sys.exit(1)
            
        # 2. Trigger Travel Itinerary Request
        print("\n🛫 Submitting new Travel Request...")
        payload = {
            "query": "Weekend trip from Chicago to Seattle next month, budget $700, coffee tasting and skyline views",
            "user_id": "test_verification_user",
            "session_id": "test_verification_session_123"
        }
        r = client.post("/api/request", json=payload)
        print(f"Submit Response: {r.status_code} - {r.json()}")
        assert r.status_code == 202
        request_id = r.json()["request_id"]
        
        # 3. Poll Status
        print(f"\n⏳ Polling active execution status for request {request_id}...")
        status = "processing"
        poll_count = 0
        max_polls = 40
        last_logged_len = 0
        
        while status == "processing" and poll_count < max_polls:
            time.sleep(3)
            poll_count += 1
            r = client.get(f"/api/status/{request_id}")
            data = r.json()
            status = data.get("status")
            
            # Print new logs
            logs = data.get("logs", [])
            if len(logs) > last_logged_len:
                for log in logs[last_logged_len:]:
                    print(f"  {log}")
                last_logged_len = len(logs)
                
            print(f"  [Poll {poll_count}] Current status: '{status}'")
            
        print(f"\n🏁 Finished polling with terminal status: '{status}'")
        
        if status != "pending_approval":
            print(f"❌ Test failed. Expected status 'pending_approval', got '{status}'.")
            sys.exit(1)
            
        # 4. Check Pending Approvals
        print("\n📋 Fetching Admin Pending Approvals Queue...")
        r = client.get("/api/pending")
        pending_list = r.json()
        print(f"Pending Proposals Count: {len(pending_list)}")
        assert any(item["request_id"] == request_id for item in pending_list)
        print("✅ Correctly listed in Admin Pending Queue.")
        
        # 5. Approve Itinerary
        print(f"\n✍️ Approving proposal {request_id}...")
        r = client.post(f"/api/approve/{request_id}")
        print(f"Approve Response: {r.status_code} - {r.json()}")
        assert r.status_code == 200
        
        # 6. Verify Terminal Status
        print("\n🔄 Verifying final status has changed to approved...")
        r = client.get(f"/api/status/{request_id}")
        final_data = r.json()
        print(f"Final Status: '{final_data.get('status')}'")
        assert final_data.get("status") == "approved"
        
        print("\n🎉 SUCCESS! FULL INTEGRATION FLOW TEST PASSED!")

if __name__ == "__main__":
    test_lifecycle()
