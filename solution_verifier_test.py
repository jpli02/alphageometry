"""Unit tests for solution_verifier.py."""
import unittest

from absl.testing import absltest
from solution_verifier import SolutionVerifier


class SolutionVerifierTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.verifier = SolutionVerifier()

  def test_inject_solution_basic(self):
    """Test basic solution injection."""
    problem = 'a b c = triangle a b c ? perp a d b c'
    solution = 'd = on_tline d b a c, on_tline d c a b'
    result = self.verifier.inject_solution(problem, solution)
    expected = 'a b c = triangle a b c; d = on_tline d b a c, on_tline d c a b ? perp a d b c'
    self.assertEqual(result, expected)

  def test_inject_solution_empty_solution(self):
    """Test injection with empty solution."""
    problem = 'a b c = triangle a b c ? perp a d b c'
    solution = ''
    result = self.verifier.inject_solution(problem, solution)
    self.assertEqual(result, problem)

  def test_inject_solution_no_goal(self):
    """Test injection when problem has no goal."""
    problem = 'a b c = triangle a b c'
    solution = 'd = on_tline d b a c'
    result = self.verifier.inject_solution(problem, solution)
    expected = 'a b c = triangle a b c; d = on_tline d b a c'
    self.assertEqual(result, expected)

  def test_inject_solution_with_trailing_semicolon(self):
    """Test injection with trailing semicolon in solution."""
    problem = 'a b c = triangle a b c ? perp a d b c'
    solution = 'd = on_tline d b a c;'
    result = self.verifier.inject_solution(problem, solution)
    expected = 'a b c = triangle a b c; d = on_tline d b a c ? perp a d b c'
    self.assertEqual(result, expected)

  def test_inject_solution_multiple_clauses(self):
    """Test injection with multiple solution clauses."""
    problem = 'a b c = triangle a b c ? perp a d b c'
    solution = 'd = on_tline d b a c, on_tline d c a b; e = on_line e a c'
    result = self.verifier.inject_solution(problem, solution)
    expected = 'a b c = triangle a b c; d = on_tline d b a c, on_tline d c a b; e = on_line e a c ? perp a d b c'
    self.assertEqual(result, expected)

  def test_verify_orthocenter_should_fail(self):
    """Test that orthocenter problem fails without auxiliary construction."""
    problem = 'a b c = triangle a b c; d = on_tline d b a c, on_tline d c a b ? perp a d b c'  # pylint: disable=line-too-long
    result = self.verifier.verify(problem, solution=None)
    self.assertFalse(result)

  def test_verify_orthocenter_with_solution_should_succeed(self):
    """Test that orthocenter problem succeeds with correct auxiliary construction."""
    problem = 'a b c = triangle a b c; d = on_tline d b a c, on_tline d c a b ? perp a d b c'  # pylint: disable=line-too-long
    solution = 'e = on_line e a c, on_line e b d'
    result = self.verifier.verify(problem, solution=solution)
    self.assertTrue(result)

  def test_verify_incenter_excenter_should_succeed(self):
    """Test that incenter-excenter problem succeeds (no solution needed)."""
    problem = (
        'a b c = triangle a b c; d = incenter d a b c; e = excenter e a b c ?'
        ' perp d c c e'
    )  # pylint: disable=line-too-long
    result = self.verifier.verify(problem, solution=None)
    self.assertTrue(result)

  def test_verify_with_empty_solution(self):
    """Test verification with empty solution (should behave like no solution)."""
    problem = 'a b c = triangle a b c; d = on_tline d b a c, on_tline d c a b ? perp a d b c'  # pylint: disable=line-too-long
    result = self.verifier.verify(problem, solution='')
    self.assertFalse(result)

  def test_verify_problem_without_goal(self):
    """Test verification with problem that has no goal."""
    problem = 'a b c = triangle a b c'
    result = self.verifier.verify(problem, solution=None)
    self.assertFalse(result)

  def test_verify_solution_already_in_problem(self):
    """Test verification when solution clauses are already in the problem."""
    problem = (
        'a b c = triangle a b c; d = on_tline d b a c, on_tline d c a b; '
        'e = on_line e a c, on_line e b d ? perp a d b c'
    )  # pylint: disable=line-too-long
    solution = 'e = on_line e a c, on_line e b d'  # Already in problem
    result = self.verifier.verify(problem, solution=solution)
    self.assertTrue(result)


if __name__ == '__main__':
  absltest.main()
