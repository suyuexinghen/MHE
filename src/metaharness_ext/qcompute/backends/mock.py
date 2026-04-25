from __future__ import annotations


class MockQuantumBackend:
    def __init__(self, deterministic_counts: dict[str, int]) -> None:
        self._counts = dict(deterministic_counts)

    def run(self, circuit: object, shots: int = 1024) -> dict[str, int]:
        del circuit, shots
        return dict(self._counts)
