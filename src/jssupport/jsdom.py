from shutil import which
from textwrap import dedent

from .exception import JsImportError
from .execjs import ExecJS


class JSDOM(ExecJS):
    """.. note:: requires :js:mod:`jsdom` installed."""

    @classmethod
    def check_jsdom(cls):
        from subprocess import run

        require = lambda m: run(
            cls.node, executable=which(cls.node), input=f"require('{m}')", text=True
        )
        return require("jsdom").returncode == 0

    def check_all(self):
        super().check_all()
        if not self.check_jsdom():
            raise JsImportError("jsdom")

    def __init__(self, *, src: str = "", ua: str = "", location: str = "", referrer: str = ""):
        super().__init__()
        src = src.replace("\n", " ")
        pre_def = f"var src=`{src}`,ua='{ua}',location='{location}',referrer='{referrer}';\n"
        self.setup.append(pre_def)
        self.setup.append(self._windowjs())

    def _windowjs(self):
        """Override this if you have other js files."""

        js = """
        const jsdom = require("jsdom");
        const { JSDOM } = jsdom;
        const dom = new JSDOM(src, {
            pretendToBeVisual: true,
            url: location,
            referrer: referrer,
            userAgent: ua,
            pretendToBeVisual: true,
            runScripts: "outside-only",
        });
        dom.reconfigure({ windowTop: {} });
        window = dom.window;
        """
        return dedent(js)

    def eval(self, script: str):
        return self(f"window.eval(`{script}`)")

    def add_eval(self, script: str):
        self.add_run("window.eval", script)
