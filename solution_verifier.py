import dd
import graph as gh
import problem as pr
import ddar

class SolutionVerifier:
    """Verifies if a solution is correct using the full DD+AR engine."""
  
    def __init__(self):
        self.defs = pr.Definition.from_txt_file("defs.txt", to_dict=True)
        self.rules = pr.Theorem.from_txt_file("rules.txt", to_dict=True)
  
    @staticmethod
    def inject_solution(problem_txt: str, solution_txt: str | None) -> str:
        """Injects the LLM's construction into the problem setup."""
        prob = problem_txt.strip()
        if not solution_txt:
            return prob
            
        sol = solution_txt.strip().rstrip(";")
        if not sol:
            return prob

        # Inject solution before the '?' separator
        if "?" not in prob:
            return f"{prob.rstrip(';')}; {sol}"
            
        left, right = prob.split("?", 1)
        # The solution adds to the premises (left side)
        return f"{left.strip().rstrip(';')}; {sol} ? {right.strip()}"
  
    def verify(self, problem_txt: str, solution: str | None = None) -> bool:
        """
        Evaluates the proof.
        
        Args:
            problem_txt: The original problem DSL.
            solution: The LLM's answer (auxiliary constructions).
            
        Returns:
            True if the construction successfully leads to the goal.
        """
        full_problem_txt = self.inject_solution(problem_txt, solution)
        
        try:
            p = pr.Problem.from_txt(full_problem_txt)
        except Exception as e:
            print(f"Syntax Error in solution: {e}")
            return False

        if p.goal is None:
            return False
  
        g, _ = gh.Graph.build_problem(p, self.defs, verbose=False)
        
        _, _, status, _, _ = ddar.solve(
            g, 
            self.rules, 
            p, max_level=100, timeout=600)
  
        return status == 'solved'