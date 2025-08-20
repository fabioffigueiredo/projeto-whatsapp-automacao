from django.test import TestCase
from core.services.fx import dolar_comercial

class FxTest(TestCase):
    def test_dolar_comercial(self):
        rate = dolar_comercial()
        self.assertTrue(rate > 0)