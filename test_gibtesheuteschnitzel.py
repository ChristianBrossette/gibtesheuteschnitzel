import unittest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime, timezone
import requests

# Import functions from your main script (assuming it is saved as schnitzel.py)
from gibtesheuteschnitzel import (
    is_today, 
    find_schnitzel_items, 
    get_schnitzel, 
    calculate_p_schnitzel
)

class TestSchnitzelScript(unittest.TestCase):

    # -------------------------------------------------------------------------
    # 1. Testing Date Logic (is_today)
    # -------------------------------------------------------------------------
    @patch('gibtesheuteschnitzel.datetime')
    def test_is_today_true(self, mock_datetime):
        # Mock today's date to match the API input
        mock_datetime.now.return_value = datetime(2026, 5, 28, tzinfo=timezone.utc)
        mock_datetime.strptime = datetime.strptime  # Keep standard strptime behavior
        
        day_obj = {'date': '2026-05-28T10:00:00.000Z'}
        self.assertTrue(is_today(day_obj))

    @patch('gibtesheuteschnitzel.datetime')
    def test_is_today_false(self, mock_datetime):
        # Mock today's date to be DIFFERENT from the API input
        mock_datetime.now.return_value = datetime(2026, 5, 29, tzinfo=timezone.utc)
        mock_datetime.strptime = datetime.strptime
        
        day_obj = {'date': '2026-05-28T10:00:00.000Z'}
        self.assertFalse(is_today(day_obj))

    def test_is_today_invalid_format(self):
        # Should gracefully return False and log an error if date is missing/malformed
        self.assertFalse(is_today({'date': 'not-a-real-date'}))
        self.assertFalse(is_today({}))

    # -------------------------------------------------------------------------
    # 2. Testing Schnitzel Matching (find_schnitzel_items)
    # -------------------------------------------------------------------------
    def test_find_schnitzel_items_found(self):
        day_obj = {
            'counters': [
                {'name': 'Vegan Bowl', 'price': 4.00},
                {'name': 'Paniertes SchweineSchnitzel mit Pommes', 'price': 3.50}
            ]
        }
        result = find_schnitzel_items(day_obj)
        self.assertEqual(len(result), 1)
        self.assertIn('SchweineSchnitzel', result[0]['name'])

    def test_find_schnitzel_items_not_found(self):
        day_obj = {
            'counters': [
                {'name': 'Spaghetti Bolognese'},
                {'name': 'Salat'}
            ]
        }
        result = find_schnitzel_items(day_obj)
        self.assertEqual(len(result), 0)

    # -------------------------------------------------------------------------
    # 3. Testing API Fetching and Loop Logic (get_schnitzel)
    # -------------------------------------------------------------------------
    @patch('gibtesheuteschnitzel.requests.get')
    @patch('gibtesheuteschnitzel.is_today')
    def test_get_schnitzel_success_ja(self, mock_is_today, mock_requests_get):
        # Mock API Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'days': [
                {'date': 'yesterday', 'counters': [{'name': 'Nudeln'}]},
                {'date': 'today', 'counters': [{'name': 'Schnitzel'}]}
            ]
        }
        mock_requests_get.return_value = mock_response
        
        # Mock is_today so it returns False for the first day, True for the second day
        mock_is_today.side_effect = [False, True]

        answer, data, is_today_flag = get_schnitzel('http://fake-api', 'fake-key')
        
        self.assertEqual(answer, 'ja')
        self.assertTrue(is_today_flag)

    @patch('gibtesheuteschnitzel.requests.get')
    @patch('gibtesheuteschnitzel.time.sleep') # Prevent test from actually waiting during retries
    def test_get_schnitzel_api_failure(self, mock_sleep, mock_requests_get):
        # Simulate an API crash throwing the exact exception the code looks for
        mock_requests_get.side_effect = requests.RequestException("API is down")
        
        with self.assertRaises(requests.RequestException):
            get_schnitzel('http://fake-api', 'fake-key', max_retries=2)
            
        # Verify it retried the specified number of times
        self.assertEqual(mock_requests_get.call_count, 2)

    # -------------------------------------------------------------------------
    # 4. Testing Statistics Calculation (calculate_p_schnitzel)
    # -------------------------------------------------------------------------
    @patch('gibtesheuteschnitzel.time.strftime')
    def test_calculate_p_schnitzel(self, mock_strftime):
        # Fix "today" for the test
        mock_strftime.return_value = "05/28/26"
        
        # Mock the contents of stats.txt
        fake_stats_data = (
            "05/26/26_nein\n"
            "05/27/26_ja\n"
            "05/28/26_ja\n"
        )
        
        with patch('builtins.open', mock_open(read_data=fake_stats_data)):
            stats_string, today_answer = calculate_p_schnitzel()
            
            # 2 out of 3 days were 'ja' -> 66.67%
            self.assertEqual(today_answer, 'ja')
            self.assertIn("66.67%", stats_string)
            self.assertIn("26.05.26", stats_string) # Checking the date formatting logic

    def test_calculate_p_schnitzel_no_file(self):
        # Test behavior when stats.txt hasn't been created yet
        with patch('builtins.open', side_effect=FileNotFoundError):
            stats_string, today_answer = calculate_p_schnitzel()
            
            self.assertEqual(stats_string, "Keine Statistiken verfügbar")
            self.assertEqual(today_answer, "nein")

if __name__ == '__main__':
    unittest.main()