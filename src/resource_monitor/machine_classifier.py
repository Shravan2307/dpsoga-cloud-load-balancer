from enum import Enum
class MachineState(str, Enum): IDLE_LOAD='IL'; OVERLOADED='OL'; UNDERLOADED='UL'; FREE_HOST='FH'
def classify_machine(score, free_epsilon=1e-9, underloaded=0.35, overloaded=0.80):
    if score <= free_epsilon: return MachineState.FREE_HOST.value
    if score >= overloaded: return MachineState.OVERLOADED.value
    if score <= underloaded: return MachineState.UNDERLOADED.value
    return MachineState.IDLE_LOAD.value
