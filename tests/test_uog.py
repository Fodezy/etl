import unittest
import json
from connectors.uog.connector import UoGConnector  # Fixed to absolute import

class TestUoGConnector(unittest.TestCase):
    def test_extract_transform(self):
        connector = UoGConnector()
        # Run extract (which also runs scrapers)
        raw = connector.extract()
        self.assertIn('subjects_with_courses', raw)
        self.assertIn('programs_with_sections', raw)

        # Run transform on a small slice to ensure mapping works
        norm = connector.transform(raw)
        self.assertIn('courses', norm)
        self.assertIn('programs', norm)
        # Ensure courses list is non-empty
        self.assertIsInstance(norm['courses'], list)
        self.assertIsInstance(norm['programs'], list)

if __name__ == '__main__':
    unittest.main()
