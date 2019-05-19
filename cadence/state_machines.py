from dataclasses import dataclass, field
from typing import Callable, List

from cadence.cadence_types import Decision, HistoryEvent
from cadence.decisions import DecisionState, DecisionId
from cadence.exceptions import IllegalStateException


class DecisionStateMachine:
    def get_decision(self) -> Decision:
        raise NotImplementedError

    def cancel(self, immediate_cancellation_callback: Callable) -> bool:
        raise NotImplementedError

    def handle_started_event(self, event: HistoryEvent):
        raise NotImplementedError

    def handle_cancellation_initiated_event(self):
        raise NotImplementedError

    def handle_cancellation_event(self):
        raise NotImplementedError

    def handle_cancellation_failure_event(self, event: HistoryEvent):
        raise NotImplementedError

    def handle_completion_event(self):
        raise NotImplementedError

    def handle_initiation_failed_event(self, event: HistoryEvent):
        raise NotImplementedError

    def handle_initiated_event(self, event: HistoryEvent):
        raise NotImplementedError

    def handle_decision_task_started_event(self):
        raise NotImplementedError

    def get_state(self) -> DecisionState:
        raise NotImplementedError

    def is_done(self) -> bool:
        raise NotImplementedError

    def get_id(self) -> DecisionId:
        raise NotImplementedError


# noinspection PyAbstractClass
@dataclass
class DecisionStateMachineBase(DecisionStateMachine):
    """
    This class has feature parity with the Java version even though it implements parts of features
    not yet implemented in the Python version.
    """
    id: DecisionId = None
    state: DecisionState = DecisionState.CREATED
    state_history: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.state_history.append(str(self))

    def get_state(self) -> DecisionState:
        return self.state

    def get_id(self) -> DecisionId:
        return self.id

    def is_done(self) -> bool:
        return self.state in (DecisionState.COMPLETED,
                              DecisionState.COMPLETED_AFTER_CANCELLATION_DECISION_SENT)

    def handle_decision_task_started_event(self):
        if self.state == DecisionState.CREATED:
            self.state_history.append("handle_decision_task_started_event")
            self.state = DecisionState.DECISION_SENT
            self.state_history.append(str(self.state))
        else:
            pass

    def cancel(self, immediate_cancellation_callback: Callable) -> bool:
        self.state_history.append("cancel")
        result = False
        if self.state == DecisionState.CREATED:
            self.state = DecisionState.COMPLETED
            if immediate_cancellation_callback:
                immediate_cancellation_callback()
        elif self.state == DecisionState.DECISION_SENT:
            self.state = DecisionState.CANCELED_BEFORE_INITIATED
            result = True
        elif self.state == DecisionState.INITIATED:
            self.state = DecisionState.CANCELED_AFTER_INITIATED
            result = True
        else:
            self.fail_state_transition()
        self.state_history.append(str(self.state))
        return result

    def handle_initiated_event(self, event: HistoryEvent):
        self.state_history.append("handle_initiated_event")
        if self.state == DecisionState.DECISION_SENT:
            self.state = DecisionState.INITIATED
        elif self.state == DecisionState.CANCELED_BEFORE_INITIATED:
            self.state = DecisionState.CANCELED_AFTER_INITIATED
        else:
            self.fail_state_transition()
        self.state_history.append(str(self.state))

    def handle_initiation_failed_event(self, event: HistoryEvent):
        self.state_history.append("handle_initiation_failed_event")
        if self.state in (
                DecisionState.INITIATED, DecisionState.DECISION_SENT, DecisionState.CANCELED_BEFORE_INITIATED):
            self.state = DecisionState.COMPLETED
        else:
            self.fail_state_transition()
        self.state_history.append(str(self.state))

    def handle_started_event(self, event: HistoryEvent):
        self.state_history.append("handle_started_event")

    def handle_completion_event(self):
        self.state_history.append("handle_completion_event")
        if self.state in (DecisionState.CANCELED_AFTER_INITIATED, DecisionState.INITIATED):
            self.state = DecisionState.COMPLETED
        elif self.state == DecisionState.CANCELLATION_DECISION_SENT:
            self.state = DecisionState.COMPLETED_AFTER_CANCELLATION_DECISION_SENT
        else:
            self.fail_state_transition()
        self.state_history.append(str(self.state))

    def handle_cancellation_initiated_event(self):
        self.state_history.append("handle_cancellation_initiated_event")
        if self.state == DecisionState.CANCELLATION_DECISION_SENT:
            # No state change
            pass
        else:
            self.fail_state_transition()
        self.state_history.append(str(self.state))

    def handle_cancellation_failure_event(self, event: HistoryEvent):
        self.state_history.append("handle_cancellation_failure_event")
        if self.state == DecisionState.COMPLETED_AFTER_CANCELLATION_DECISION_SENT:
            self.state = DecisionState.COMPLETED
        else:
            self.state.fail_state_transition()
        self.state_history.append(str(self.state))

    def handle_cancellation_event(self):
        self.state_history.append("handle_cancellation_event")
        if self.state == DecisionState.CANCELLATION_DECISION_SENT:
            self.state = DecisionState.COMPLETED
        else:
            self.fail_state_transition()
        self.state_history.append(str(self.state))

    def fail_state_transition(self):
        raise IllegalStateException("id=" + str(self.id) + ", transitions=" + str(self.state_history))
