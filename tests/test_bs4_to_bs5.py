from scripts.bs4_to_bs5 import rewrite_html


def test_rewrites_data_toggle():
    src = '<a href="#" data-toggle="dropdown">x</a>'
    out = rewrite_html(src)
    assert 'data-bs-toggle="dropdown"' in out
    assert 'data-toggle=' not in out


def test_rewrites_data_target():
    src = '<button data-target="#foo">x</button>'
    assert 'data-bs-target="#foo"' in rewrite_html(src)


def test_rewrites_slide_attrs():
    src = '<a data-slide="prev">x</a><li data-slide-to="0">y</li>'
    out = rewrite_html(src)
    assert 'data-bs-slide="prev"' in out
    assert 'data-bs-slide-to="0"' in out


def test_rewrites_text_left_class():
    src = '<div class="text-left mb-3">x</div>'
    out = rewrite_html(src)
    assert 'text-start' in out
    assert 'text-left' not in out


def test_rewrites_margin_classes():
    src = '<div class="ml-1 mr-3 pl-2 pr-4">x</div>'
    out = rewrite_html(src)
    assert 'ms-1' in out and 'me-3' in out and 'ps-2' in out and 'pe-4' in out
    assert 'ml-1' not in out and 'pr-4' not in out


def test_rewrites_form_row_and_form_group():
    src = '<div class="form-row"><div class="form-group">x</div></div>'
    out = rewrite_html(src)
    assert 'row' in out and 'g-2' in out
    assert 'mb-3' in out
    assert 'form-group' not in out


def test_rewrites_sr_only():
    src = '<span class="sr-only">screen readers</span>'
    out = rewrite_html(src)
    assert 'visually-hidden' in out
    assert 'sr-only' not in out


def test_rewrites_badge():
    src = '<span class="badge badge-info">3</span>'
    out = rewrite_html(src)
    assert 'bg-info' in out
    assert 'text-white' in out
    assert 'badge-info' not in out


def test_rewrites_font_awesome_bars():
    src = '<i class="fa fa-bars"></i>'
    out = rewrite_html(src)
    assert 'bi-list' in out
    assert 'fa-bars' not in out
    assert 'bi ' in out or 'bi"' in out


def test_does_not_rewrite_inside_pre_or_code():
    src = '<pre><code>data-toggle="dropdown"</code></pre>'
    out = rewrite_html(src)
    assert 'data-toggle="dropdown"' in out
    assert 'data-bs-toggle' not in out


def test_replaces_jumbotron_with_content_card():
    src = '<div class="jumbotron pagejumbotron">body</div>'
    out = rewrite_html(src)
    assert 'content-card' in out
    assert 'jumbotron' not in out


def test_replaces_mainjumbotron_with_hero():
    src = '<div class="jumbotron mainjumbotron">body</div>'
    out = rewrite_html(src)
    assert 'hero' in out
    assert 'jumbotron' not in out
