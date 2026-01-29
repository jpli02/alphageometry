import dd
import graph as gh
import problem as pr
import collections

class ProofVerifier:
    def __init__(self, defs_path="defs.txt", rules_path="rules.txt"):
        self.defs = pr.Definition.from_txt_file(defs_path, to_dict=True)
        self.rules_dict = pr.Theorem.from_txt_file(rules_path, to_dict=True)
        self.rules_list = list(self.rules_dict.values())

    def _is_construction(self, dsl: str) -> bool:
        return "=" in dsl

    def _parse_predicate(self, predicate_str: str) -> tuple[str, list[str]]:
        parts = predicate_str.replace(',', ' ').split()
        if len(parts) < 2:
            raise ValueError(f"Invalid predicate format: {predicate_str}")
        return parts[0], parts[1:]

    def _add_verified_predicates_to_graph(self, g: gh.Graph, context_str: str) -> None:
        """
        Add previously verified predicates to the graph using apply_derivations.
        This ensures algebraic solvers (angles, ratios) are updated.
        """
        clauses = [c.strip() for c in context_str.split(';') if c.strip()]
        
        # Structure: {predicate_name: [(args_nodes, dependency_object), ...]}
        derived_facts = collections.defaultdict(list)
        
        dummy_dep = pr.EmptyDependency(level=0, rule_name="verified")

        for clause in clauses:
            # Skip constructions (handled by Graph.build_problem)
            if ' = ' in clause:
                continue
                
            try:
                pred_name, pred_args = self._parse_predicate(clause)
                
                try:
                    # Convert string args (e.g. "a", "b") to graph nodes (integers/objects)
                    nodes = g.names2nodes(pred_args)
                except (KeyError, Exception):
                    # If points don't exist in graph yet, skip.
                    continue
                
                # Check if this fact is already known to avoid redundancy
                if not g.check(pred_name, nodes):
                    derived_facts[pred_name].append((nodes, dummy_dep))
                    
            except (ValueError, Exception):
                continue

        # Apply the facts to the graph's algebraic engine
        if derived_facts:
            try:
                dd.apply_derivations(g, derived_facts)
            except Exception as e:
                print(f"  [Context Load Warning] Failed to apply some context: {e}")

    def _run_bfs_check(self, context_str: str, target_predicate_str: str, max_level=2) -> bool:
        target_predicate_str = target_predicate_str.strip().rstrip(";")
        context_str = context_str.strip().rstrip(";")
        
        try:
            # We treat the context + target as a temporary problem
            temp_prob_txt = f"{context_str} ? {target_predicate_str}"
            p = pr.Problem.from_txt(temp_prob_txt)
            
            try:
                # 1. Build graph from constructions (handled natively by build_problem)
                g, _ = gh.Graph.build_problem(p, self.defs, verbose=False)
                
                # 2. Manually apply the non-construction facts from context
                self._add_verified_predicates_to_graph(g, context_str)
                
            except Exception as e:
                print(f"  [Graph build failed] {type(e).__name__}: {e}")
                return False
        except Exception as e:
            print(f"  [Problem parse failed] {type(e).__name__}: {e}")
            return False

        if p.goal is None:
            return False

        def goal_holds() -> bool:
            try:
                goal_args = g.names2nodes(p.goal.args)
                return g.check(p.goal.name, goal_args)
            except (ValueError, KeyError, AttributeError):
                return False
            except Exception:
                return False

        # Incremental deepening BFS
        for level in range(1, max_level + 1):
            if goal_holds():
                return True

            try:
                added, derives, eq4s, _ = dd.bfs_one_level(
                    g,
                    self.rules_dict,
                    level,
                    p,
                    verbose=False,
                    nm_check=True,
                    timeout=300,
                )

                if derives:
                    dd.apply_derivations(g, derives)
                if eq4s:
                    dd.apply_derivations(g, eq4s)
            
            except ValueError as e:
                # Catch specific solver errors like "Cannot be perp"
                continue
            except Exception as e:
                print(f"  [Solver Error] {type(e).__name__}: {e}")
                return False

        return goal_holds()

    def verify_proof(self, problem_txt: str, proof_dsl: str) -> dict:
        result = {
            "is_valid": False,
            "error_msg": "",
            "steps_passed": 0,
            "goal_reached": False
        }

        if "?" in problem_txt:
            prems, global_goal_dsl = problem_txt.split("?", 1)
        else:
            prems, global_goal_dsl = problem_txt, ""
        
        current_context = prems.strip()
        
        raw_str = proof_dsl.replace('\n', ';')
        raw_segments = [s.strip() for s in raw_str.split(';') if s.strip()]
        
        steps = []
        for seg in raw_segments:
            if "=" in seg:
                steps.append(seg)
            else:
                sub_segments = [s.strip() for s in seg.split(',') if s.strip()]
                steps.extend(sub_segments)

        if not steps:
            result["error_msg"] = "No proof steps provided."
            return result

        print(f"--- Starting Verification (Steps: {len(steps)}) ---")

        for i, step in enumerate(steps):
            step_num = i + 1

            if self._is_construction(step):
                if step in current_context:
                    print(f"  Step {step_num} (Construction): {step} [Already in context]")
                else:
                    print(f"  Step {step_num} (Construction): {step} [Added]")
                    current_context = f"{current_context}; {step}"
            else:
                print(f"  Step {step_num} (Derivation): {step}")
                clean_step = step.rstrip(",;")
                
                # Check if derivable
                if self._run_bfs_check(current_context, clean_step, max_level=10):
                    print(f"    [OK]")
                    current_context = f"{current_context}; {clean_step}"
                else:
                    result["error_msg"] = f"Step {step_num} Logic Gap: '{step}' not derivable from current context."
                    result["steps_passed"] = i
                    return result
        
        result["steps_passed"] = len(steps)

        if not global_goal_dsl.strip():
            result["is_valid"] = True
            result["goal_reached"] = True
            result["error_msg"] = "Verified (No global goal)."
            return result
        
        # Verify Final Goal
        print(f"Checking Final Goal: {global_goal_dsl.strip()}")
        is_goal_reached = self._run_bfs_check(current_context, global_goal_dsl.strip(), max_level=10)
        
        if is_goal_reached:
            result["is_valid"] = True
            result["goal_reached"] = True
            result["error_msg"] = "Success: All proof steps valid and goal reached."
        else:
            result["is_valid"] = False
            result["goal_reached"] = False
            result["error_msg"] = "All steps valid, but final goal NOT reached."

        return result