import pytest
from unittest.mock import patch, MagicMock

from news.renderers import render_body_from_json, render_block


@pytest.mark.django_db
class TestRender:
    def test_render_body_from_json(self):
        """Тест рендеринга JSON тела"""
        body_json = [
            {"type": "paragraph", "data": {"text": "Test paragraph"}},
            {"type": "heading", "data": {"text": "Test heading", "level": 2}}
        ]

        result = render_body_from_json(body_json)
        assert isinstance(result, str)
        assert "Test paragraph" in result
        assert "Test heading" in result

    def test_render_block_paragraph(self):
        """Тест рендеринга блока paragraph"""
        block = {"type": "paragraph", "data": {"text": "Test text"}}
        result = render_block(block)
        assert "Test text" in result

    @patch('news.renderers.MediaAsset.objects.get')
    def test_render_block_image_with_media_id(self, mock_get):
        """Тест рендеринга блока image с media_id"""
        mock_media = MagicMock()
        mock_media.file.url = '/media/test.jpg'
        mock_get.return_value = mock_media

        block = {
            "type": "image",
            "data": {
                "media_id": 1,
                "alt": "Test alt"
            }
        }

        result = render_block(block)
        assert '/media/test.jpg' in result
        assert "Test alt" in result

    def test_render_block_image_with_file_url(self):
        """Тест рендеринга блока image с file url"""
        block = {
            "type": "image",
            "data": {
                "file": {"url": "/media/test.jpg"},
                "alt": "Test alt"
            }
        }

        result = render_block(block)
        assert "/media/test.jpg" in result
        assert "Test alt" in result

    def test_render_unknown_block_type(self):
        """Тест рендеринга неизвестного типа блока"""
        block = {"type": "unknown", "data": {}}
        result = render_block(block)
        assert result == ""

    def test_render_empty_body_json(self):
        """Тест рендеринга пустого body_json"""
        result = render_body_from_json(None)
        assert result == ""

        result = render_body_from_json([])
        assert result == ""

    def test_render_block_invalid_image_data(self):
        """Тест неверного блока изображений"""
        block = {"type": "image", "data": {}}
        result = render_block(block)
        assert result == ""

    def test_render_body_malformed_json(self):
        """Тест неправильно сформированного JSON"""
        malformed = [{"type": "paragraph"}]
        result = render_body_from_json(malformed)
        assert isinstance(result, str)