"""Tests for the VCFExtractor class."""

import builtins
import sys
from pathlib import Path

import pytest
import vobject

from convert_anything_md.extractors.base import ExtractorError
from convert_anything_md.extractors.vcf import VCFExtractor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def create_vcard(overrides=None) -> vobject.vCard:
    """Create a baseline vCard and apply optional attribute overrides."""
    overrides = dict(overrides or {})

    def set_property(name, value):
        normalized = name.upper()
        if normalized == "N":
            if isinstance(value, dict):
                value = vobject.vcard.Name(**value)
        elif normalized == "ADR" and isinstance(value, dict):
            value = vobject.vcard.Address(**value)

        if isinstance(value, list):
            if normalized in {"ORG", "CATEGORIES"}:
                prop = vcard.add(normalized.lower())
                prop.value = value
                return

            for item in value:
                if isinstance(item, tuple) and len(item) == 2:
                    prop = vcard.add(normalized.lower())
                    prop.value = item[1]
                    prop.type_param = item[0]
                else:
                    prop = vcard.add(normalized.lower())
                    prop.value = item
            return

        if (isinstance(value, tuple) and
            len(value) == 2 and
            isinstance(value[0], str)):
            prop = vcard.add(normalized.lower())
            prop.value = value[1]
            prop.type_param = value[0]
            return

        prop = vcard.add(normalized.lower())
        prop.value = value

    vcard = vobject.vCard()

    set_property("VERSION", overrides.pop("VERSION", "4.0"))
    set_property("FN", overrides.pop("FN", "Bruce Wayne"))
    set_property(
        "N",
        overrides.pop(
            "N",
            {
                "family": "Wayne",
                "given": "Bruce",
                "additional": "Thomas",
                "prefix": "Mr.",
                "suffix": "Esq.",
            },
        ),
    )
    set_property("NICKNAME", overrides.pop("NICKNAME", "Batman, The Dark Knight"))
    set_property(
        "PHOTO",
        overrides.pop("PHOTO", ("URI", "https://justiceleague.org"))
    )
    set_property("BDAY", overrides.pop("BDAY", "1939-03-30"))
    set_property("ANNIVERSARY", overrides.pop("ANNIVERSARY", "1940-04-25"))
    set_property("GENDER", overrides.pop("GENDER", "M"))
    set_property("PRONOUNS", overrides.pop("PRONOUNS", "he/him"))
    set_property("GRAMGENDER", overrides.pop("GRAMGENDER", "MASCULINE"))
    set_property(
        "ADR",
        overrides.pop(
            "ADR",
            {
                "street": "1007 Mountain Drive",
                "city": "Gotham",
                "region": "NJ",
                "code": "07001",
                "country": "USA",
                "box": "",
                "extended": "",
            },
        ),
    )
    set_property("TEL", overrides.pop("TEL", [("CELL", "+1-555-468-6228")]))
    set_property("EMAIL", overrides.pop("EMAIL", [("WORK", "bruce@waynecorp.com")]))
    set_property("IMPP", overrides.pop("IMPP", [("WORK", "xmpp:batman@jabber.org")]))
    set_property("LANG", overrides.pop("LANG", "en-US"))
    set_property("GEO", overrides.pop("GEO", "geo:40.730610,-73.935242"))
    set_property("TZ", overrides.pop("TZ", "America/New_York"))
    set_property("TITLE", overrides.pop("TITLE", "CEO"))
    set_property("ROLE", overrides.pop("ROLE", "Chairman"))
    set_property("MEMBER", overrides.pop("MEMBER", "uuid:league-id-007"))
    set_property(
        "RELATED",
        overrides.pop("RELATED", [("co-worker", "uuid:alfred-id-101")])
    )
    set_property("ORG", overrides.pop("ORG", ["Wayne Enterprises", "Tech Division"]))
    set_property(
        "LOGO",
        overrides.pop("LOGO", ("URI", "https://wayneenterprises.com"))
    )
    set_property("CATEGORIES", overrides.pop("CATEGORIES", ["Billionaire", "Hero"]))
    set_property(
        "NOTE",
        overrides.pop("NOTE", "High-profile billionaire tech investor.")
    )
    set_property(
        "SOUND",
        overrides.pop("SOUND", ("URI", "https://wayneenterprises.com"))
    )
    set_property("SOCIALPROFILE", overrides.pop("SOCIALPROFILE", "https://x.com"))
    set_property("URL", overrides.pop("URL", "https://wayneenterprises.com"))
    set_property(
        "CALADRURI",
        overrides.pop("CALADRURI", "mailto:bruce@waynecorp.com")
    )
    set_property("CALURI", overrides.pop("CALURI", "webcal://://waynecorp.com"))
    set_property("FBURL", overrides.pop("FBURL", "https://waynecorp.com"))
    set_property("SOURCE", overrides.pop("SOURCE", "ldap://://waynecorp.com"))
    set_property("KIND", overrides.pop("KIND", "individual"))
    set_property(
        "XML",
        overrides.pop(
            "XML",
            "<customData xmlns='http://example.com'>Batman</customData>"
        )
    )
    set_property(
        "PRODID",
        overrides.pop("PRODID", "-//Custom Enterprise Generator V1.0//EN")
    )
    set_property("REV", overrides.pop("REV", "2026-08-06T21:24:00Z"))
    set_property(
        "UID",
        overrides.pop("UID", "urn:uuid:f81d4fae-7dec-11d0-a765-00a0c91e6bf6")
    )
    set_property(
        "CLIENTPIDMAP",
        overrides.pop(
            "CLIENTPIDMAP",
            "1;urn:uuid:53e374d9-317a-48da-a156-cb31a1ec329e"
        ),
    )
    set_property("KEY", overrides.pop("KEY", ("URI", "https://waynecorp.com")))

    for attr, value in overrides.items():
        set_property(attr, value)

    return vcard


def write_and_extract(vcard: vobject.vCard, tmp_path: Path):
    path = tmp_path / "test.vcf"
    path.write_text(vcard.serialize(), encoding="utf-8")
    return VCFExtractor().extract(str(path))


def write_text_and_extract(vcard_text: str, tmp_path: Path):
    path = tmp_path / "test.vcf"
    path.write_text(vcard_text, encoding="utf-8")
    return VCFExtractor().extract(str(path))


def test_valid_vcf_extraction(tmp_path: Path):
    result = write_and_extract(create_vcard(), tmp_path)

    assert result.markdown.startswith("## Bruce Wayne")
    assert "vCard Version: 4.0" in result.markdown


def test_vcf_accepts_non_default_version_3p0(tmp_path: Path):
    result = write_and_extract(
        create_vcard(overrides={"VERSION": "3.0", "FN": "Clark Kent"}),
        tmp_path,
    )

    assert result.markdown.startswith("## Clark Kent")
    assert "vCard Version: 3.0" in result.markdown


def test_vcf_accepts_non_default_version_2p1(tmp_path: Path):
    result = write_and_extract(
        create_vcard(overrides={"VERSION": "2.1", "FN": "Clark Kent"}),
        tmp_path,
    )

    assert result.markdown.startswith("## Clark Kent")
    assert "vCard Version: 2.1" in result.markdown


def test_vcf_accepts_non_default_version_5p0(tmp_path: Path):
    """This test shows that if vcards are updated
    in the future, any version number works"""
    result = write_and_extract(
        create_vcard(overrides={"VERSION": "5.0", "FN": "Clark Kent"}),
        tmp_path,
    )
    assert result.markdown.startswith("## Clark Kent")
    assert "vCard Version: 5.0" in result.markdown


def test_vcf_renders_custom_attribute(tmp_path: Path):
    # This test shows that any custom value works and will show up in the md file
    result = write_and_extract(
        create_vcard(overrides={"X-CUSTOM": "made up value"}),
        tmp_path
    )

    assert "**X-CUSTOM:** made up value" in result.markdown


def test_vcf_renders_multiple_attribute_with_types(tmp_path: Path):
    # Shows that multiple instances of any attribute works
    result = write_and_extract(
        create_vcard(
            overrides={
                "EMAIL": [
                    ("WORK", "bruce@waynecorp.com"),
                    ("HOME", "batcave@wayne.com"),
                ]
            }
        ),
        tmp_path,
    )
    assert "WORK: bruce@waynecorp.com" in result.markdown
    assert "HOME: batcave@wayne.com" in result.markdown

    result = write_and_extract(
        create_vcard(
            overrides={
                "GEO": [
                    ("FORTRESSOFSOLITUDE", "76.2N 100.4W"),
                    ("METROPOLIS", "37.1511N -88.7319W"),
                ]
            }
        ),
        tmp_path,
    )
    assert "FORTRESSOFSOLITUDE: 76.2N 100.4W" in result.markdown
    assert "METROPOLIS: 37.1511N -88.7319W" in result.markdown


def test_vcf_renders_multiple_attribute_without_types(tmp_path: Path):
    # Shows that multiple instances of any attribute works
    result = write_and_extract(
        create_vcard(
            overrides={"EMAIL": [
                ("WORK:", "bruce@waynecorp.com"),
                ("batcave@wayne.com")
            ]}
        ),
        tmp_path,
    )
    assert "WORK:" in result.markdown
    assert "  - batcave@wayne.com" in result.markdown


def test_missing_version_raises(tmp_path: Path):
    # Version is required and vcard is not valid if it is missing
    vcard_text = create_vcard().serialize()
    text_without_version = "\n".join(
        line for line in vcard_text.splitlines() if not line.startswith("VERSION:")
    )

    with pytest.raises(ExtractorError, match="missing VERSION field"):
        write_text_and_extract(text_without_version + "\n", tmp_path)


def test_missing_fn_raises(tmp_path: Path):
    # Full Name is required and vcard is not valid if it is missing
    vcard_text = create_vcard().serialize()
    text_without_fn = "\n".join(
        line for line in vcard_text.splitlines() if not line.startswith("FN:")
    )

    with pytest.raises(ExtractorError, match="missing FN"):
        write_text_and_extract(text_without_fn + "\n", tmp_path)


def test_read_error_raises(tmp_path: Path, monkeypatch):
    # Simulate a file read failure after the initial content checks.
    vcard_text = create_vcard().serialize()
    path = tmp_path / "test.vcf"
    path.write_text(vcard_text, encoding="utf-8")

    original_open = builtins.open
    call_counts = {"count": 0}

    def fake_open(file, mode="r", encoding=None, *args, **kwargs):
        if file == str(path) and mode == "r":
            call_counts["count"] += 1
            if call_counts["count"] == 2:
                raise OSError("filesystem broken")
        return original_open(
            file,
            mode,
            *args,
            **kwargs,
            encoding=encoding
        )  # noqa: B026

    monkeypatch.setattr(builtins, "open", fake_open)

    with pytest.raises(ExtractorError, match="Failed to read file"):
        VCFExtractor().extract(str(path))


def test_parse_error_raises(tmp_path: Path, monkeypatch):
    # Simulate an invalid vCard parse error after reading the file.
    bad_text = "VERSION:4.0\nFN:Test\nINVALID"
    path = tmp_path / "test.vcf"
    path.write_text(bad_text, encoding="utf-8")

    with pytest.raises(ExtractorError, match="Failed to parse vCard data"):
        VCFExtractor().extract(str(path))


def test_list_value_single_item_renders_as_multiline(tmp_path: Path):
    # A single ORG property with a list value renders each list item on its own line.
    vcard = create_vcard(overrides={"ORG": ["Wayne Enterprises", "Tech Division"]})
    result = write_and_extract(vcard, tmp_path)

    assert "- **Organization:**" in result.markdown
    assert "- Wayne Enterprises" in result.markdown
    assert "- Tech Division" in result.markdown
