"""Unit tests for proof_verifier.py."""
import time
import unittest

from absl.testing import absltest
from proof_verifier import ProofVerifier


class ProofVerifierTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.verifier = ProofVerifier()

  def verify_proof(self, problem_txt: str, proof_dsl: str) -> dict:
    """Wrapper around verifier.verify_proof that measures execution time."""
    start_time = time.time()
    result = self.verifier.verify_proof(problem_txt, proof_dsl)
    elapsed_time = time.time() - start_time
    print(f"  [verify_proof time: {elapsed_time:.4f}s]")
    return result

  
  def test_verify_proof_complex1(self):
    """Test that proof with problem 1 is valid."""
    problem = " a b c d = trapezoid a b c d; e = midpoint e a d; f = midpoint f b c ? para e f a b"
    proof = "e = midp e a d; f = midp f b c; eqratio e a e d f b f c; para a b c d; coll e a d; coll c f b; eqratio e a e d f b f c; para e f a b"
    result = self.verify_proof(problem, proof)
    print(result)
    
    self.assertTrue(result["goal_reached"])
    self.assertTrue(result["is_valid"])
  
  def test_verify_proof_complex2(self):
    """Test that proof with problem 2 is valid."""
    problem = "a b c d = eq_quadrangle a b c d; x = parallelogram a b c x ? cong a d a x"
    proof = "para a b c x; para a x b c; eqangle b a b c x c x a; para a x b c; eqangle b a b c x c x a; cong c b a x; cong a d b c; cong a d a x"
    result = self.verify_proof(problem, proof)
    print(result)
    
    self.assertTrue(result["goal_reached"])
    self.assertTrue(result["is_valid"])

  def test_verify_proof_complex56(self):
    """Test that proof with problem 56 is valid."""
    problem = "a b c = ieq_triangle a b c; m = midpoint m a b; n = midpoint n b c; p = midpoint p a c ? para m n a c"
    proof = 'coll b m a, m = midp m a b; coll c n b, n = midp n b c; para m n a c'
    
    result = self.verify_proof(problem, proof)
    print(result)
    
    self.assertTrue(result["goal_reached"])
    self.assertTrue(result["is_valid"])
    
  def test_verify_proof_complex57(self):
    """Test that proof with problem 57 is valid."""
    problem = "a b c = r_triangle a b c; m = midpoint m a b; n = midpoint n a c; p = midpoint p b c ? para m n b c"
    proof = "coll b m a, m = midp m a b; coll c n b, n = midp n a c; para m n b c"
    
    result = self.verify_proof(problem, proof)
    print(result)
    
    self.assertTrue(result["goal_reached"])
    self.assertTrue(result["is_valid"])
    
if __name__ == '__main__':
  absltest.main()
