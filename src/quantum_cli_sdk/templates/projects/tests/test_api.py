"""
Tests for the quantum API.
"""

import sys
import unittest
from pathlib import Path

# Add the source directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api.routes import setup_routes, get_circuits, get_circuit, run_circuit, get_results


class TestAPIRoutes(unittest.TestCase):
    """Tests for the API routes."""

    def test_setup_routes(self):
        """Test that routes can be set up correctly."""
        app = setup_routes(None)
        self.assertIn("routes", app)
        self.assertEqual(len(app["routes"]), 4)  # Should have 4 routes
        
    def test_route_paths(self):
        """Test that the routes have the correct paths."""
        app = setup_routes(None)
        paths = [route["path"] for route in app["routes"]]
        
        self.assertIn("/circuits", paths)
        self.assertIn("/circuits/{circuit_id}", paths)
        self.assertIn("/run", paths)
        self.assertIn("/results/{job_id}", paths)
        
    def test_route_methods(self):
        """Test that the routes have the correct HTTP methods."""
        app = setup_routes(None)
        
        # Check that we have GET and POST methods
        methods = [route["method"] for route in app["routes"]]
        self.assertIn("GET", methods)
        self.assertIn("POST", methods)
        
        # Specifically check the run endpoint is POST
        run_route = [r for r in app["routes"] if r["path"] == "/run"][0]
        self.assertEqual(run_route["method"], "POST")


class TestAPIHandlers(unittest.TestCase):
    """Tests for the API handler functions."""
    
    def test_get_circuits(self):
        """Test the get_circuits handler."""
        response = get_circuits()
        self.assertEqual(response["status"], "success")
        self.assertIn("data", response)
        self.assertIsInstance(response["data"], list)
        self.assertTrue(len(response["data"]) > 0)
        
    def test_get_circuit_valid(self):
        """Test the get_circuit handler with a valid ID."""
        response = get_circuit("bell")
        self.assertEqual(response["status"], "success")
        self.assertIn("data", response)
        self.assertEqual(response["data"]["id"], "bell")
        self.assertEqual(response["data"]["name"], "Bell State")
        
    def test_get_circuit_invalid(self):
        """Test the get_circuit handler with an invalid ID."""
        response = get_circuit("nonexistent")
        self.assertEqual(response["status"], "error")
        self.assertIn("message", response)
        
    def test_run_circuit(self):
        """Test the run_circuit handler."""
        response = run_circuit({})
        self.assertEqual(response["status"], "success")
        self.assertIn("data", response)
        self.assertIn("job_id", response["data"])
        self.assertEqual(response["data"]["status"], "submitted")
        
    def test_get_results(self):
        """Test the get_results handler."""
        job_id = "test-job-123"
        response = get_results(job_id)
        self.assertEqual(response["status"], "success")
        self.assertIn("data", response)
        self.assertEqual(response["data"]["job_id"], job_id)
        self.assertIn("results", response["data"])
        self.assertIn("counts", response["data"]["results"])


if __name__ == "__main__":
    unittest.main() 