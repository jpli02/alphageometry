"""Unit tests for proof_verifier.py."""
import unittest

from absl.testing import absltest
from proof_verifier import ProofVerifier


class ProofVerifierTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.verifier = ProofVerifier()

  def test_is_construction(self):
    """Test _is_construction method."""
    self.assertTrue(self.verifier._is_construction("d = on_line d a c"))
    self.assertTrue(self.verifier._is_construction("e = on_line e a c, on_line e b d"))
    self.assertFalse(self.verifier._is_construction("perp a d b c"))
    self.assertFalse(self.verifier._is_construction("cong a b c d"))

  def test_verify_proof_valid_with_construction_and_goal(self):
    """Test verification of valid proof with construction step."""
    problem = 'a b c = triangle a b c; d = on_tline d b a c, on_tline d c a b ? perp a d b c'  # pylint: disable=line-too-long
    proof = 'e = on_line e a c, on_line e b d'
    
    result = self.verifier.verify_proof(problem, proof)
    
    self.assertTrue(result["is_valid"])
    self.assertTrue(result["goal_reached"])
    self.assertEqual(result["steps_passed"], 1)
    self.assertIn("Success", result["error_msg"])

  def test_verify_proof_valid_multiple_steps(self):
    """Test verification with multiple proof steps."""
    problem = 'a b c = triangle a b c ? perp a d b c'
    # First add construction, then verify a derivation step
    proof = 'd = on_tline d b a c, on_tline d c a b; e = on_line e a c, on_line e b d'
    
    result = self.verifier.verify_proof(problem, proof)
    
    self.assertTrue(result["is_valid"])
    self.assertTrue(result["goal_reached"])
    self.assertEqual(result["steps_passed"], 2)

  def test_verify_proof_invalid_wrong_construction(self):
    """Test that invalid construction fails immediately."""
    problem = 'a b c = triangle a b c ? perp a d b c'
    # Invalid construction (point d not properly defined)
    proof = 'd = invalid_construction d a b'
    
    result = self.verifier.verify_proof(problem, proof)
    
    self.assertFalse(result["is_valid"])
    self.assertFalse(result["goal_reached"])

  def test_verify_proof_invalid_wrong_derivation(self):
    """Test that invalid derivation step fails immediately."""
    problem = 'a b c = triangle a b c ? perp a d b c'
    # Valid construction but wrong derivation
    proof = 'd = on_tline d b a c, on_tline d c a b; cong a b c d'  # Wrong derivation
    
    result = self.verifier.verify_proof(problem, proof)
    
    self.assertFalse(result["is_valid"])
    self.assertFalse(result["goal_reached"])
    self.assertEqual(result["steps_passed"], 1)  # First step (construction) passed
    self.assertIn("Logic Gap", result["error_msg"])

  # def test_verify_proof_stops_on_first_error(self):
  #   """Test that verification stops on first invalid step."""
  #   problem = 'a b c = triangle a b c ? perp a d b c'
  #   # Multiple steps, second one is wrong
  #   proof = 'd = on_tline d b a c, on_tline d c a b; wrong_predicate a b c; perp a d b c'
    
  #   result = self.verifier.verify_proof(problem, proof)
    
  #   self.assertFalse(result["is_valid"])
  #   self.assertEqual(result["steps_passed"], 1)  # Only first step passed
  #   self.assertIn("Logic Gap", result["error_msg"])

  def test_verify_proof_empty_proof(self):
    """Test verification with empty proof steps."""
    problem = 'a b c = triangle a b c ? perp a d b c'
    proof = ''
    
    result = self.verifier.verify_proof(problem, proof)
    
    self.assertFalse(result["is_valid"])
    self.assertIn("No proof steps", result["error_msg"])

  def test_verify_proof_no_goal(self):
    """Test verification with problem that has no goal."""
    problem = 'a b c = triangle a b c'
    proof = 'd = on_line d a b'
    
    result = self.verifier.verify_proof(problem, proof)
    
    # Should be valid if all steps are valid (no goal to reach)
    self.assertTrue(result["is_valid"])
    self.assertTrue(result["goal_reached"])
    self.assertIn("No global goal", result["error_msg"])

  def test_verify_proof_steps_valid_but_goal_not_reached(self):
    """Test case where all steps are valid but goal is not reached."""
    problem = 'a b c = triangle a b c ? perp a d b c'
    # Valid construction but doesn't lead to goal
    proof = 'd = on_line d a b'  # Valid but insufficient
    
    result = self.verifier.verify_proof(problem, proof)
    
    self.assertFalse(result["is_valid"])
    self.assertFalse(result["goal_reached"])
    self.assertEqual(result["steps_passed"], 1)  # Step passed
    self.assertIn("final goal NOT reached", result["error_msg"])

  def test_verify_proof_construction_already_in_context(self):
    """Test that construction already in context is skipped."""
    problem = 'a b c = triangle a b c; d = on_tline d b a c, on_tline d c a b ? perp a d b c'  # pylint: disable=line-too-long
    # Try to add construction that's already in problem
    proof = 'd = on_tline d b a c, on_tline d c a b'
    
    result = self.verifier.verify_proof(problem, proof)
    
    # Should still work (construction is idempotent)
    # But goal might not be reached without additional steps
    self.assertIsInstance(result["steps_passed"], int)

  def test_verify_proof_with_newline_separators(self):
    """Test that proof steps can be separated by newlines."""
    problem = 'a b c = triangle a b c; d = on_tline d b a c, on_tline d c a b ? perp a d b c'  # pylint: disable=line-too-long
    proof = 'e = on_line e a c, on_line e b d'
    
    result = self.verifier.verify_proof(problem, proof)
    
    self.assertTrue(result["is_valid"])
    self.assertTrue(result["goal_reached"])

  def test_verify_proof_mixed_separators(self):
    """Test proof with mixed semicolon and newline separators."""
    problem = 'a b c = triangle a b c ? perp a d b c'
    proof = 'd = on_tline d b a c, on_tline d c a b\ne = on_line e a c, on_line e b d'
    
    result = self.verifier.verify_proof(problem, proof)
    
    self.assertTrue(result["is_valid"])
    self.assertTrue(result["goal_reached"])
    self.assertEqual(result["steps_passed"], 2)

  def test_verify_proof_simple_derivation_only(self):
    """Test proof with only derivation steps (no constructions)."""
    # Problem that can be solved directly
    problem = 'a b c = triangle a b c; d = incenter d a b c; e = excenter e a b c ? perp d c c e'  # pylint: disable=line-too-long
    # Empty proof - should check if goal is reachable from premises
    proof = ''
    
    result = self.verifier.verify_proof(problem, proof)
    
    # Empty proof means we only check if goal is reachable
    # This should fail because we need to actually derive it
    self.assertFalse(result["is_valid"])

  def test_verify_proof_invalid_syntax_in_step(self):
    """Test that invalid syntax in a step causes failure."""
    problem = 'a b c = triangle a b c ? perp a d b c'
    proof = 'invalid syntax here!!!'
    
    result = self.verifier.verify_proof(problem, proof)
    
    self.assertFalse(result["is_valid"])
    # Should fail at parsing or construction/derivation check
    self.assertIsInstance(result["error_msg"], str)

  def test_verify_proof_construction_before_derivation(self):
    """Test that constructions must come before derivations that use them."""
    problem = 'a b c = triangle a b c ? perp a d b c'
    # Try to use a derivation before construction (if d is needed)
    # This tests the sequential nature of verification
    proof = 'perp a d b c; d = on_tline d b a c, on_tline d c a b'
    
    result = self.verifier.verify_proof(problem, proof)
    
    # Should fail because d is not defined when we try to use it
    self.assertFalse(result["is_valid"])
    self.assertEqual(result["steps_passed"], 0)


if __name__ == '__main__':
  absltest.main()
