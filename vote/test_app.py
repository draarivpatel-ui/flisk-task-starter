import json
import unittest
from unittest.mock import patch

from app import app


class VoteTest(unittest.TestCase):
    def test_invalid_options_are_not_queued(self):
        with app.test_client() as client, patch("app.get_redis") as get_redis:
            for data in ({}, {"vote": ""}, {"vote": "other"}):
                with self.subTest(data=data):
                    get_redis.reset_mock()
                    response = client.post("/", data=data)
                    self.assertEqual(response.status_code, 400)
                    get_redis.assert_not_called()

    def test_valid_options_are_queued_for_the_same_voter(self):
        with app.test_client() as client, patch("app.get_redis") as get_redis:
            queue = get_redis.return_value
            first_voter = None
            for option in ("a", "b"):
                with self.subTest(option=option):
                    queue.rpush.reset_mock()
                    response = client.post("/", data={"vote": option})
                    self.assertEqual(response.status_code, 200)
                    queue.rpush.assert_called_once()
                    key, payload = queue.rpush.call_args.args
                    vote = json.loads(payload)
                    self.assertEqual(key, "votes")
                    self.assertEqual(vote["vote"], option)
                    self.assertTrue(vote["voter_id"])
                    if first_voter is None:
                        first_voter = vote["voter_id"]
                    else:
                        self.assertEqual(vote["voter_id"], first_voter)
