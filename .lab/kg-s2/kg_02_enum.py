"""State machine for a coffee machine."""
from __future__ import annotations

from enum import Enum, auto


class MachineState(Enum):
    OFF = auto()
    IDLE = auto()
    GRINDING = auto()
    BREWING = auto()
    ERROR = auto()


VALID_TRANSITIONS: dict[MachineState, frozenset[MachineState]] = {
    MachineState.OFF: frozenset({MachineState.IDLE}),
    MachineState.IDLE: frozenset({MachineState.GRINDING, MachineState.OFF}),
    MachineState.GRINDING: frozenset({MachineState.BREWING, MachineState.ERROR}),
    MachineState.BREWING: frozenset({MachineState.IDLE, MachineState.ERROR}),
    MachineState.ERROR: frozenset({MachineState.OFF}),
}


def transition(current: MachineState, target: MachineState) -> MachineState:
    if target not in VALID_TRANSITIONS[current]:
        raise ValueError(f"illegal transition {current.name} -> {target.name}")
    return target
