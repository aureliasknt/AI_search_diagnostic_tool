"""Test keamanan util: masking, share code, password, enkripsi HP."""
from app.security import (decrypt_phone, encrypt_phone, hash_password,
                          mask_phone, new_share_code, new_sms_code,
                          valid_cn_mobile, verify_password)


def test_mask_phone():
    assert mask_phone("13800138000") == "138****8000"


def test_share_code_length_and_uniqueness():
    codes = {new_share_code() for _ in range(200)}
    assert all(len(c) >= 10 for c in codes)
    assert len(codes) == 200


def test_sms_code_format():
    assert len(new_sms_code()) == 6
    assert new_sms_code().isdigit()


def test_password_hash_roundtrip():
    stored = hash_password("rahasia123")
    assert verify_password("rahasia123", stored)
    assert not verify_password("salah", stored)


def test_phone_encryption_roundtrip():
    enc = encrypt_phone("13800138000")
    assert enc != "13800138000"
    assert decrypt_phone(enc) == "13800138000"


def test_valid_cn_mobile():
    assert valid_cn_mobile("13800138000")
    assert valid_cn_mobile("19912345678")
    assert not valid_cn_mobile("12345678901")
    assert not valid_cn_mobile("1380013800")
    assert not valid_cn_mobile("")
