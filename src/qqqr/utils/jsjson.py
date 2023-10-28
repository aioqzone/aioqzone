import ast
import logging
from textwrap import dedent
from typing import Dict, List, Union

logger = logging.getLogger(__name__)
JsonDict = Dict[Union[str, int], "JsonValue"]
JsonList = List["JsonValue"]
JsonValue = Union[bool, int, str, JsonDict, JsonList]


class AstLoader:
    """`AstLoader` uses standard :mod:`ast` module to parse the js/json"""

    class RewriteUndef(ast.NodeTransformer):
        const = {
            "undefined": ast.Constant(value=None),
            "null": ast.Constant(value=None),
            "true": ast.Constant(value=True),
            "false": ast.Constant(value=False),
        }

        def visit_Name(self, node: ast.Name):
            if node.id in self.const:
                return self.const[node.id]
            return ast.Str(s=node.id)

    @classmethod
    def json_loads(cls, js: str, filename: str = "stdin") -> JsonValue:
        """
        The json_loads function loads a JSON object from a js/json string. It uses standard
        :mod:`ast` module to parse the js/json.

        :param js: Used to Pass the js/json string to be parsed.
        :param filename: Used to Specify the name of the file that is being read. This is only for debug use.
        :return: A jsonvalue object.
        """
        js = dedent(js).replace(r"\/", "/")
        node = ast.parse(js, mode="eval")
        node = ast.fix_missing_locations(cls.RewriteUndef().visit(node))
        code = compile(node, filename, mode="eval")
        return eval(code)


def json_loads(js: str) -> JsonValue:
    """The json_loads function converts a string representation of JS/JSON data into a Python object.
    Current implementation is using :external+python:mod:`ast`.

    If you need more parameters or another implementation, call `xxxLoader.json_loads` instead.

    .. seealso:: :meth:`.AstLoader.json_loads`

    :param js: Used to Pass the JS/JSON string.
    :return: A jsonvalue object.
    """
    return AstLoader.json_loads(js)
