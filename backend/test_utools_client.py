"""
Unit tests for Utools API client.
Tests all functionality with mock responses to avoid hitting real API.
"""

import json
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import requests

from backend.utools_client import (
    UtoolsClient, 
    UtoolsError, 
    RateLimitError, 
    AuthenticationError, 
    APIResponseError,
    SearchResult
)


class TestUtoolsClient:
    """Test suite for UtoolsClient"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key"
        self.client = UtoolsClient(self.api_key)
        
    @pytest.fixture
    def mock_search_response(self):
        """Mock successful search response"""
        return {
            "code": 1,
            "message": "success",
            "data": json.dumps({
                "data": {
                    "search_by_raw_query": {
                        "search_timeline": {
                            "timeline": {
                                "instructions": [
                                    {
                                        "type": "TimelineAddEntries",
                                        "entries": [
                                            {
                                                "entryId": "tweet-123456789",
                                                "content": {
                                                    "itemContent": {
                                                        "tweet_results": {
                                                            "result": {
                                                                "__typename": "Tweet",
                                                                "rest_id": "123456789",
                                                                "legacy": {
                                                                    "full_text": "Check out this comet invitation link: https://www.perplexity.ai/browser/claim/ABC123",
                                                                    "created_at": "Wed Oct 25 20:30:15 +0000 2023"
                                                                },
                                                                "core": {
                                                                    "user_results": {
                                                                        "result": {
                                                                            "rest_id": "987654321",
                                                                            "legacy": {
                                                                                "screen_name": "testuser"
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            })
        }
    
    @pytest.fixture
    def mock_user_response(self):
        """Mock successful user lookup response"""
        return {
            "code": 1,
            "message": "success",
            "data": json.dumps({
                "data": {
                    "user": {
                        "result": {
                            "rest_id": "987654321",
                            "legacy": {
                                "screen_name": "testuser",
                                "name": "Test User"
                            }
                        }
                    }
                }
            })
        }
    
    @pytest.fixture
    def mock_followers_response(self):
        """Mock successful followers response"""
        return {
            "code": 1,
            "message": "success", 
            "data": json.dumps({
                "ids": [987654321, 111111111, 222222222]
            })
        }

    def test_init(self):
        """Test client initialization"""
        client = UtoolsClient("test_key", "https://custom.api.url")
        assert client.api_key == "test_key"
        assert client.base_url == "https://custom.api.url"
        assert client._min_request_interval == 1.0
        
    @patch('requests.Session.get')
    def test_make_request_success(self, mock_get):
        """Test successful API request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 1, "data": "success"}
        mock_get.return_value = mock_response
        
        result = self.client._make_request("test", {"param": "value"})
        
        assert result == {"code": 1, "data": "success"}
        mock_get.assert_called_once()
        
        # Check that API key was added to params
        call_args = mock_get.call_args
        assert call_args[1]['params']['apiKey'] == self.api_key
        assert call_args[1]['params']['param'] == "value"
    
    @patch('requests.Session.get')
    def test_make_request_rate_limit_http(self, mock_get):
        """Test rate limit handling via HTTP status code"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_get.return_value = mock_response
        
        with pytest.raises(RateLimitError):
            self.client._make_request("test", {})
    
    @patch('requests.Session.get')
    def test_make_request_rate_limit_api_response(self, mock_get):
        """Test rate limit handling via API response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0, 
            "message": "Rate limit exceeded"
        }
        mock_get.return_value = mock_response
        
        with pytest.raises(RateLimitError):
            self.client._make_request("test", {})
    
    @patch('requests.Session.get')
    def test_make_request_auth_error(self, mock_get):
        """Test authentication error handling"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response
        
        with pytest.raises(AuthenticationError):
            self.client._make_request("test", {})
    
    @patch('requests.Session.get')
    def test_make_request_api_error(self, mock_get):
        """Test API error response handling"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "message": "Invalid request"
        }
        mock_get.return_value = mock_response
        
        with pytest.raises(APIResponseError, match="API error: Invalid request"):
            self.client._make_request("test", {})
    
    @patch('requests.Session.get')
    def test_make_request_invalid_json(self, mock_get):
        """Test invalid JSON response handling"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response
        
        with pytest.raises(APIResponseError, match="Invalid JSON response"):
            self.client._make_request("test", {})
    
    @patch('requests.Session.get')
    def test_make_request_retry_logic(self, mock_get):
        """Test retry logic with exponential backoff"""
        # First two calls fail with network error, third succeeds
        def side_effect(*args, **kwargs):
            if mock_get.call_count <= 2:
                raise requests.RequestException("Network error")
            else:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"code": 1, "data": "success"}
                return mock_response
        
        mock_get.side_effect = side_effect
        
        with patch('time.sleep') as mock_sleep:
            result = self.client._make_request("test", {}, retries=2)
            
        assert result == {"code": 1, "data": "success"}
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2
        
        # Check exponential backoff timing
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [1.0, 2.0]  # 2^0 * 1.0, 2^1 * 1.0
    
    @patch('time.time')
    @patch('time.sleep')
    @patch('requests.Session.get')
    def test_rate_limiting_between_requests(self, mock_get, mock_sleep, mock_time):
        """Test rate limiting between consecutive requests"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 1, "data": "success"}
        mock_get.return_value = mock_response
        
        # Simulate time progression - need more time values for all the time.time() calls
        mock_time.side_effect = [0, 0, 0.5, 0.5, 1.0, 1.5]  # Two requests 0.5 seconds apart
        
        # Make two requests
        self.client._make_request("test1", {})
        self.client._make_request("test2", {})
        
        # Should sleep for 0.5 seconds on second request (1.0 - 0.5)
        # The first call might also sleep due to initial rate limiting
        assert mock_sleep.call_count >= 1
        # Check that the last sleep call was for 0.5 seconds
        last_sleep_call = mock_sleep.call_args_list[-1]
        assert last_sleep_call[0][0] == 0.5
    
    @patch.object(UtoolsClient, '_make_request')
    def test_search_tweets_success(self, mock_make_request, mock_search_response):
        """Test successful tweet search"""
        mock_make_request.return_value = mock_search_response
        
        results = self.client.search_tweets("comet invitation", count=10)
        
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SearchResult)
        assert result.tweet_id == "123456789"
        assert "comet invitation link" in result.content
        assert result.author_username == "testuser"
        assert result.author_id == "987654321"
        assert result.tweet_url == "https://x.com/testuser/status/123456789"
        
        mock_make_request.assert_called_once_with("search", {
            "words": "comet invitation",
            "product": "Latest", 
            "count": 10
        })
    
    @patch.object(UtoolsClient, '_make_request')
    def test_search_tweets_empty_results(self, mock_make_request):
        """Test search with no results"""
        empty_response = {
            "code": 1,
            "data": json.dumps({
                "data": {
                    "search_by_raw_query": {
                        "search_timeline": {
                            "timeline": {
                                "instructions": []
                            }
                        }
                    }
                }
            })
        }
        mock_make_request.return_value = empty_response
        
        results = self.client.search_tweets("nonexistent")
        assert results == []
    
    @patch.object(UtoolsClient, '_make_request')
    def test_search_tweets_malformed_response(self, mock_make_request):
        """Test search with malformed response data"""
        malformed_response = {
            "code": 1,
            "data": "invalid json"
        }
        mock_make_request.return_value = malformed_response
        
        with pytest.raises(APIResponseError, match="Failed to parse search response data"):
            self.client.search_tweets("test")
    
    @patch.object(UtoolsClient, '_make_request')
    def test_get_user_by_screen_name_success(self, mock_make_request, mock_user_response):
        """Test successful user lookup"""
        mock_make_request.return_value = mock_user_response
        
        user = self.client.get_user_by_screen_name("testuser")
        
        assert user is not None
        assert user["rest_id"] == "987654321"
        assert user["legacy"]["screen_name"] == "testuser"
        
        mock_make_request.assert_called_once_with("userByScreenNameV2", {
            "screen_name": "testuser"
        })
    
    @patch.object(UtoolsClient, '_make_request')
    def test_get_user_by_screen_name_not_found(self, mock_make_request):
        """Test user lookup when user doesn't exist"""
        not_found_response = {
            "code": 1,
            "data": json.dumps({"data": {}})
        }
        mock_make_request.return_value = not_found_response
        
        user = self.client.get_user_by_screen_name("nonexistent")
        assert user is None
    
    @patch.object(UtoolsClient, '_make_request')
    def test_get_followers_success(self, mock_make_request, mock_followers_response):
        """Test successful followers retrieval"""
        mock_make_request.return_value = mock_followers_response
        
        followers = self.client.get_followers("123456789")
        
        assert followers == ["987654321", "111111111", "222222222"]
        
        mock_make_request.assert_called_once_with("followersids", {
            "user_id": "123456789",
            "count": 200
        })
    
    @patch.object(UtoolsClient, '_make_request')
    def test_get_followers_empty(self, mock_make_request):
        """Test followers retrieval with no followers"""
        empty_response = {
            "code": 1,
            "data": json.dumps({"ids": []})
        }
        mock_make_request.return_value = empty_response
        
        followers = self.client.get_followers("123456789")
        assert followers == []
    
    @patch.object(UtoolsClient, 'get_user_by_screen_name')
    @patch.object(UtoolsClient, 'get_followers')
    def test_verify_user_follows_success(self, mock_get_followers, mock_get_user):
        """Test successful follower verification"""
        mock_get_user.return_value = {"rest_id": "987654321"}
        mock_get_followers.return_value = ["987654321", "111111111", "222222222"]
        
        result = self.client.verify_user_follows("testuser", "123456789")
        
        assert result is True
        mock_get_user.assert_called_once_with("testuser")
        mock_get_followers.assert_called_once_with("123456789")
    
    @patch.object(UtoolsClient, 'get_user_by_screen_name')
    @patch.object(UtoolsClient, 'get_followers')
    def test_verify_user_follows_not_following(self, mock_get_followers, mock_get_user):
        """Test follower verification when user is not following"""
        mock_get_user.return_value = {"rest_id": "999999999"}
        mock_get_followers.return_value = ["987654321", "111111111", "222222222"]
        
        result = self.client.verify_user_follows("testuser", "123456789")
        
        assert result is False
    
    @patch.object(UtoolsClient, 'get_user_by_screen_name')
    def test_verify_user_follows_user_not_found(self, mock_get_user):
        """Test follower verification when user doesn't exist"""
        mock_get_user.return_value = None
        
        result = self.client.verify_user_follows("nonexistent", "123456789")
        
        assert result is False
    
    @patch.object(UtoolsClient, 'get_user_by_screen_name')
    def test_verify_user_follows_api_error(self, mock_get_user):
        """Test follower verification with API error"""
        mock_get_user.side_effect = UtoolsError("API error")
        
        with pytest.raises(UtoolsError, match="Follower verification failed"):
            self.client.verify_user_follows("testuser", "123456789")
    
    def test_parse_search_results_complex_structure(self):
        """Test parsing of complex search results with multiple tweets"""
        search_data = {
            "data": {
                "search_by_raw_query": {
                    "search_timeline": {
                        "timeline": {
                            "instructions": [
                                {
                                    "type": "TimelineAddEntries",
                                    "entries": [
                                        {
                                            "entryId": "tweet-123",
                                            "content": {
                                                "itemContent": {
                                                    "tweet_results": {
                                                        "result": {
                                                            "__typename": "Tweet",
                                                            "rest_id": "123",
                                                            "legacy": {
                                                                "full_text": "First tweet",
                                                                "created_at": "Wed Oct 25 20:30:15 +0000 2023"
                                                            },
                                                            "core": {
                                                                "user_results": {
                                                                    "result": {
                                                                        "rest_id": "user1",
                                                                        "legacy": {"screen_name": "user1"}
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                        {
                                            "entryId": "tweet-456", 
                                            "content": {
                                                "itemContent": {
                                                    "tweet_results": {
                                                        "result": {
                                                            "__typename": "Tweet",
                                                            "rest_id": "456",
                                                            "legacy": {
                                                                "full_text": "Second tweet",
                                                                "created_at": "Wed Oct 25 21:30:15 +0000 2023"
                                                            },
                                                            "core": {
                                                                "user_results": {
                                                                    "result": {
                                                                        "rest_id": "user2",
                                                                        "legacy": {"screen_name": "user2"}
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    ]
                                },
                                {
                                    "type": "OtherInstruction",
                                    "entries": []
                                }
                            ]
                        }
                    }
                }
            }
        }
        
        results = self.client._parse_search_results(search_data)
        
        assert len(results) == 2
        assert results[0].tweet_id == "123"
        assert results[0].content == "First tweet"
        assert results[0].author_username == "user1"
        assert results[1].tweet_id == "456"
        assert results[1].content == "Second tweet"
        assert results[1].author_username == "user2"
    
    def test_parse_search_results_malformed_entry(self):
        """Test parsing with malformed entries (should skip them)"""
        search_data = {
            "data": {
                "search_by_raw_query": {
                    "search_timeline": {
                        "timeline": {
                            "instructions": [
                                {
                                    "type": "TimelineAddEntries",
                                    "entries": [
                                        {
                                            "entryId": "tweet-123",
                                            "content": {
                                                "itemContent": {
                                                    "tweet_results": {
                                                        "result": {
                                                            "__typename": "Tweet",
                                                            # Missing required fields
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            }
        }
        
        results = self.client._parse_search_results(search_data)
        assert results == []  # Should skip malformed entry


if __name__ == "__main__":
    pytest.main([__file__, "-v"])