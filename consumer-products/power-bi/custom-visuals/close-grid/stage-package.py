"""Stage the built P4 visual into the source PBIP and an isolated QA copy."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'shared'))
from stage import stage

print(stage(HERE, 'NexusFinance-P4-QA'))
