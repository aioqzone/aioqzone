from jssupport.jsjson import json_loads


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
        assert d['usr'] == 'admin'
        assert d['pwd'] == 2333
        assert d['admin']

    def test_null(self):
        s = """
        {
            extra: null
        }
        """
        d = json_loads(s)
        assert isinstance(d, dict)
        assert d['extra'] is None
