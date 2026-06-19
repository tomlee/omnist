"""Format codecs: round-trip, cross-format transcode, and profile limits."""
import datetime
import json

import pytest

from dataspec import (
    read_json, write_json, check_json, read_yaml, write_yaml, check_yaml,
    read_toml, write_toml, check_toml, read_xml, write_xml, check_xml,
    WriteError, ParseError, WriteReport,
)

yaml = pytest.importorskip("yaml")
import tomllib  # noqa: E402  (3.11+)

SAMPLE = {
    "name": "Ann",
    "age": 30,
    "active": True,
    "ratio": 0.5,
    "tags": ["x", "y"],
    "zip": "999",                # a numeric-looking string stays a string
    "address": {"city": "HK", "nums": [1, 2, 3]},
}


# ---------------------------------------------------------------- JSON
class TestJson:
    def test_round_trip(self):
        assert read_json(write_json(SAMPLE)) == SAMPLE

    def test_type_fidelity(self):
        d = read_json(write_json({"i": 1, "f": 1.0, "b": True, "s": "1"}))
        assert d["i"] == 1 and isinstance(d["i"], int)
        assert isinstance(d["f"], float)
        assert d["b"] is True
        assert d["s"] == "1" and isinstance(d["s"], str)

    def test_null(self):
        assert read_json(write_json({"x": None})) == {"x": None}

    def test_datetime_downgrades_to_iso(self):
        out = write_json({"t": datetime.date(2024, 1, 1)})
        assert json.loads(out)["t"] == "2024-01-01"


# ---------------------------------------------------------------- YAML
class TestYaml:
    def test_round_trip(self):
        assert yaml.safe_load(write_yaml(SAMPLE)) == SAMPLE

    def test_read(self):
        assert read_yaml("name: Ann\ntags: [a, b]\n") == {"name": "Ann", "tags": ["a", "b"]}

    def test_null(self):
        assert read_yaml("x: null\n") == {"x": None}

    def test_rejects_non_string_keys(self):
        with pytest.raises(ParseError):
            read_yaml("1: a\n2: b\n")


# ---------------------------------------------------------------- TOML
class TestToml:
    def test_round_trip(self):
        assert tomllib.loads(write_toml(SAMPLE)) == SAMPLE

    def test_read(self):
        assert read_toml('a = 1\n[b]\nc = "x"\n') == {"a": 1, "b": {"c": "x"}}

    def test_datetime_native(self):
        d = {"created": datetime.datetime(2024, 1, 1, 12, 0)}
        assert tomllib.loads(write_toml(d)) == d

    def test_omits_null_field(self):
        # null Option C: a null object-field is omitted
        assert tomllib.loads(write_toml({"a": 1, "b": None})) == {"a": 1}

    def test_strict_rejects_null_field(self):
        with pytest.raises(WriteError):
            write_toml({"a": 1, "b": None}, strict=True)

    def test_drops_null_in_array_lenient(self):
        # lenient default: the null item is dropped, the rest survive
        assert tomllib.loads(write_toml({"xs": [1, None, 2]})) == {"xs": [1, 2]}

    def test_strict_rejects_null_in_array(self):
        with pytest.raises(WriteError):
            write_toml({"xs": [1, None, 2]}, strict=True)

    def test_wraps_top_level_non_object_lenient(self):
        # lenient default: a top-level array is wrapped under `wrap_key`
        assert tomllib.loads(write_toml([1, 2, 3])) == {"value": [1, 2, 3]}
        assert tomllib.loads(write_toml([1, 2], wrap_key="items")) == {"items": [1, 2]}

    def test_strict_rejects_top_level_non_object(self):
        with pytest.raises(WriteError):
            write_toml([1, 2, 3], strict=True)


# ---------------------------------------------------------------- XML
class TestXml:
    def test_round_trip_with_typing(self):
        data = {"name": "Ann", "age": 30, "active": True,
                "tags": ["x", "y"], "addr": {"city": "HK"}}
        assert read_xml(write_xml(data, root="rec")) == data

    def test_repeated_names_become_list(self):
        xml = "<r><item>1</item><item>2</item><other>x</other></r>"
        assert read_xml(xml) == {"item": [1, 2], "other": "x"}

    def test_rejects_attributes(self):
        with pytest.raises(ParseError):
            read_xml('<r><a x="1">v</a></r>')

    def test_rejects_mixed_content(self):
        with pytest.raises(ParseError):
            read_xml("<r>text<a>1</a></r>")

    def test_namespaces_stripped(self):
        assert read_xml('<r xmlns:n="urn:x"><n:a>1</n:a></r>') == {"a": 1}

    def test_omits_null_field(self):
        assert "<b>" not in write_xml({"a": 1, "b": None}, root="r")

    def test_drops_null_in_array_lenient(self):
        assert read_xml(write_xml({"xs": [1, None, 2]}, root="r")) == {"xs": [1, 2]}

    def test_strict_rejects_null_in_array(self):
        with pytest.raises(WriteError):
            write_xml({"xs": [1, None]}, root="r", strict=True)

    def test_wraps_top_level_array_lenient(self):
        assert read_xml(write_xml([1, 2, 3], wrap_key="items")) == {"items": [1, 2, 3]}

    def test_strict_rejects_top_level_array(self):
        with pytest.raises(WriteError):
            write_xml([1, 2, 3], strict=True)


# ---------------------------------------------------- cross-format transcode
class TestTranscode:
    def test_json_to_toml(self):
        toml = write_toml(read_json('{"name": "Ann", "tags": ["a", "b"]}'))
        assert tomllib.loads(toml) == {"name": "Ann", "tags": ["a", "b"]}

    def test_toml_to_json(self):
        out = write_json(read_toml('title = "t"\n[o]\nk = 1\n'))
        assert json.loads(out) == {"title": "t", "o": {"k": 1}}

    def test_json_to_yaml_to_json(self):
        original = '{"a": 1, "b": [true, null, "s"], "c": {"d": 2.5}}'
        back = read_yaml(write_yaml(read_json(original)))
        assert back == json.loads(original)

    def test_json_with_null_to_toml_omits(self):
        # a null field drops out of TOML (lenient default)
        out = write_toml(read_json('{"a": 1, "b": null}'))
        assert tomllib.loads(out) == {"a": 1}


# ---------------------------------------------------- adjustment reports
class TestReports:
    def test_clean_write_has_empty_report(self):
        rep = WriteReport()
        write_toml({"a": 1}, report=rep)
        assert rep.adjustments == []
        assert bool(rep) is True

    def test_check_does_not_produce_output(self):
        rep = check_toml({"a": 1, "b": None})
        assert isinstance(rep, WriteReport)
        codes = [a.code for a in rep]
        assert codes == ["null.field.omitted"]
        assert rep.warnings and not rep.errors
        assert bool(rep) is True            # warnings only -> still "safe"

    def test_null_array_item_is_an_error(self):
        rep = check_toml({"xs": [1, None, 2]})
        assert [a.code for a in rep.errors] == ["null.item.dropped"]
        assert rep.errors[0].path == "$.xs[1]"
        assert bool(rep) is False           # has an error -> not safe

    def test_null_style_drop_demotes_to_warning(self):
        rep = check_toml({"xs": [1, None]}, null_style="drop")
        assert rep.errors == []
        assert [a.code for a in rep.warnings] == ["null.item.dropped"]

    def test_report_arg_and_strict_share_events(self):
        rep = WriteReport()
        with pytest.raises(WriteError) as ei:
            write_toml({"xs": [1, None]}, strict=True, report=rep)
        # the collector is filled even on the strict path...
        assert [a.code for a in rep] == ["null.item.dropped"]
        # ...and the exception carries the same report
        assert ei.value.report.errors

    def test_json_temporal_and_special_float(self):
        rep = check_json({"when": datetime.date(2024, 1, 1), "x": float("nan")})
        codes = {a.code for a in rep}
        assert codes == {"temporal.stringified", "float.special"}
        assert any(a.severity == "error" for a in rep)     # nan is an error

    def test_yaml_time_downgrades(self):
        rep = check_yaml({"t": datetime.time(9, 30)})
        assert [a.code for a in rep] == ["temporal.stringified"]

    def test_xml_sanitizes_bad_key(self):
        rep = WriteReport()
        out = write_xml({"a b": 1}, root="r", report=rep)
        assert [a.code for a in rep] == ["key.sanitized"]
        assert "<a_b>" in out

    def test_xml_nested_array_is_error(self):
        rep = check_xml({"grid": [[1, 2], [3, 4]]}, root="r")
        assert any(a.code == "array.nested.ambiguous" for a in rep.errors)
