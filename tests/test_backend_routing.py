import unittest

from backend.errors import ValidationError
from backend.service import understand_query


class BackendRoutingTests(unittest.TestCase):
    def test_backend_routes_requests_through_agent(self) -> None:
        cases = [
            ("What objects are visible in this scene?", 1, "vqa"),
            ("Where are the buildings?", 1, "grounding"),
            ("What changed between these images?", 2, "change_detection"),
            ("Analyze this area using optical and SAR imagery.", 2, "optical_sar"),
        ]

        for query, image_count, expected_task in cases:
            with self.subTest(query=query):
                routing = understand_query(query, image_count)

                self.assertEqual(routing["task"], expected_task)
                self.assertEqual(
                    routing["required_images"],
                    2 if expected_task in {"change_detection", "optical_sar"} else 1,
                )
                self.assertTrue(routing["reason"])

    def test_backend_converts_agent_image_requirement_to_validation_error(self) -> None:
        with self.assertRaisesRegex(ValidationError, "requires 2 image"):
            understand_query("Compare these two images.", image_count=1)
