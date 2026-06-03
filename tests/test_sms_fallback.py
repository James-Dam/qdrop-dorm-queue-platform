import os
import sys
import unittest
from importlib import reload
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import sms_messaging.services as sms_services


class SmsFallbackTests(unittest.TestCase):
    def setUp(self):
        self.old_env = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.old_env)

    def test_send_confirmation_message_falls_back_when_sms_disabled(self):
        os.environ["ENABLE_SMS"] = "false"
        module = reload(sms_services)

        result = module.send_confirmation_message(
            "+15555551234", "shower", "08:00 AM", 30
        )
        self.assertTrue(result)

    def test_send_confirmation_message_falls_back_when_credentials_missing(self):
        os.environ["ENABLE_SMS"] = "true"
        os.environ["TWILIO_ACCOUNT_SID"] = ""
        os.environ["TWILIO_AUTH_TOKEN"] = ""
        os.environ["TWILIO_PHONE_NUMBER"] = ""
        module = reload(sms_services)

        result = module.send_confirmation_message(
            "+15555551234", "washer", "09:30 AM", 30
        )
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
