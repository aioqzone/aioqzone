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
