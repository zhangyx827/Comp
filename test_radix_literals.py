from compiler.compiler import Compiler


def test_radix_integer_literals():
    compiler = Compiler()
    code = """int main() {
    int a = 0x10 + 0b10 + 0o7;
    return a;
}"""

    result = compiler.compile(code)

    assert result["success"], result.get("errors")

    tokens = result["lexer_result"]["tokens"]
    literal_values = [t["value"] for t in tokens if t["type"] == "INTEGER_LITERAL"]
    assert literal_values == ["0x10", "0b10", "0o7"]

    ast = result["parser_result"]
    init_value = ast["children"][0]["children"][0]["value"]["value"]
    assert init_value == 25

    optimized_ast = result["optimization_result"]["optimized_ast"]
    optimized_init_value = optimized_ast["children"][0]["children"][0]["value"]["value"]
    assert optimized_init_value == 25
