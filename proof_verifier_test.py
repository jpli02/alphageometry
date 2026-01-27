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

  
  def test_verify_proof_complex1_success(self):
    """Test that proof with problem 1 is valid."""
    problem = " a b c d = trapezoid a b c d; e = midpoint e a d; f = midpoint f b c ? para e f a b"
    proof = "e = midp e a d; f = midp f b c; eqratio e a e d f b f c; para a b c d; coll e a d; coll c f b; eqratio e a e d f b f c; para e f a b"
    result = self.verify_proof(problem, proof)
    print(result)
    
    self.assertTrue(result["goal_reached"])
    self.assertTrue(result["is_valid"])
  
  def test_verify_proof_complex1_failure(self):
    """Test that proof with problem 1 is failed."""
    problem = " a b c d = trapezoid a b c d; e = midpoint e a d; f = midpoint f b c ? para e f a b"
    proof = "e = midp e a d; f = midp f b c; eqratio e a e d c b f c; para e f a b" # eqratio is wrong
    result = self.verify_proof(problem, proof)
    print(result)

    self.assertFalse(result["goal_reached"])
    self.assertFalse(result["is_valid"])
  
  def test_verify_proof_complex1_failure2(self):
    """Test that proof with problem 1 is failed. no goal reached."""
    problem = " a b c d = trapezoid a b c d; e = midpoint e a d; f = midpoint f b c ? para e f a b"
    proof = "para e f a a" # goal is wrong
    result = self.verify_proof(problem, proof)
    print(result)

    self.assertFalse(result["goal_reached"])
    self.assertFalse(result["is_valid"])
    
  def test_verify_proof_complex1_failure3(self):
    """Test that proof with problem 1 is failed. invalid proof."""
    problem = " a b c d = trapezoid a b c d; e = midpoint e a d; f = midpoint f b c ? para e f a b"
    proof = "coll e f a b" # keyword is wrong
    result = self.verify_proof(problem, proof)
    print(result)

    self.assertFalse(result["goal_reached"])
    self.assertFalse(result["is_valid"])
  
  def test_verify_proof_complex2(self):
    """Test that proof with problem 2 is valid."""
    problem = "a b c d = eq_quadrangle a b c d; x = parallelogram a b c x ? cong a d a x"
    proof = "para a b c x; para a x b c; eqangle b a b c x c x a; para a x b c; eqangle b a b c x c x a; cong c b a x; cong a d b c; cong a d a x"
    result = self.verify_proof(problem, proof)
    print(result)
    
    self.assertTrue(result["goal_reached"])
    self.assertTrue(result["is_valid"])
    
  def test_verify_proof_complex44(self):
    """Test that proof with problem 44 is valid."""
    problem = "a b c = triangle a b c; o = circle o a b c; d = on_line d b c; e = on_line e b c, on_circle e a d; f = on_circle f o a, on_circle f a d; g = on_circle g o a, on_circle g a d; o1 = circle o1 f b d; o2 = circle o2 g c e; k = on_circle k o1 b, on_line k a b; l = on_circle l o2 c, on_line l a c; x = on_line x f k, on_line x l g ? coll x o a"
    proof = "cong o b o c; cong o a o b; coll c d b; coll c e b; cong a e a d; cong a f a d; cong o f o a; cong a g a d; cong o g o a; cong o1 b o1 d; cong o1 f o1 b; cong o2 g o2 c;cong o2 c o2 e; cong o1 k o1 b; coll a b k; cong o2 l o2 c; coll c a l; coll f x k; coll l g x; cong a f a g; cyclic b k d f; eqangle k b k d f b f d; cyclic b f a g; cyclic g a f c; cyclic g b f c; cyclic f e g d; "
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
    
  def test_verify_proof_complex57_success(self):
    """Test that proof with problem 57 is valid."""
    problem = "a b c = r_triangle a b c; m = midpoint m a b; n = midpoint n a c; p = midpoint p b c ? para m n b c"
    proof = "coll b m a, m = midp m a b; coll c n b, n = midp n a c; para m n b c"
    
    result = self.verify_proof(problem, proof)
    print(result)
    
    self.assertTrue(result["goal_reached"])
    self.assertTrue(result["is_valid"])
    

    
if __name__ == '__main__':
  absltest.main()
