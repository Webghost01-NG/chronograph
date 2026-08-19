import logging
from typing import List, Dict, Any, Optional

from chronograph.retrieval.temporal_ranker import RankedFact

logger = logging.getLogger(__name__)

class SubgraphContext:
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens

    def format_for_llm(self, facts: List[RankedFact], paths: Optional[List[Dict[str, Any]]] = None, temporal_chain: Optional[List[Dict[str, Any]]] = None) -> str:
        sections = []
        
        current_facts = [f for f in facts if f.is_current]
        hist_facts = [f for f in facts if not f.is_current]
        
        if current_facts:
            sections.append("[CURRENT FACTS]")
            for f in current_facts:
                sections.append(f"- {f.content} (Session: {f.session_id}, Valid From: {f.valid_from})")
                
        if hist_facts:
            sections.append("\n[HISTORICAL FACTS]")
            for f in hist_facts:
                sections.append(f"- {f.content} (Session: {f.session_id}, Valid: {f.valid_from} to {f.valid_to})")
                
        if paths:
            sections.append("\n[RELATIONSHIP PATHS]")
            for p in paths:
                sections.append(f"- {str(p)}")
                
        if temporal_chain:
            sections.append("\n[TEMPORAL CHAIN]")
            for tc in temporal_chain:
                sections.append(f"- {str(tc)}")
                
        result = "\n".join(sections)
        
        # very rough token estimation
        if len(result.split()) > self.max_tokens:
            logger.warning("Context truncated to fit max_tokens.")
            words = result.split()[:self.max_tokens]
            result = " ".join(words) + "...\n[TRUNCATED]"
            
        return result
