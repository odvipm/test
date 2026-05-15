import json
import pytest
from pathlib import Path


def test_save_and_get_credentials_via_keyring(mocker):
    mocker.patch("keyring.set_password")
    mocker.patch("keyring.get_password", side_effect=["user@test.com", "s3cr3t"])

    import auth
    auth.save_credentials("user@test.com", "s3cr3t")
    username, password = auth.get_credentials()

    assert username == "user@test.com"
    assert password == "s3cr3t"


def test_save_falls_back_to_file_when_keyring_unavailable(mocker, tmp_path, monkeypatch):
    mocker.patch("keyring.set_password", side_effect=Exception("keyring locked"))
    mocker.patch("keyring.get_password", side_effect=Exception("keyring locked"))

    import auth
    monkeypatch.setattr(auth, "CREDENTIALS_PATH", tmp_path / "credentials.json")

    auth.save_credentials("user@test.com", "s3cr3t")

    assert (tmp_path / "credentials.json").exists()
    data = json.loads((tmp_path / "credentials.json").read_text())
    assert data["username"] == "user@test.com"


def test_get_falls_back_to_file_when_keyring_returns_none(mocker, tmp_path, monkeypatch):
    mocker.patch("keyring.get_password", return_value=None)

    import auth
    monkeypatch.setattr(auth, "CREDENTIALS_PATH", tmp_path / "credentials.json")
    (tmp_path / "credentials.json").write_text(
        json.dumps({"username": "file_user", "password": "file_pass"})
    )

    username, password = auth.get_credentials()
    assert username == "file_user"
    assert password == "file_pass"


def test_get_raises_when_no_credentials_anywhere(mocker, tmp_path, monkeypatch):
    mocker.patch("keyring.get_password", return_value=None)

    import auth
    monkeypatch.setattr(auth, "CREDENTIALS_PATH", tmp_path / "no_creds.json")

    with pytest.raises(RuntimeError, match="No credentials found"):
        auth.get_credentials()
