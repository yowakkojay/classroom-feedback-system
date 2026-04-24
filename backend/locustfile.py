from locust import HttpUser, task, between
import random


class StudentUser(HttpUser):
    """模拟学生用户"""
    wait_time = between(1, 3)
    student_index = 0

    def on_start(self):
        StudentUser.student_index += 1
        idx = StudentUser.student_index
        response = self.client.post("/api/auth/login/", json={
            "username": f"stress_test_{idx}",
            "password": "test123"
        })
        if response.status_code == 200:
            self.token = response.json().get("access")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(5)
    def submit_emoji(self):
        if not self.token:
            return
        self.client.post(
            "/api/feedback/submit/",
            json={
                "session_id": 10,  # 活跃的 session
                "score": random.randint(1, 6),
                "time_slot": random.randint(0, 5)
            },
            headers=self.headers,
            name="/api/feedback/submit/"
        )

    @task(1)
    def send_discussion(self):
        if not self.token:
            return
        self.client.post(
            "/api/discussion/send/",
            json={
                "session": 10,
                "content": f"测试消息 {random.randint(1, 9999)}"
            },
            headers=self.headers
        )

    @task(1)
    def get_messages(self):
        if not self.token:
            return
        self.client.get(
            "/api/discussion/messages/10/",
            headers=self.headers
        )


class TeacherUser(HttpUser):
    """模拟教师用户"""
    wait_time = between(2, 5)

    def on_start(self):
        response = self.client.post("/api/auth/login/", json={
            "username": "ywj",
            "password": "ywj123"
        })
        if response.status_code == 200:
            self.token = response.json().get("access")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(5)
    def get_statistics(self):
        if not self.token:
            return
        self.client.get(
            "/api/feedback/statistics/10/",
            headers=self.headers,
            name="/api/feedback/statistics/"
        )

    @task(3)
    def get_slots(self):
        if not self.token:
            return
        self.client.get(
            "/api/feedback/statistics/10/slots/",
            headers=self.headers
        )

    @task(2)
    def get_history(self):
        if not self.token:
            return
        self.client.get(
            "/api/feedback/history/",
            headers=self.headers
        )

    @task(1)
    def get_messages(self):
        if not self.token:
            return
        self.client.get(
            "/api/discussion/messages/10/",
            headers=self.headers
        )
