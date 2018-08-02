from django.test import TestCase
from django.urls import reverse


class HomeIndexViewTests(TestCase):
    def test_home(self):
        """
        Basic home test
        """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SLCPythoners")
