from hashlib import sha256

from tools.dev.runtime_replay import replay


def test_replay_is_byte_identical_for_one_thousand_seeds() -> None:
    for seed in range(1000):
        output = replay(seed)
        assert output == replay(seed)


def test_seed_changes_action_stream() -> None:
    assert sha256(replay(1)).digest() != sha256(replay(2)).digest()
