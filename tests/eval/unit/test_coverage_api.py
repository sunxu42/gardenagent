from eval.api.routes import build_coverage_response


def test_coverage_api_returns_sixteen_cells() -> None:
    response = build_coverage_response()
    assert len(response.cells) == 16


def test_coverage_api_filters_by_domain() -> None:
    response = build_coverage_response(domain="memory")
    assert all(cell.domain == "memory" for cell in response.cells)
    assert len(response.cells) == 2
