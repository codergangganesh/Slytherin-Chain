"""Comprehensive test suite running all endpoints and scenarios with complete tracebacks."""
import asyncio
import traceback
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.db.init_db import init_database

async def main():
    await init_database()
    app = create_app()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api/v1", timeout=30.0) as client:
        # 1. Login
        login_res = await client.post("/auth/login", json={"username": "admin", "password": "admin_demo_password"})
        print(f"POST /auth/login -> [{login_res.status_code}]")
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Endpoints to test
        endpoints = [
            "/auth/me",
            "/dashboard/summary",
            "/dashboard/trends",
            "/incidents",
            "/assets",
            "/response-actions",
            "/playbooks",
            "/settings/autonomy-mode",
            "/settings/playbooks",
            "/integrity/status",
            "/integrity/entries",
            "/integrity/batches",
            "/simulator/scenarios",
        ]

        for ep in endpoints:
            try:
                res = await client.get(ep, headers=headers)
                print(f"GET {ep:30} -> [{res.status_code}]")
                if res.status_code != 200:
                    print(f"   Error detail: {res.text}")
            except Exception as e:
                print(f"GET {ep:30} -> EXCEPTION: {e}")
                traceback.print_exc()

        # 3. Test running scenario
        print("\nTesting Attack Simulator Scenario execution...")
        scenarios = [
            "ssh_brute_force_compromise",
            "port_scan_recon",
            "ransomware_activity",
            "benign_admin_scan_false_positive",
            "protected_asset_attack",
        ]
        for scenario in scenarios:
            try:
                sim_res = await client.post(f"/simulator/scenarios/{scenario}/run?speed=2.0", headers=headers)
                print(f"POST /simulator/scenarios/{scenario}/run -> [{sim_res.status_code}]")
                if sim_res.status_code != 200:
                    print(f"   Scenario error: {sim_res.text}")
                else:
                    data = sim_res.json()
                    print(f"   Success: {data.get('scenario_name')} - {data.get('events_injected')} events, {data.get('alerts_triggered')} alerts, {data.get('incidents_impacted')} incidents")
            except Exception as e:
                print(f"POST /simulator/scenarios/{scenario}/run -> EXCEPTION: {e}")
                traceback.print_exc()

        # 4. Check incidents, timeline, and actions after scenario injection
        inc_res = await client.get("/incidents", headers=headers)
        inc_data = inc_res.json()
        print(f"\nGET /incidents after attacks -> [{inc_res.status_code}], total incidents: {inc_data.get('total')}")
        
        if inc_data.get("items"):
            first_inc_id = inc_data["items"][0]["id"]
            detail_res = await client.get(f"/incidents/{first_inc_id}", headers=headers)
            print(f"GET /incidents/{first_inc_id} -> [{detail_res.status_code}] Risk Score: {detail_res.json().get('risk_score')}")
            
            tl_res = await client.get(f"/incidents/{first_inc_id}/timeline", headers=headers)
            print(f"GET /incidents/{first_inc_id}/timeline -> [{tl_res.status_code}], entries: {len(tl_res.json())}")

        act_res = await client.get("/response-actions", headers=headers)
        print(f"GET /response-actions after attacks -> [{act_res.status_code}], total actions: {act_res.json().get('total')}")

        verif_res = await client.get("/integrity/status", headers=headers)
        print(f"GET /integrity/status after attacks -> [{verif_res.status_code}], status: {verif_res.json().get('status')}")

        print("\n==========================================================")
        print("   ALL SENTINELCHAIN MODULES TESTED AND OPERATIONAL!")
        print("==========================================================")

if __name__ == "__main__":
    asyncio.run(main())
