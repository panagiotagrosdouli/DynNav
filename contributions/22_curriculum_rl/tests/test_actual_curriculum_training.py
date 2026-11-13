import importlib.util
from pathlib import Path
import sys

import pytest

pytest.importorskip('torch')
path = Path(__file__).resolve().parents[1] / 'curriculum_rl.py'
spec = importlib.util.spec_from_file_location('c22_actual_training', path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_curriculum_uses_actual_ppo_updates_and_records_episode_stage(tmp_path):
    log = module.run_curriculum_training(n_episodes=2, out_csv=str(tmp_path / 'training.csv'), seed=25)
    assert len(log) == 2
    assert all(row['policy_update_l2'] > 0 for row in log)
    assert all('value_loss' in row and 'policy_loss' in row for row in log)
    assert all(row['stage'] == 'easy' for row in log)
    repeated = module.run_curriculum_training(n_episodes=2, out_csv=str(tmp_path / 'repeat.csv'), seed=25)
    assert log == repeated


def test_unimplemented_reverse_strategy_is_explicit():
    with pytest.raises(NotImplementedError, match='Reverse'):
        module.CurriculumScheduler(strategy=module.CurriculumStrategy.REVERSE)
