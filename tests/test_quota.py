import json
import os
import unittest
from unittest.mock import patch

import quota


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class QuotaReservationTests(unittest.TestCase):
    def test_allowed_reservation_returns_true(self):
        env = {"HUB_URL": "https://example.convex.site", "HUB_WEBHOOK_SECRET": "test-secret", "GITHUB_RUN_ID": "123"}
        with patch.dict(os.environ, env, clear=True), patch("quota.urllib.request.urlopen", return_value=FakeResponse({"allowed": True, "calls": 1, "studioCalls": 1})):
            self.assertTrue(quota.reserve_image("faceless-studio", "asset-a"))

    def test_cap_denial_returns_false(self):
        env = {"HUB_URL": "https://example.convex.site", "HUB_WEBHOOK_SECRET": "test-secret", "GITHUB_RUN_ID": "123"}
        with patch.dict(os.environ, env, clear=True), patch("quota.urllib.request.urlopen", return_value=FakeResponse({"allowed": False, "reason": "global_daily_call_cap"})):
            self.assertFalse(quota.reserve_image("faceless-studio", "asset-a"))

    def test_missing_configuration_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True), patch("quota.urllib.request.urlopen") as request:
            self.assertFalse(quota.reserve_image("faceless-studio", "asset-a"))
            request.assert_not_called()

    def test_endpoint_error_fails_closed(self):
        env = {"HUB_URL": "https://example.convex.site", "HUB_WEBHOOK_SECRET": "test-secret"}
        with patch.dict(os.environ, env, clear=True), patch("quota.urllib.request.urlopen", side_effect=OSError("offline")):
            self.assertFalse(quota.reserve_image("faceless-studio", "asset-a"))


if __name__ == "__main__":
    unittest.main()
