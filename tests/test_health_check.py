"""
Pytest Tests for Health Check Button Interactions

Tests health check button interactions to ensure:
- Correct Coda entries are made
- Follow-up prompts are sent appropriately
- Both "Great" and "Not Great" paths work correctly
"""

import pytest
from unittest.mock import Mock, MagicMock
import time
import sys
import os
import importlib

# Add repo root and src to path for imports
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

src_path = os.path.join(repo_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)


class TestHealthCheckButtonInteractions:
    """Test class for health check button interactions."""
    
    @pytest.fixture
    def mock_bot(self, mock_slack_client, mock_coda_service):
        """Create a mock bot instance with mocked dependencies."""
        bot = Mock()
        bot.client = mock_slack_client
        bot.coda = mock_coda_service
        bot.health_responses = {}
        bot.get_user_name = Mock(return_value="Test User")
        bot.send_dm = Mock(return_value=True)
        bot.open_modal = Mock(return_value=True)
        
        return bot
    
    @pytest.fixture
    def great_button_payload(self):
        """Payload for clicking the 'Great' button."""
        return {
            'user': {'id': 'U123456'},
            'actions': [{'action_id': 'health_check_great', 'value': 'great'}],
            'channel': {'id': 'D123456'},
            'message': {'ts': '1234567890.123'},
            'response_url': ''
        }
    
    @pytest.fixture
    def not_great_button_payload(self):
        """Payload for clicking the 'Not Great' button."""
        return {
            'user': {'id': 'U123456'},
            'actions': [{'action_id': 'health_check_not_great', 'value': 'not_great'}],
            'channel': {'id': 'D123456'},
            'message': {'ts': '1234567890.123'},
            'response_url': ''
        }
    
    @pytest.fixture
    def public_share_payload(self):
        """Payload for clicking 'Public Share' button."""
        return {
            'user': {'id': 'U123456'},
            'actions': [{'action_id': 'health_share_public', 'value': 'public_health_check_not_great'}],
            'trigger_id': 'trigger123'
        }
    
    @pytest.fixture
    def private_share_payload(self):
        """Payload for clicking 'Private Share' button."""
        return {
            'user': {'id': 'U123456'},
            'actions': [{'action_id': 'health_share_private', 'value': 'private_health_check_not_great'}],
            'trigger_id': 'trigger123'
        }
    
    @pytest.fixture
    def public_share_modal_payload(self):
        """Payload for submitting public share modal."""
        return {
            'user': {'id': 'U123456'},
            'view': {
                'state': {
                    'values': {
                        'public_share': {
                            'public_share_input': {
                                'value': 'Feeling stressed about the deadline'
                            }
                        }
                    }
                }
            }
        }
    
    @pytest.fixture
    def private_share_modal_payload(self):
        """Payload for submitting private share modal."""
        return {
            'user': {'id': 'U123456'},
            'view': {
                'state': {
                    'values': {
                        'private_share': {
                            'private_share_input': {
                                'value': 'Need some support'
                            }
                        }
                    }
                }
            }
        }
    
    def _import_events_module(self):
        """Import events module with mocked dependencies."""
        # Remove cached modules to ensure clean import each time
        for module_name in ('events', 'src.events'):
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        events_module = importlib.import_module('src.events')
        # Make it available as `events` for convenience
        sys.modules['events'] = events_module
        
        # Mock external dependencies the module imports directly
        events_module.logger = MagicMock()
        events_module.error_handler = MagicMock()
        events_module.input_validator = MagicMock()
        events_module.input_validator.validate_user_id.return_value = True
        events_module.safe_executor = MagicMock()
        events_module.safe_executor.execute = lambda func, name, user_id, **kwargs: func(**kwargs)
        
        return events_module
    
    def test_great_button_saves_to_coda(self, mock_bot, great_button_payload, mock_coda_service):
        """Test that clicking 'Great' button saves to Coda Health_Check table."""
        events = self._import_events_module()
        
        # Mock users_info response
        mock_bot.client.users_info = Mock(return_value={
            'user': {'real_name': 'Test User', 'name': 'testuser'}
        })
        
        # Mock send_dm
        mock_bot.send_dm = Mock(return_value=True)
        
        # Call handler
        result = events.handle_health_response(mock_bot, great_button_payload)
        
        # Wait for background thread to complete
        time.sleep(0.5)
        
        # Verify Coda save_health_check was called
        mock_coda_service.save_health_check.assert_called_once()
        call_args = mock_coda_service.save_health_check.call_args
        
        # Verify correct arguments
        assert call_args[0][0] == 'U123456'  # user_id
        assert call_args[0][1] == 'Test User'  # username
        assert call_args[0][2] == '😊 Great'  # mood
        assert call_args[0][3] == ''  # share_text
        assert call_args[0][4] is False  # is_public
        
        # Verify response
        assert result == {"response_action": "clear"}
    
    def test_great_button_sends_followup_prompt(self, mock_bot, great_button_payload):
        """Test that clicking 'Great' button sends follow-up prompt."""
        events = self._import_events_module()
        
        # Mock users_info response
        mock_bot.client.users_info = Mock(return_value={
            'user': {'real_name': 'Test User', 'name': 'testuser'}
        })
        
        # Mock send_dm to capture calls
        mock_bot.send_dm = Mock(return_value=True)
        
        # Call handler
        events.handle_health_response(mock_bot, great_button_payload)
        
        # Wait for background thread
        time.sleep(0.5)
        
        # Verify send_dm was called with follow-up prompt
        assert mock_bot.send_dm.called
        call_args_list = mock_bot.send_dm.call_args_list
        
        # Find the follow-up call (should have blocks)
        followup_call = None
        for call_item in call_args_list:
            if len(call_item) >= 2 and call_item[1].get('blocks'):
                followup_call = call_item
                break
        
        assert followup_call is not None, "Follow-up prompt with blocks was not sent"
        
        # Verify blocks contain share buttons
        blocks = followup_call[1]['blocks']
        assert any(block.get('type') == 'actions' for block in blocks)
    
    def test_not_great_button_saves_to_coda(self, mock_bot, not_great_button_payload, mock_coda_service):
        """Test that clicking 'Not Great' button saves to Coda Health_Check table."""
        events = self._import_events_module()
        
        # Mock users_info response
        mock_bot.client.users_info = Mock(return_value={
            'user': {'real_name': 'Test User', 'name': 'testuser'}
        })
        
        # Mock send_dm
        mock_bot.send_dm = Mock(return_value=True)
        
        # Call handler
        result = events.handle_health_response(mock_bot, not_great_button_payload)
        
        # Wait for background thread
        time.sleep(0.5)
        
        # Verify Coda save_health_check was called
        mock_coda_service.save_health_check.assert_called_once()
        call_args = mock_coda_service.save_health_check.call_args
        
        # Verify correct arguments
        assert call_args[0][0] == 'U123456'  # user_id
        assert call_args[0][1] == 'Test User'  # username
        assert call_args[0][2] == '😕 Not great'  # mood
        assert call_args[0][3] == ''  # share_text
        assert call_args[0][4] is False  # is_public
        
        # Verify response
        assert result == {"response_action": "clear"}
    
    def test_not_great_button_sends_followup_prompt(self, mock_bot, not_great_button_payload):
        """Test that clicking 'Not Great' button sends follow-up prompt."""
        events = self._import_events_module()
        
        # Mock users_info response
        mock_bot.client.users_info = Mock(return_value={
            'user': {'real_name': 'Test User', 'name': 'testuser'}
        })
        
        # Mock send_dm
        mock_bot.send_dm = Mock(return_value=True)
        
        # Call handler
        events.handle_health_response(mock_bot, not_great_button_payload)
        
        # Wait for background thread
        time.sleep(0.5)
        
        # Verify send_dm was called with follow-up prompt
        assert mock_bot.send_dm.called
        call_args_list = mock_bot.send_dm.call_args_list
        
        # Find the follow-up call (should have blocks)
        followup_call = None
        for call_item in call_args_list:
            if len(call_item) >= 2 and call_item[1].get('blocks'):
                followup_call = call_item
                break
        
        assert followup_call is not None, "Follow-up prompt with blocks was not sent"
        
        # Verify blocks contain share buttons
        blocks = followup_call[1]['blocks']
        actions_block = next((b for b in blocks if b.get('type') == 'actions'), None)
        assert actions_block is not None
        
        # Verify share button action_ids
        button_action_ids = [elem.get('action_id') for elem in actions_block.get('elements', [])]
        assert 'health_share_public' in button_action_ids
        assert 'health_share_private' in button_action_ids
        assert 'health_no_share' in button_action_ids
    
    def test_public_share_opens_modal(self, mock_bot, public_share_payload):
        """Test that clicking 'Public Share' opens a modal."""
        events = self._import_events_module()
        
        # Set up stored mood
        mock_bot.health_responses['U123456'] = '😕 Not great'
        
        # Mock open_modal
        mock_bot.open_modal = Mock(return_value=True)
        
        # Call handler
        result = events.handle_health_share_response(mock_bot, public_share_payload)
        
        # Verify open_modal was called
        mock_bot.open_modal.assert_called_once()
        call_args = mock_bot.open_modal.call_args
        
        # Verify modal properties
        assert call_args[1]['title'] == 'Share Publicly'
        assert call_args[1]['callback_id'] == 'health_public_share_submit'
        assert call_args[1]['trigger_id'] == 'trigger123'
        
        # Verify response
        assert result == {"response_action": "clear"}
    
    def test_private_share_opens_modal(self, mock_bot, private_share_payload):
        """Test that clicking 'Private Share' opens a modal."""
        events = self._import_events_module()
        
        # Set up stored mood
        mock_bot.health_responses['U123456'] = '😕 Not great'
        
        # Mock open_modal
        mock_bot.open_modal = Mock(return_value=True)
        
        # Call handler
        result = events.handle_health_share_response(mock_bot, private_share_payload)
        
        # Verify open_modal was called
        mock_bot.open_modal.assert_called_once()
        call_args = mock_bot.open_modal.call_args
        
        # Verify modal properties
        assert call_args[1]['title'] == 'Share Privately'
        assert call_args[1]['callback_id'] == 'health_private_share_submit'
        assert call_args[1]['trigger_id'] == 'trigger123'
        
        # Verify response
        assert result == {"response_action": "clear"}
    
    def test_public_share_submission_saves_to_after_health_check(self, mock_bot, public_share_modal_payload, mock_coda_service):
        """Test that submitting public share saves to After_Health_Check table."""
        events = self._import_events_module()
        
        # Set up stored mood
        mock_bot.health_responses['U123456'] = '😕 Not great'
        
        # Mock send_dm
        mock_bot.send_dm = Mock(return_value=True)
        
        # Call handler
        result = events.handle_health_public_share_submission(mock_bot, public_share_modal_payload)
        
        # Wait for background thread
        time.sleep(0.5)
        
        # Verify Coda save_health_check_sharing was called
        mock_coda_service.save_health_check_sharing.assert_called_once()
        args, kwargs = mock_coda_service.save_health_check_sharing.call_args
        
        # Verify correct arguments
        assert args[0] == 'U123456'  # user_id
        assert args[1] == 'Test User'  # username
        assert args[2] == '😕 Not great'  # mood
        assert args[3] == 'Feeling stressed about the deadline'  # share_text
        assert kwargs.get('is_public') is True  # is_public flag
        
        # Verify response
        assert result == {"response_action": "clear"}
        
        # Verify confirmation message was sent
        assert mock_bot.send_dm.called
    
    def test_private_share_submission_saves_to_after_health_check(self, mock_bot, private_share_modal_payload, mock_coda_service):
        """Test that submitting private share saves to After_Health_Check table."""
        events = self._import_events_module()
        
        # Set up stored mood
        mock_bot.health_responses['U123456'] = '😕 Not great'
        
        # Mock send_dm
        mock_bot.send_dm = Mock(return_value=True)
        
        # Call handler
        result = events.handle_health_private_share_submission(mock_bot, private_share_modal_payload)
        
        # Wait for background thread
        time.sleep(0.5)
        
        # Verify Coda save_health_check_sharing was called
        mock_coda_service.save_health_check_sharing.assert_called_once()
        args, kwargs = mock_coda_service.save_health_check_sharing.call_args
        
        # Verify correct arguments
        assert args[0] == 'U123456'  # user_id
        assert args[1] == 'Test User'  # username
        assert args[2] == '😕 Not great'  # mood
        assert args[3] == 'Need some support'  # share_text
        assert kwargs.get('is_public') is False  # is_public flag
        
        # Verify response
        assert result == {"response_action": "clear"}
        
        # Verify confirmation message was sent
        assert mock_bot.send_dm.called
    
    def test_no_share_clears_mood(self, mock_bot):
        """Test that clicking 'No Thanks' clears stored mood."""
        events = self._import_events_module()
        
        # Set up stored mood
        mock_bot.health_responses['U123456'] = '😊 Great'
        
        # Mock send_dm
        mock_bot.send_dm = Mock(return_value=True)
        
        # Create payload for no share
        no_share_payload = {
            'user': {'id': 'U123456'},
            'actions': [{'action_id': 'health_no_share', 'value': 'no_share_health_check_great'}]
        }
        
        # Call handler
        result = events.handle_health_share_response(mock_bot, no_share_payload)
        
        # Wait for background thread
        time.sleep(0.5)
        
        # Verify mood was cleared
        assert 'U123456' not in mock_bot.health_responses
        
        # Verify response
        assert result == {"response_action": "clear"}
        
        # Verify thank you message was sent
        assert mock_bot.send_dm.called
    
    def test_complete_not_great_flow(self, mock_bot, not_great_button_payload, public_share_payload, 
                                      public_share_modal_payload, mock_coda_service):
        """Test complete 'Not Great' flow: button -> follow-up -> public share -> Coda save."""
        events = self._import_events_module()
        
        # Mock users_info response
        mock_bot.client.users_info = Mock(return_value={
            'user': {'real_name': 'Test User', 'name': 'testuser'}
        })
        
        # Mock send_dm and open_modal
        mock_bot.send_dm = Mock(return_value=True)
        mock_bot.open_modal = Mock(return_value=True)
        
        # Step 1: Click "Not Great" button
        events.handle_health_response(mock_bot, not_great_button_payload)
        time.sleep(0.5)
        
        # Verify initial Coda save
        assert mock_coda_service.save_health_check.called
        assert mock_bot.health_responses.get('U123456') == '😕 Not great'
        
        # Step 2: Click "Public Share"
        events.handle_health_share_response(mock_bot, public_share_payload)
        
        # Verify modal was opened
        assert mock_bot.open_modal.called
        
        # Step 3: Submit public share modal
        events.handle_health_public_share_submission(mock_bot, public_share_modal_payload)
        time.sleep(0.5)
        
        # Verify After_Health_Check save
        assert mock_coda_service.save_health_check_sharing.called
        _, kwargs = mock_coda_service.save_health_check_sharing.call_args
        assert kwargs.get('is_public') is True  # is_public flag
        
        # Verify mood was cleared
        assert 'U123456' not in mock_bot.health_responses
    
    def test_complete_great_flow(self, mock_bot, great_button_payload, mock_coda_service):
        """Test complete 'Great' flow: button -> Coda save -> follow-up prompt."""
        events = self._import_events_module()
        
        # Mock users_info response
        mock_bot.client.users_info = Mock(return_value={
            'user': {'real_name': 'Test User', 'name': 'testuser'}
        })
        
        # Mock send_dm
        mock_bot.send_dm = Mock(return_value=True)
        
        # Click "Great" button
        result = events.handle_health_response(mock_bot, great_button_payload)
        time.sleep(0.5)
        
        # Verify Coda save
        assert mock_coda_service.save_health_check.called
        call_args = mock_coda_service.save_health_check.call_args
        assert call_args[0][2] == '😊 Great'
        
        # Verify follow-up prompt was sent
        assert mock_bot.send_dm.called
        
        # Verify response
        assert result == {"response_action": "clear"}
