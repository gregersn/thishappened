from thishappened.renderer.utils import text_warp


def test_text_warp():
    input_text = "This is a long line, that contains more than one sentence. This is the second sentence."

    output = text_warp(input_text, 20, language='en')
    
    assert len(output) > 1
    