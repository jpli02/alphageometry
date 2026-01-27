import dd
import graph as gh
import problem as pr

class ProofVerifier:
    def __init__(self, defs_path="defs.txt", rules_path="rules.txt"):
        self.defs = pr.Definition.from_txt_file(defs_path, to_dict=True)
        self.rules_dict = pr.Theorem.from_txt_file(rules_path, to_dict=True)
        self.rules_list = list(self.rules_dict.values())

    def _is_construction(self, dsl: str) -> bool:
        return "=" in dsl

    def _parse_predicate(self, predicate_str: str) -> tuple[str, list[str]]:
        """Parse a predicate string into (name, args)."""
        parts = predicate_str.strip().split()
        if len(parts) < 2:
            raise ValueError(f"Invalid predicate format: {predicate_str}")
        name = parts[0]
        # Remove trailing commas from arguments
        args = [arg.strip(",") for arg in parts[1:]]
        return name, args

    def _add_verified_predicates_to_graph(self, g: gh.Graph, context_str: str) -> None:
        """Add previously verified predicates to the graph."""
        clauses = [c.strip() for c in context_str.split(';') if c.strip()]
        
        for clause in clauses:
            if ' = ' in clause:
                continue
            try:
                pred_name, pred_args = self._parse_predicate(clause)
                try:
                    nodes = g.names2nodes(pred_args)
                except KeyError:
                    continue
                except Exception:
                    continue
                
                if not g.check(pred_name, nodes):
                    deps = pr.EmptyDependency(level=0, rule_name="verified")
                    try:
                        g.add_piece(pred_name, nodes, deps=deps)
                    except ValueError:
                        pass
            except (ValueError, Exception):
                continue

    def _run_bfs_check(self, context_str: str, target_predicate_str: str, max_level=2) -> bool:
        """
        Check if target is derivable from context using incremental deepening.
        Wraps dd.bfs_one_level in try/except to prevent solver crashes.
        """
        target_predicate_str = target_predicate_str.strip().rstrip(";")
        context_str = context_str.strip().rstrip(";")
        
        try:
            temp_prob_txt = f"{context_str} ? {target_predicate_str}"
            p = pr.Problem.from_txt(temp_prob_txt)
            
            try:
                g, _ = gh.Graph.build_problem(p, self.defs, verbose=False)
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

        # Incremental deepening
        for level in range(1, max_level + 1):
            if goal_holds():
                return True

            try:
                # Run the solver for one level
                # nm_check=True helps avoid bad geometry, but doesn't catch all logic errors
                added, derives, eq4s, _ = dd.bfs_one_level(
                    g,
                    self.rules_dict,
                    level,
                    p,
                    verbose=False,
                    nm_check=True,
                    timeout=30,
                )

                if derives:
                    dd.apply_derivations(g, derives)
                if eq4s:
                    dd.apply_derivations(g, eq4s)
            
            except Exception as e:
                # CRITICAL FIX: Catch solver crashes (like "ab and ab Cannot be perp")
                # If the solver crashes at this level, we assume this path is invalid.
                print(f"  [Solver Error at Level {level}] {type(e).__name__}: {e}")
                # Depending on strictness, we can either continue to next level or return False.
                # Usually a crash means the graph state is corrupted or inconsistent.
                return False

        return goal_holds()

    def verify_proof(self, problem_txt: str, proof_dsl: str) -> dict:
        result = {
            "is_valid": False,
            "error_msg": "",
            "steps_passed": 0,
            "goal_reached": False
        }

        # 1. Parse Problem
        if "?" in problem_txt:
            prems, global_goal_dsl = problem_txt.split("?", 1)
        else:
            prems, global_goal_dsl = problem_txt, ""
        
        current_context = prems.strip()
        
        # 2. Parse Proof Steps (Handling commas as separators for non-constructions)
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

        # 3. Verify Sequentially
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
                
                # Check derivation
                if self._run_bfs_check(current_context, clean_step, max_level=10):
                    print(f"    [OK]")
                    current_context = f"{current_context}; {clean_step}"
                else:
                    result["error_msg"] = f"Step {step_num} Logic Gap: '{step}' not derivable from current context."
                    result["steps_passed"] = i
                    return result
        
        print("All steps passed")
        result["steps_passed"] = len(steps)

        # 4. Global Goal Check
        if not global_goal_dsl.strip():
            result["is_valid"] = True
            result["goal_reached"] = True
            result["error_msg"] = "Verified (No global goal)."
            return result
        
        print(f"Checking Final Goal: {global_goal_dsl.strip()}")
        is_goal_reached = self._run_bfs_check(current_context, global_goal_dsl.strip(), max_level=12)
        
        if is_goal_reached:
            result["is_valid"] = True
            result["goal_reached"] = True
            result["error_msg"] = "Success: All proof steps valid and goal reached."
        else:
            result["is_valid"] = False
            result["goal_reached"] = False
            result["error_msg"] = "All steps valid, but final goal NOT reached."

        return result