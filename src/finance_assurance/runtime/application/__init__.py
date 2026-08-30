"""Parameterised Milestone 2 application services."""

from importlib import import_module

__all__ = [
    "AccountingWorkflow",
    "CandidateAdmissionService",
    "CandidateAssessmentCommand",
    "CandidateAssessmentExecution",
    "CandidateReceipt",
    "EventCreations",
    "InMemoryObservationSink",
    "ModuleCommand",
    "ModuleContractService",
    "ProposalTreatmentVersion",
    "RuntimeQueryService",
    "ScriptedClock",
    "ScriptedIdentityGenerator",
]

_EXPORT_MODULES = {
    "AccountingWorkflow": ".models",
    "CandidateAdmissionService": ".admission",
    "CandidateAssessmentCommand": ".models",
    "CandidateAssessmentExecution": ".admission",
    "CandidateReceipt": ".models",
    "EventCreations": ".models",
    "InMemoryObservationSink": ".contracts",
    "ModuleCommand": ".contracts",
    "ModuleContractService": ".contracts",
    "ProposalTreatmentVersion": ".models",
    "RuntimeQueryService": ".queries",
    "ScriptedClock": ".models",
    "ScriptedIdentityGenerator": ".models",
}


def __getattr__(name: str) -> object:
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(name)
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value
