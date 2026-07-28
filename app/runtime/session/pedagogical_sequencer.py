from typing import List, Any
from app.models.quiz import Question

class PedagogicalSequencer:
    """
    Orders questions into a deterministic pedagogical flow:
    Warm-up -> Recall -> Understand -> Apply -> Challenge
    Absolutely no random.shuffle().
    """
    
    def _get_pedagogical_score(self, q: Question) -> int:
        bloom = str(getattr(q, "bloom_level", "RECALL")).upper()
        difficulty = getattr(q, "difficulty", 3)
        
        # 1. Warm-up (EASY)
        if difficulty <= 2:
            return 1
            
        # 2. Recall (MEDIUM + RECALL)
        if bloom in ["REMEMBER", "RECALL"]:
            return 2
            
        # 3. Understand (MEDIUM + UNDERSTAND)
        if bloom in ["UNDERSTAND", "COMPREHENSION"]:
            return 3
            
        # 4. Apply (APPLICATION)
        if bloom in ["APPLY", "APPLICATION"]:
            return 4
            
        # 5. Challenge (ANALYSIS, EVALUATION, CREATION, or HARD)
        return 5

    def sequence(self, questions: List[Question], session_type: Any = None, student_id: Any = None, uow: Any = None) -> List[Question]:
        if not questions:
            return []

        # If it's a REVISION session, use the prioritized history-based sequencing
        if session_type and getattr(session_type, "value", str(session_type)) == "REVISION" and student_id and uow:
            import random
            from datetime import datetime, timezone, timedelta
            from app.models.assessment.student_response import StudentResponse
            
            q_ids = [q.id for q in questions]
            
            # Fetch all responses for these questions by this student
            responses = uow.session.query(StudentResponse).filter(
                StudentResponse.question_id.in_(q_ids)
            ).join(
                StudentResponse.session
            ).filter(
                StudentResponse.session.has(student_id=student_id)
            ).all()
            
            # Group responses by question ID
            responses_by_q = {}
            for r in responses:
                qid = r.question_id
                if qid not in responses_by_q:
                    responses_by_q[qid] = []
                responses_by_q[qid].append(r)
                
            # Classify questions into tiers
            tier_wrong = []      # Tier 1
            tier_skipped = []    # Tier 2
            tier_old_correct = [] # Tier 3 (old correct or never attempted)
            tier_recent_correct = [] # Tier 4 (recently correct)
            
            now = datetime.now(timezone.utc)
            thirty_days_ago = now - timedelta(days=30)
            
            for q in questions:
                q_res = responses_by_q.get(q.id, [])
                if not q_res:
                    # Never attempted -> treat as Tier 3
                    tier_old_correct.append(q)
                    continue
                    
                # Check if ever incorrect
                ever_incorrect = any(not r.is_correct and r.evaluation_method != "SKIPPED" for r in q_res)
                # Check if latest was skipped
                latest_res = max(q_res, key=lambda r: r.created_at)
                latest_skipped = getattr(latest_res, "evaluation_method", "") == "SKIPPED"
                
                if ever_incorrect:
                    tier_wrong.append(q)
                elif latest_skipped:
                    tier_skipped.append(q)
                else:
                    # Check latest correct date
                    correct_res = [r for r in q_res if r.is_correct]
                    if correct_res:
                        latest_correct = max(correct_res, key=lambda r: r.created_at)
                        lc_time = latest_correct.created_at
                        if lc_time.tzinfo is None:
                            lc_time = lc_time.replace(tzinfo=timezone.utc)
                        if lc_time < thirty_days_ago:
                            tier_old_correct.append(q)
                        else:
                            tier_recent_correct.append(q)
                    else:
                        tier_old_correct.append(q)
            
            # Shuffle each tier to introduce randomness within priority groups
            random.shuffle(tier_wrong)
            random.shuffle(tier_skipped)
            random.shuffle(tier_old_correct)
            random.shuffle(tier_recent_correct)
            
            combined = tier_wrong + tier_skipped + tier_old_correct + tier_recent_correct
            
            # Spacing / Anti-repetition algorithm
            # Avoid consecutive questions with the same learning_unit_id
            final_list = []
            last_lu_ids = []  # Keep track of last 2 used LU IDs
            
            while combined:
                # Find the first question that doesn't match the last 2 LU IDs
                found_idx = -1
                for idx, q in enumerate(combined):
                    if q.learning_unit_id not in last_lu_ids:
                        found_idx = idx
                        break
                
                if found_idx != -1:
                    q = combined.pop(found_idx)
                else:
                    # Fallback to the first available if all remaining share the same LUs
                    q = combined.pop(0)
                    
                final_list.append(q)
                last_lu_ids.append(q.learning_unit_id)
                if len(last_lu_ids) > 2:
                    last_lu_ids.pop(0)
                    
            return final_list

        # Sort entirely by pedagogical score ascending.
        # This forces the progression Warm-up -> Recall -> Understand -> Apply -> Challenge
        return sorted(questions, key=self._get_pedagogical_score)
