from io import BytesIO
from pathlib import Path

from PIL import Image
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[2] / "frontend/streamlit/app.py"


def by_label(elements, label):
    return next(element for element in elements if element.label == label)


def test_actual_service_starts_without_upload():
    app = AppTest.from_file(APP).run()
    assert not app.exception
    assert app.get("file_uploader")
    assert any("Upload a photo" in item.value for item in app.info)


def test_uploaded_flow_and_invalid_layout_keep_individual_download(monkeypatch):
    image = BytesIO()
    Image.new("RGB", (320, 400), "white").save(image, "PNG")
    upload = BytesIO(image.getvalue())
    upload.name = "portrait.png"
    monkeypatch.setattr("streamlit.file_uploader", lambda *args, **kwargs: upload)

    app = AppTest.from_file(APP).run()
    assert not app.exception
    assert any(item.value.startswith("Source:") for item in app.caption)
    by_label(app.button, "Prepare JPG photo").click()
    app.run()
    assert by_label(app.get("download_button"), "Download individual photo")

    by_label(app.selectbox, "Paper").select("Custom")
    app.run()
    by_label(app.number_input, "Paper width (mm)").set_value(1.0)
    by_label(app.number_input, "Paper height (mm)").set_value(1.0)
    app.run()
    assert app.error
    assert by_label(app.get("download_button"), "Download individual photo")
