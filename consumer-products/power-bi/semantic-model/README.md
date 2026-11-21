# Power BI semantic model

The [TMDL model](../NexusFinance/NexusFinance.SemanticModel/definition/model.tmdl)
is part of the [NexusFinance PBIP](../NexusFinance/NexusFinance.pbip).
It contains 19 tables and 15 relationships, including the two comparison
adapters. See the [Power BI workspace](../README.md) for the model's C2
manifest pin and Desktop refresh steps.

The model must pin one exact C2 delivery manifest and must not create a second
accounting or governed-truth authority.
