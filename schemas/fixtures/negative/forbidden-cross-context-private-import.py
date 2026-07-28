# expected_error: TOPOLOGY_PRIVATE_CROSS_CONTEXT_IMPORT
from ranex.policy.domain.roles import Role

def use_private_role(role: Role) -> Role:
    return role
