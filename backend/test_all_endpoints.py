"""Comprehensive API endpoint test suite for SentinelChain backend."""
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import create_app

async def main():
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api/v1") as client:
        # 1. Login
        login_res = await client.post("/auth/login", json={"username": "admin", "password": "admin_demo_password"})
        print(f"POST /auth/login: {login_res.status_code}")
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Endpoints
        endpoints = [
            ("GET", "/auth/me"),
            ("GET", "/dashboard/summary"),
            ("GET", "/dashboard/trends"),
            ("GET", "/incidents"),
            ("GET", "/incidents/"),
            ("GET", "/assets"),
            ("GET", "/assets/"),
            ("GET", "/response-actions"),
            ("GET", "/response-actions/"),
            ("GET", "/playbooks"),
            ("GET", "/integrity/status"),
            ("GET", "/integrity/entries"),
            ("GET", "/integrity/batches"),
            ("GET", "/simulator/scenarios"),
            ("GET", "/settings/autonomy-mode"),
        ]

        for method, ep in endpoints:
            if method == "GET":
                res = await client.get(ep, headers=headers)
                print(f"{method} {ep} -> [{res.status_code}]")
                assert res.status_code == 200, f"Failed on {ep}: {res.text}"

        # Test running a scenario
        sim_res = await client.post("/simulator/scenarios/ssh_brute_force_compromise/run?speed=2.0", headers=headers)
        print(f"POST /simulator/scenarios/.../run -> [{sim_res.status_code}]: {sim_res.json()}")
        assert sim_res.status_code == 200

        # Check incidents again
        inc_res = await client.get("/incidents", headers=headers)
        print(f"GET /incidents after sim -> [{inc_res.status_code}], items count: {len(inc_res.json()['items'])}")

        print("\n ALL ENDPOINTS PASSED WITH 200 OK!")

if __name__ == "__main__":
    asyncio.run(main())
