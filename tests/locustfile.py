from locust import HttpUser, between, task

# These must exist in your DB for the test to work
TENANT_ID = "f7880935-2fb3-4096-877b-49b7b7b5b5e0"
USER_ID = "a5845bd5-a405-4652-840a-0b22577f00c3"
HEADERS = {"x-tenant-id": TENANT_ID, "x-user-id": USER_ID}


class DocSenseUser(HttpUser):
    """
    Simulates one user of the DocSense API.
    Each simulated user runs tasks randomly, weighted by @task(weight).
    """

    wait_time = between(1, 3)
    # Wait 1-3 seconds between tasks (simulates real user think time)
    # Without this, users would hammer the API with no pause

    @task(3)
    def health_check(self):
        """Weight 3 - called 3x more often than search."""
        self.client.get("/health")

    @task(1)
    def search(self):
        """Weight 1 - the expensive operation."""
        self.client.post(
            "/search/",
            json={"query": "how does DocSense handle multi-tenancy?", "top_k": 3},
            headers=HEADERS,
        )

    @task(2)
    def get_feedback_stats(self):
        """Weight 2 - lightweight DB query."""
        self.client.get("/feedback/stats", headers=HEADERS)
