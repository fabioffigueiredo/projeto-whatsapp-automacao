from django.test import TestCase

class WebhookTest(TestCase):
    def test_start_flow(self):
        url = "/api/webhook/whatsapp"
        r = self.client.post(url, data={"phone":"555199999123","message":"oi"}, content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Dólar", r.json()["reply"])
