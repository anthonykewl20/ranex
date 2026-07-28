# expected_error: TOPOLOGY_UNREGISTERED_DEPENDENCY_EDGE
from ranex.knowledge.api import KnowledgeView

def use_knowledge(view: KnowledgeView) -> KnowledgeView:
    return view
