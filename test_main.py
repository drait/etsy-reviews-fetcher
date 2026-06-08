import os
import pytest
from unittest.mock import patch, MagicMock, call

import main
from main import extract_listing_id, fetch_listing, fetch_all_reviews, analyze


# --- extract_listing_id ---

def test_extract_listing_id_full_url():
    assert extract_listing_id("https://www.etsy.com/listing/1315972330/some-title") == "1315972330"

def test_extract_listing_id_url_no_title():
    assert extract_listing_id("https://www.etsy.com/listing/1315972330") == "1315972330"

def test_extract_listing_id_bare_id():
    assert extract_listing_id("1315972330") == "1315972330"

def test_extract_listing_id_invalid(capsys):
    with pytest.raises(SystemExit):
        extract_listing_id("not-a-listing")


# --- fetch_listing ---

@patch("main.requests.get")
def test_fetch_listing(mock_get):
    mock_get.return_value.json.return_value = {"title": "Cool mug", "listing_id": 123}
    mock_get.return_value.raise_for_status = MagicMock()

    os.environ["ETSY_API_KEY"] = "test-key"
    result = fetch_listing("123")

    mock_get.assert_called_once_with(
        "https://openapi.etsy.com/v3/application/listings/123",
        headers={"x-api-key": "test-key"},
    )
    assert result["title"] == "Cool mug"

@patch("main.requests.get")
def test_fetch_listing_raises_on_http_error(mock_get):
    mock_get.return_value.raise_for_status.side_effect = Exception("403 Forbidden")

    with pytest.raises(Exception, match="403"):
        fetch_listing("123")


# --- fetch_all_reviews ---

@patch("main.requests.get")
def test_fetch_all_reviews_single_page(mock_get):
    mock_get.return_value.raise_for_status = MagicMock()
    mock_get.return_value.json.return_value = {
        "count": 2,
        "results": [{"rating": 5, "review": "Great!"}, {"rating": 4, "review": "Good"}],
    }

    os.environ["ETSY_API_KEY"] = "test-key"
    reviews = fetch_all_reviews("123")

    assert len(reviews) == 2
    assert mock_get.call_count == 1

@patch("main.requests.get")
def test_fetch_all_reviews_paginates(mock_get):
    page1 = {"count": 150, "results": [{"rating": 5, "review": f"r{i}"} for i in range(100)]}
    page2 = {"count": 150, "results": [{"rating": 4, "review": f"r{i}"} for i in range(50)]}
    mock_get.return_value.raise_for_status = MagicMock()
    mock_get.return_value.json.side_effect = [page1, page2]

    reviews = fetch_all_reviews("123")

    assert len(reviews) == 150
    assert mock_get.call_count == 2
    _, kwargs = mock_get.call_args_list[1]
    assert kwargs["params"]["offset"] == 100

@patch("main.requests.get")
def test_fetch_all_reviews_empty(mock_get):
    mock_get.return_value.raise_for_status = MagicMock()
    mock_get.return_value.json.return_value = {"count": 0, "results": []}

    reviews = fetch_all_reviews("123")
    assert reviews == []


# --- analyze ---

@patch("main.anthropic.Anthropic")
def test_analyze_streams_output(mock_anthropic, capsys):
    mock_stream = MagicMock()
    mock_stream.__enter__ = MagicMock(return_value=mock_stream)
    mock_stream.__exit__ = MagicMock(return_value=False)
    mock_stream.text_stream = iter(["Great ", "listing!"])
    mock_anthropic.return_value.messages.stream.return_value = mock_stream

    listing = {"title": "Cool mug", "description": "A nice mug", "tags": ["mug"], "materials": [], "price": None}
    reviews = [{"rating": 5, "review": "Loved it"}, {"rating": 4, "review": ""}]

    analyze(listing, reviews)

    captured = capsys.readouterr()
    assert "Great listing!" in captured.out

@patch("main.anthropic.Anthropic")
def test_analyze_formats_price(mock_anthropic, capsys):
    mock_stream = MagicMock()
    mock_stream.__enter__ = MagicMock(return_value=mock_stream)
    mock_stream.__exit__ = MagicMock(return_value=False)
    mock_stream.text_stream = iter(["ok"])
    mock_anthropic.return_value.messages.stream.return_value = mock_stream

    listing = {
        "title": "Mug",
        "description": "desc",
        "tags": [],
        "materials": [],
        "price": {"amount": 1500, "divisor": 100, "currency_code": "USD"},
    }

    analyze(listing, [])

    _, kwargs = mock_anthropic.return_value.messages.stream.call_args
    prompt = kwargs["messages"][0]["content"]
    assert "15.00 USD" in prompt
