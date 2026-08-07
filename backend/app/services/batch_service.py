from app.schemas import BatchStatus


VALID_TRANSITIONS: dict[BatchStatus, set[BatchStatus]] = {
    BatchStatus.QUEUED: {
        BatchStatus.PROCESSING,
    },
    BatchStatus.PROCESSING: {
        BatchStatus.COMPLETED,
        BatchStatus.FAILED,
    },
    BatchStatus.COMPLETED: set(),
    BatchStatus.FAILED: set(),
}


def is_valid_transition(
    current_status: BatchStatus,
    new_status: BatchStatus,
) -> bool:
    return new_status in VALID_TRANSITIONS.get(current_status, set())