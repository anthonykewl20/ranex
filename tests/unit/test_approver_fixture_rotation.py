"""Fixture authority rotation stays valid when a governed clone has an approver."""
import _approver
import pytest
import yaml

from ranex.foundation.signing import generate_keypair
from ranex.policy.adapters.configuration.yaml.principal_catalog import load_principals
from ranex.policy.adapters.configuration.yaml.producer_keyring import load_trust_keyring


def _keyring(tmp_path, role='approver'):
    _, worker = generate_keypair()
    _, service = generate_keypair()
    _, active = generate_keypair()
    _, retired = generate_keypair()
    document = {'producers': {'worker': worker},
                'verdict_signer': {'id': 'kernel-verdict-signer', 'public_key': service},
                'principals': {
                    'worker': {'role': 'worker', 'keys': [{'key': worker, 'status': 'active'}]},
                    'kernel-verdict-signer': {'role': 'service', 'keys': [{'key': service, 'status': 'active'}]},
                    'reviewer': {'role': role, 'keys': [{'key': active, 'status': 'active'},
                                                       {'key': retired, 'status': 'retired'}]},
                }}
    path = tmp_path / 'producers.yaml'
    path.write_text(yaml.safe_dump(document))
    return path, active, retired, worker


def test_fixture_rotation_retains_keys_and_catalog_consumer_accepts(tmp_path):
    path, active, retired, _ = _keyring(tmp_path)
    _, new = generate_keypair()
    _approver.register_approver(path, 'reviewer', new)
    trust = load_trust_keyring(path)
    catalog = load_principals(path)
    principal = catalog.principals['reviewer']
    assert trust.verdict_signer_id == 'kernel-verdict-signer'
    assert principal.role == 'approver'
    assert set(principal.active_keys) == {active, new}
    assert catalog.may_sign(retired) is False
    before = path.read_bytes()
    _approver.register_approver(path, 'reviewer', new)
    assert path.read_bytes() == before


@pytest.mark.parametrize('role', ['worker', 'service'])
def test_fixture_rotation_never_escalates_existing_principal_role(tmp_path, role):
    path, _, _, _ = _keyring(tmp_path, role=role)
    before = path.read_bytes()
    _, new = generate_keypair()
    with pytest.raises(ValueError):
        _approver.register_approver(path, 'reviewer', new)
    assert path.read_bytes() == before


def test_fixture_rotation_rejects_cross_principal_key_alias_without_writing(tmp_path):
    path, _, _, worker = _keyring(tmp_path)
    before = path.read_bytes()
    with pytest.raises(ValueError):
        _approver.register_approver(path, 'reviewer', worker)
    assert path.read_bytes() == before


def test_fixture_rotation_cannot_reactivate_retired_key(tmp_path):
    path, _, retired, _ = _keyring(tmp_path)
    before = path.read_bytes()
    with pytest.raises(ValueError):
        _approver.register_approver(path, 'reviewer', retired)
    assert path.read_bytes() == before
