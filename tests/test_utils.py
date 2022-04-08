from thishappened.renderer.utils import text_warp, text_grab


def test_text_warp():
    input_text = "This is a long line, that contains more than one sentence. This is the second sentence."
    output = text_warp(input_text, 20, language='en')

    assert len(output) > 1


def test_text_grab():
    input_text = "This is a long line, that contains more than one sentence. This is the second sentence."

    output, rest = text_grab(input_text, 20, language='en')

    assert len(output) > 1
    assert output == input_text[0:20]
    assert rest is not None
    assert len(rest) > 1
    assert rest == input_text[21:]
    assert len(output) > 1
