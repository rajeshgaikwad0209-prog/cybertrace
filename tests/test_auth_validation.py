"""
Unit tests for app.core.auth validation logic.

Note: these tests import the auth module, which requires the `bcrypt`
package to be installed (see requirements.txt). Run with:
    pytest tests/test_auth_validation.py -v
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app.core.auth import validate_username, validate_password, AuthError, hash_password, verify_password


class TestUsernameValidation:
    def test_valid_username_passes(self):
        validate_username("john_doe-123")  # should not raise

    def test_too_short_username_rejected(self):
        with pytest.raises(AuthError):
            validate_username("ab")

    def test_too_long_username_rejected(self):
        with pytest.raises(AuthError):
            validate_username("a" * 33)

    def test_empty_username_rejected(self):
        with pytest.raises(AuthError):
            validate_username("")

    def test_special_characters_rejected(self):
        with pytest.raises(AuthError):
            validate_username("john@doe!")

    def test_spaces_rejected(self):
        with pytest.raises(AuthError):
            validate_username("john doe")


class TestPasswordValidation:
    def test_valid_password_passes(self):
        validate_password("correcthorsebattery")  # should not raise

    def test_too_short_password_rejected(self):
        with pytest.raises(AuthError):
            validate_password("short1")

    def test_empty_password_rejected(self):
        with pytest.raises(AuthError):
            validate_password("")

    def test_common_password_rejected(self):
        with pytest.raises(AuthError):
            validate_password("password")


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        pw = "correcthorsebattery"
        hashed = hash_password(pw)
        assert hashed != pw
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        pw = "correcthorsebattery"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_verify_incorrect_password(self):
        hashed = hash_password("correcthorsebattery")
        assert verify_password("wrongpassword", hashed) is False

    def test_hashes_are_salted_and_differ(self):
        pw = "correcthorsebattery"
        hash1 = hash_password(pw)
        hash2 = hash_password(pw)
        assert hash1 != hash2  # different salts
        assert verify_password(pw, hash1) is True
        assert verify_password(pw, hash2) is True

    def test_verify_handles_malformed_hash_gracefully(self):
        assert verify_password("anything", "not-a-real-hash") is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
