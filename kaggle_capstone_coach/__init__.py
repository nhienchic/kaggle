"""Kaggle Capstone Submission Coach."""

__all__ = ["ReadinessReport", "run_readiness_workflow"]


def __getattr__(name: str):
    if name == "ReadinessReport":
        from .workflow import ReadinessReport

        return ReadinessReport
    if name == "run_readiness_workflow":
        from .workflow import run_readiness_workflow

        return run_readiness_workflow
    raise AttributeError(name)
