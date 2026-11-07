import builtins

import pytest

from qqqr.utils.jsjson import json_loads


class TestJsJson:
    def test_js(self):
        s = """
        {
            usr: 'admin',
            pwd: 2333,
            admin: true
        }
        """
        d = json_loads(s)
        assert isinstance(d, dict)
        assert d["usr"] == "admin"
        assert d["pwd"] == 2333
        assert d["admin"] == True

    def test_null(self):
        s = """
        {
            extra: null,
            merge: [undefined],
        }
        """
        d = json_loads(s)
        assert isinstance(d, dict)
        assert d["extra"] is None
        assert d["merge"] == [None]

    def test_escape(self):
        s = r"{html:'http:\/\/qq.com'}"
        d = json_loads(s)
        assert isinstance(d, dict)
        assert d["html"] == "http://qq.com"


HOSTILE_PAYLOADS = [
    "'abc'.upper()",
    "'abc'.__class__",
    "{'a': 1}['a']",
    "(lambda: 1)()",
    "().__class__.__base__.__subclasses__()",
    "().__class__.__base__.__subclasses__()[0]",
    "f'{1}'",
]


class TestJsJsonSecurity:
    @pytest.mark.parametrize("payload", HOSTILE_PAYLOADS)
    def test_rejects_executable_expressions(self, payload):
        with pytest.raises((ValueError, SyntaxError)):
            json_loads(payload)

    def test_does_not_call_eval(self, monkeypatch):
        def _fail(*args, **kwargs):
            raise AssertionError("eval() must not be used")

        monkeypatch.setattr(builtins, "eval", _fail)
        assert json_loads("{a: 1}") == {"a": 1}


COMPLEX_JS = r"""
{
    code: 0,
    data: {
        feeds: [
            {
                id: 'feed-1',
                text: 'line1\nline2\ttab\r"quote"\'single\'<\/script> \x41\u4e2d',
                nums: [0, -1, 1.5, 1e-3, 0x1F, 0b1010, 0o17, 1_000],
                flags: [true, false, null, undefined],
                path: 'C:\\temp\\file',
                nested: {empty: {}, arr: [[], [1], [{x: null}]], u: undefined},
            },
        ],
        hasmore: true,
        attachinfo: '',
        count: 1,
    },
}
"""

COMPLEX_PY = {
    "code": 0,
    "data": {
        "feeds": [
            {
                "id": "feed-1",
                "text": "line1\nline2\ttab\r\"quote\"'single'</script> A中",
                "nums": [0, -1, 1.5, 0.001, 31, 10, 15, 1000],
                "flags": [True, False, None, None],
                "path": "C:\\temp\\file",
                "nested": {"empty": {}, "arr": [[], [1], [{"x": None}]], "u": None},
            }
        ],
        "hasmore": True,
        "attachinfo": "",
        "count": 1,
    },
}


class TestJsJsonComplex:
    def test_complex_nested_literal(self):
        assert json_loads(COMPLEX_JS) == COMPLEX_PY

    def test_unquoted_unicode_and_numeric_keys(self):
        assert json_loads("{中文: '值', _x: 1, a1: 2, 1: 'a', -2: 'b'}") == {
            "中文": "值",
            "_x": 1,
            "a1": 2,
            1: "a",
            -2: "b",
        }

    def test_bare_identifier_values_become_strings(self):
        assert json_loads("{a: foo, b: bar}") == {"a": "foo", "b": "bar"}

    def test_empty_containers(self):
        assert json_loads("{a: {}, b: [], c: [{}]}") == {"a": {}, "b": [], "c": [{}]}

    def test_duplicate_keys_last_wins(self):
        assert json_loads("{a: 1, a: 2}") == {"a": 2}

    def test_large_payload(self):
        n = 200
        items = ", ".join(
            f"{{id: {i}, text: 'item {i}', ok: true, score: {i}.5, tags: [1, 2, 3]}}"
            for i in range(n)
        )
        data = json_loads("[" + items + "]")
        assert len(data) == n
        assert data[0] == {
            "id": 0,
            "text": "item 0",
            "ok": True,
            "score": 0.5,
            "tags": [1, 2, 3],
        }
        assert data[-1]["id"] == n - 1
