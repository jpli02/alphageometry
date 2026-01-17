import dd
import graph as gh
import problem as pr

class ProofVerifier:
    def __init__(self, defs_path="defs.txt", rules_path="rules.txt"):
        self.defs = pr.Definition.from_txt_file(defs_path, to_dict=True)
        # Load rules as list for BFS
        self.rules_dict = pr.Theorem.from_txt_file(rules_path, to_dict=True)
        self.rules_list = list(self.rules_dict.values())

    def _is_construction(self, dsl: str) -> bool:
        return "=" in dsl

    def _run_bfs_check(self, context_str: str, target_predicate_str: str, max_level=2) -> bool:
        """
        Check if target is derivable from context by incrementally enabling
        more complex rule levels (AlphaGeometry style).
        """
        target_predicate_str = target_predicate_str.strip().rstrip(";")
        context_str = context_str.strip().rstrip(";")

        # 1) Build a temporary Problem with explicit goal
        # Problem.from_txt() will parse the goal as a Construction
        try:
            temp_prob_txt = f"{context_str} ? {target_predicate_str}"
            p = pr.Problem.from_txt(temp_prob_txt)
            try:
                g, _ = gh.Graph.build_problem(p, self.defs, verbose=False)
            except Exception as e:
                print(f"  [Graph build failed] {type(e).__name__}: {e}")
                return False
        except Exception as e:
            return False

        # Check if goal exists
        if p.goal is None:
            return False


        # Helper: check goal if all names exist
        def goal_holds() -> bool:
            try:
                goal_args = g.names2nodes(p.goal.args)
            except Exception:
                return False
            try:
                return g.check(p.goal.name, goal_args)
            except (ValueError, KeyError, AttributeError) as e:
                # g.check can raise ValueError for unrecognized predicate names
                # or other errors for invalid arguments
                print(f"  [Check failed] {type(e).__name__}: {e}")
                return False
            except Exception as e:
                # Catch any other unexpected exceptions
                print(f"  [Check error] {type(e).__name__}: {e}")
                return False

        # 3) Incremental deepening over theorem "level"
        for level in range(1, max_level + 1):
            if goal_holds():
                return True

            # One pass of DD/AR at this level
            added, derives, eq4s, _ = dd.bfs_one_level(
                g,
                self.rules_dict,
                level,
                p,
                verbose=False,
                nm_check=True,
                timeout=30,  # Reduced timeout for faster failure
            )

            # Apply AR outputs 
            if derives:
                dd.apply_derivations(g, derives)
            if eq4s:
                dd.apply_derivations(g, eq4s)

            if goal_holds():
                return True

        return goal_holds()


    def verify_proof(self, problem_txt: str, proof_dsl: str) -> dict:
        """
        Verify each step of a proof and check if it solves the problem.
        If any middle step is wrong, the result is wrong.
        
        Args:
            problem_txt: Problem in DSL format (e.g., "a b c = triangle a b c ? perp a d b c")
            proof_dsl: Proof steps in DSL format, separated by ';' or newlines
                      (e.g., "e = on_line e a c, on_line e b d; perp a d b c")
        
        Returns:
            Dictionary with:
            - is_valid: True if all steps are valid and goal is reached
            - error_msg: Error message if verification fails
            - steps_passed: Number of steps that passed (0-indexed, so if fails at step 3, returns 2)
            - goal_reached: True if final goal is reached
        """
        result = {
            "is_valid": False,
            "error_msg": "",
            "steps_passed": 0,
            "goal_reached": False
        }

        # 1. Split original problem
        if "?" in problem_txt:
            prems, global_goal_dsl = problem_txt.split("?", 1)
        else:
            prems, global_goal_dsl = problem_txt, ""
        
        current_context = prems.strip()
        
        # Parse proof steps (handle both ';' and newline separators)
        steps = [s.strip() for s in proof_dsl.replace('\n', ';').split(';') if s.strip()]

        if not steps:
            result["error_msg"] = "No proof steps provided."
            return result

        print(f"--- Starting Verification (Steps: {len(steps)}) ---")

        # 2. Verify each step sequentially
        for i, step in enumerate(steps):
            step_num = i + 1

            if self._is_construction(step):
                if step in current_context:
                    print(f"  Step {step_num} (Construction): {step} [already in context]")
                    continue
                
                temp_context = f"{current_context}; {step}"
                current_context = temp_context
                print(f"  Step {step_num} (Construction): {step} [OK]")
                    
            else:
                # Derivation step checking: BFS verification
                print(f"  Step {step_num} (Derivation): {step}")
                if self._run_bfs_check(current_context, step, max_level=3):
                    print(f"    [OK]")
                    current_context = f"{current_context}; {step}"
                else:
                    result["error_msg"] = f"Step {step_num} Logic Gap: '{step}' not derivable from current context."
                    result["steps_passed"] = i  # Failed at step i (0-indexed)
                    return result
                
        print("All steps passed")
        result["steps_passed"] = len(steps)

        # 3. Final goal verification
        if not global_goal_dsl.strip():
            # No global goal (e.g., pure construction problem)
            result["is_valid"] = True
            result["goal_reached"] = True
            result["error_msg"] = "Verified (No global goal)."
            return result
        
        # For final goal, use larger max_level (increase with difficulty)
        is_goal_reached = self._run_bfs_check(current_context, global_goal_dsl.strip(), max_level=10)
        print("is_goal_reached: ", is_goal_reached)
        if is_goal_reached:
            result["is_valid"] = True
            result["goal_reached"] = True
            result["error_msg"] = "Success: All proof steps valid and goal reached."
        else:
            result["is_valid"] = False  # final goal not reached
            result["goal_reached"] = False
            result["error_msg"] = "All steps valid, but final goal NOT reached."

        return result