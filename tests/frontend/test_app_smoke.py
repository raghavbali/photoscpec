from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class EmptyService:
    config_errors = []

    def list_specs(self):
        return []

    def resolve_dimensions(self, request):
        from photoscpec.interfaces.models import DimensionsResult
        return DimensionsResult(35, 45, 413, 531, request.dpi)


@patch("photoscpec.services.photoscpec_service.PhotoScpecService", EmptyService)
def test_app_renders_without_upload():
    app = AppTest.from_file("frontend/app.py").run()
    assert not app.exception
    assert app.file_uploader
    assert any("Upload a photo" in item.value for item in app.info)
