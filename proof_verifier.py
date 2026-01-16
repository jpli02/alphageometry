import dd
import graph as gh
import problem as pr
import geometry as gm

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
        Core helper: Check if a target derivation step is reachable
                    from the given context using BFS. 
                        
        Args:
            context_str: Current context (premises + previous steps)
            target_predicate_str: Target predicate to verify (e.g., "perp a d b c")
            max_level: Maximum BFS depth (increase this as problem becomes more complex
            
        Returns:
            True if target is reachable, False otherwise
        """
        # 1. Parse target as Construction (predicate, not clause)
        try:
            target_construction = pr.Construction.from_txt(target_predicate_str)
        except Exception:
            return False
        # 2. Build graph from context
        try:
            temp_prob_txt = f"{context_str.strip().rstrip(';')} ? {target_predicate_str}"
            p = pr.Problem.from_txt(temp_prob_txt)
            g, _ = gh.Graph.build_problem(p, self.defs, verbose=False)
        except Exception:
            return False
        # 3. BFS loop with DD + AR
        level = 1
        while level <= max_level:
            # Check if goal is already satisfied
            goal_args = g.names2nodes(target_construction.args)
            if g.check(target_construction.name, goal_args):
                return True

            # Run DD (deduction rules)
            # bfs_one_level already runs AR internally and returns derives/eq4s
            # Note: bfs_one_level expects rules as dict (not list)
            added, derives, eq4s, _ = dd.bfs_one_level(
                g, self.rules_dict, level, p, verbose=False, nm_check=True, timeout=30
            )
            
            # Apply AR derivations if any
            added_alg = []
            if derives:
                added_alg += dd.apply_derivations(g, derives)
            if eq4s:
                added_alg += dd.apply_derivations(g, eq4s)
            
            # Check goal again after applying AR
            goal_args = g.names2nodes(target_construction.args)
            if g.check(target_construction.name, goal_args):
                return True
            
            # If no new facts from DD or AR, we're saturated
            if not added and not added_alg:
                break
            
            level += 1

        # Final check
        goal_args = g.names2nodes(target_construction.args)
        return g.check(target_construction.name, goal_args)

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
                try:
                    p_temp = pr.Problem.from_txt(temp_context)
                    gh.Graph.build_problem(p_temp, self.defs, verbose=False)
                    current_context = temp_context  
                    print(f"  Step {step_num} (Construction): {step} [OK]")
                except Exception as e:
                    result["error_msg"] = f"Step {step_num} Construction Error: '{step}' -> {str(e)}"
                    result["steps_passed"] = i  # Failed at step i (0-indexed)
                    return result

            else:
                # Derivation step checking: BFS verification
                print(f"  Step {step_num} (Derivation): {step}")
                if self._run_bfs_check(current_context, step, max_level=1):
                    print(f"    [OK]")
                else:
                    result["error_msg"] = f"Step {step_num} Logic Gap: '{step}' not derivable from current context."
                    result["steps_passed"] = i  # Failed at step i (0-indexed)
                    return result
        print("All steps passed")
        # All steps passed
        result["steps_passed"] = len(steps)

        # 3. Final goal verification
        if not global_goal_dsl.strip():
            # No global goal (e.g., pure construction problem)
            result["is_valid"] = True
            result["goal_reached"] = True
            result["error_msg"] = "Verified (No global goal)."
            return result

        print(f"  Verifying Final Goal: {global_goal_dsl}")
        
        # For final goal, use larger max_level (e.g., 10)
        is_goal_reached = self._run_bfs_check(current_context, global_goal_dsl.strip(), max_level=10)

        if is_goal_reached:
            result["is_valid"] = True
            result["goal_reached"] = True
            result["error_msg"] = "Success: All proof steps valid and goal reached."
        else:
            result["is_valid"] = False  # final goal not reached
            result["goal_reached"] = False
            result["error_msg"] = "All steps valid, but final goal NOT reached."

        return result