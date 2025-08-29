import json
import time
import threading
from datetime import datetime
# Flask imports removed for Socket Mode compatibility
from .utils import logger, error_handler, input_validator, safe_executor
from .handlers import (
    handle_health_response,
    handle_health_share_response,
    handle_health_public_share_submission,
    handle_health_private_share_submission,
    handle_health_no_share,
    # Blocker handlers
    handle_blocker_note_edit,
    handle_complete_blocker_with_form,
    handle_blocker_followup_response as blocker_handle_followup_response,
    handle_claim_blocker,
    handle_update_progress,
    handle_mark_resolved,
    handle_view_blocker_details,
    handle_submit_blocker_details,
    handle_followup_response,
    # KR handlers
    handle_open_kr_continue_modal,
    handle_kr_continue_submit,
    # Modal handlers
    handle_open_blocker_report_modal,
    handle_open_checkin_modal,
    # Submission handlers
    handle_blocker_details_submission,
    handle_blocker_note_submission,
    handle_progress_update_submission,
    handle_checkin_submission,
    handle_daily_checkin_submission,
    # Blocker resolution handlers
    handle_blocker_completion_submission,
    handle_blocker_resolution_submission,
    handle_blocker_direct_resolution_submission,
    handle_blocker_channel_resolution_submission,
    handle_24hr_resolution_submission,
    # View handlers
    handle_view_details,
    handle_view_all_blockers,
    handle_view_blockers_with_sprint,
    handle_view_blockers_modal,
    # Modal opening handlers
    handle_open_blocker_modal_channel,
    handle_open_blocker_sprint_modal,
    handle_open_blocker_continue_modal,
    handle_open_view_blockers_modal,
)

# ============================================================================
# EVENTS MODULE: TABLE OF CONTENTS
# ----------------------------------------------------------------------------
# 1) Utilities
#    - track_submission
#    - log_payload_for_debugging
#    - generate_kr_explanation
#
# 2) Blockers: Note Editing & Completion
#    - handle_blocker_note_edit
#    - handle_complete_blocker_with_form
#
# 3) Mentor Responses
#    - handle_mentor_response
#
# 4) Modal Submissions Router
#    - handle_view_submission (routes: checkin, blocker, progress, health, etc.)
#
# 5) Events API Routing
#    - handle_events
#
# 6) Message & Reaction Events
#    - _handle_message_event
#    - _handle_reaction_event
#    - _handle_bot_mention
#    - _handle_blocker_keyword
#    - _handle_completion_reaction
#
# 7) Interactive Components Router
#    - handle_interactive_components
#
# 8) Health Check Handlers
#    - handle_health_response
#    - handle_health_public_share_submission
#    - handle_health_no_share
#    - handle_health_private_share_submission
#
# 9) Blockers: Progress & Resolution
#    - handle_update_progress
#    - handle_mark_resolved
#    - handle_blocker_completion_submission
#    - handle_blocker_resolution_submission
#    - handle_blocker_direct_resolution_submission
#    - handle_blocker_channel_resolution_submission
#
# 10) Blockers: Forms & Modals
#    - handle_open_blocker_report_modal
#    - handle_submit_blocker_form
#    - handle_open_blocker_modal_channel
#    - handle_blocker_sprint_modal_submission
#
# 11) Check-ins
#    - handle_open_checkin_modal
#    - handle_checkin_submission
#    - handle_daily_checkin_submission
#    - handle_checkin_no_blocker
#
# 12) Viewing Blockers
#    - handle_view_all_blockers
#    - handle_open_blocker_sprint_modal
#    - handle_view_blockers_with_sprint
#    - handle_open_view_blockers_modal
#    - handle_view_blockers_modal
#
# 13) KR (Key Results) Handlers
#    - handle_open_kr_continue_modal
#    - handle_kr_continue_submit
#    - generate_kr_explanation
#
# 14) 24-hour Resolution
#    - handle_24hr_resolution_submission
# ============================================================================

# Global submission tracking to prevent duplicates
_submission_tracker = {}

def track_submission(user_id, submission_type, data_hash=None):
    """Track a submission to prevent duplicates."""
    global _submission_tracker
    current_time = time.time()
    
    # Create a unique key for this submission
    if data_hash:
        submission_key = f"{user_id}_{submission_type}_{data_hash}"
    else:
        submission_key = f"{user_id}_{submission_type}_{int(current_time)}"
    
    # Clean up old submissions (older than 30 seconds)
    _submission_tracker = {k: v for k, v in _submission_tracker.items() if current_time - v < 30}
    
    # Check if this is a recent duplicate
    if submission_key in _submission_tracker:
        print(f"🔍 DEBUG: Duplicate submission detected: {submission_key}")
        return False
    
    # Track this submission
    _submission_tracker[submission_key] = current_time
    print(f"🔍 DEBUG: Tracking submission: {submission_key}")
    return True

# ============================================================================
# 1) Utilities
# ----------------------------------------------------------------------------
# Helper utilities used across handlers
# ============================================================================
def log_payload_for_debugging(payload):
    """Log payload structure for debugging."""
    try:
        print("🔍 DEBUG: Received payload:")
        print(f"   Type: {payload.get('type', 'N/A')}")
        print(f"   Keys: {list(payload.keys())}")
        
        if 'user' in payload:
            print(f"   User: {payload['user']}")
        
        if 'actions' in payload:
            print(f"   Actions: {payload['actions']}")
        
        if 'channel' in payload:
            print(f"   Channel: {payload['channel']}")
        
        if 'message' in payload:
            print(f"   Message keys: {list(payload['message'].keys())}")
            
    except Exception as e:
        print(f"❌ Error logging payload: {e}")

# ============================================================================
# 13) KR (Key Results) Handlers
# ----------------------------------------------------------------------------
# KR-related helper used by mentor response and KR flows
# ============================================================================
def generate_kr_explanation(kr_name, owner, status, definition_of_done=None):
    """Generate a contextual explanation for a KR based on its details."""
    try:
        explanation = f"This KR is currently {status.lower()}"
        
        if owner and owner != 'N/A':
            explanation += f" and is owned by {owner}"
        
        if definition_of_done and definition_of_done.strip():
            explanation += f". The definition of done includes: {definition_of_done}"
        
        explanation += "."
        
        return explanation
    except Exception as e:
        print(f"Error generating KR explanation: {e}")
        return "Unable to generate explanation at this time."

# ============================================================================
# 2) Blockers: Note Editing & Completion
# ----------------------------------------------------------------------------
# Moved to handlers.blocker_handlers

# ============================================================================
# 3) Mentor Responses
# ----------------------------------------------------------------------------
def handle_mentor_response(bot, payload):
    """Handle mentor check responses."""
    try:
        print(f"🔍 DEBUG: handle_mentor_response called with payload: {payload}")
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        action_id = payload['actions'][0]['action_id']
        value = payload['actions'][0]['value']
        channel_id = payload['channel']['id']
        message_ts = payload['message']['ts']
        
        print(f"🔍 DEBUG: handle_mentor_response called - Action: {action_id}, Value: {value}")
        print(f"🔍 DEBUG: User: {user_name} ({user_id})")
        print(f"🔍 DEBUG: Channel: {channel_id}, Message TS: {message_ts}")
        
        # Parse value: mentor_yes/request_type/user_id or mentor_no/request_type/user_id
        parts = value.split('_')
        print(f"🔍 DEBUG: Parsed value parts: {parts}")
        
        if len(parts) >= 3:
            mentor_response = parts[1]  # yes or no
            request_type = parts[2]     # kr or blocker
            target_user_id = parts[3]   # user_id
            
            print(f"🔍 DEBUG: Mentor response: {mentor_response}, Request type: {request_type}, Target user: {target_user_id}")
            
            # Note: Mentor table has been removed as per user request
            
            if mentor_response == 'yes':
                if request_type == 'kr':
                    # User has reached out to mentor, proceed with KR request
                    search_term = bot.pending_kr_search.get(target_user_id)
                    sprint_number = bot.pending_kr_sprint.get(target_user_id)
                    
                    print(f"🔍 DEBUG: Found sprint number: {sprint_number}")
                    print(f"🔍 DEBUG: KR search term: '{search_term}', Sprint: {sprint_number}")
                    print(f"🔍 DEBUG: All pending data for user {target_user_id}:")
                    print(f"🔍 DEBUG: - pending_kr_search: {bot.pending_kr_search.get(target_user_id)}")
                    print(f"🔍 DEBUG: - pending_kr_sprint: {bot.pending_kr_sprint.get(target_user_id)}")
                    
                    # Send "give me one moment" message first
                    bot.send_dm(target_user_id, "🔍 Give me one moment as it searches...")
                    
                    if search_term and sprint_number:
                        # Show KR search results with sprint filter
                        if bot.coda:
                            # Search for KRs by name first, then filter by sprint if needed
                            matches = bot.coda.search_kr_table(search_term)
                            if matches:
                                # Deduplicate KRs by name to avoid showing the same KR multiple times
                                unique_krs = {}
                                for m in matches:
                                    kr_name = m.get('c-yQ1M6UqTSj', 'N/A')
                                    if kr_name not in unique_krs:
                                        unique_krs[kr_name] = m
                                
                                # Use deduplicated results
                                unique_matches = list(unique_krs.values())
                                print(f"🔍 DEBUG: Found {len(matches)} total matches, {len(unique_matches)} unique KRs for sprint {sprint_number}")
                                
                                # Delete the original mentor check message first
                                print(f"🔍 DEBUG: Deleting mentor check message")
                                try:
                                    bot.update_message(
                                        channel_id=channel_id,
                                        ts=message_ts,
                                        text=f"✅ Found {len(unique_matches)} unique KRs for '{search_term}' in Sprint {sprint_number}:"
                                    )
                                except Exception as e:
                                    print(f"❌ Error updating mentor check message: {e}")
                                
                                # Send each unique KR as a separate message
                                print(f"🔍 DEBUG: Sending {len(unique_matches)} unique KR results as separate messages")
                                for i, m in enumerate(unique_matches, 1):
                                    kr_name = m.get('c-yQ1M6UqTSj', 'N/A')
                                    owner = m.get('c-efR-vVo_3w', 'N/A')
                                    status = m.get('c-cC29Yow8Gr', 'N/A')
                                    definition_of_done = m.get('c-P_mQJLObL0', '')
                                    link = m.get('link', None)
                                    explanation = generate_kr_explanation(kr_name, owner, status, definition_of_done)
                                    
                                    # Create individual KR message
                                    kr_message = f"*KR {i}*: {kr_name}\n*Owner*: {owner}\n*Status*: {status}\n*Definition of Done*: {definition_of_done}\n*AI Explanation*: {explanation}"
                                    if link:
                                        kr_message += f"\n<Link|{link}>"
                                    
                                    # Send as separate message
                                    try:
                                        bot.send_dm(target_user_id, kr_message)
                                        print(f"🔍 DEBUG: Sent KR {i} message")
                                    except Exception as e:
                                        print(f"❌ Error sending KR {i} message: {e}")
                            else:
                                # No matches found
                                result_text = f'No matching KRs found for "{search_term}" in Sprint {sprint_number}.'
                                print(f"🔍 DEBUG: No matches found, updating mentor check message")
                                bot.update_message(
                                    channel_id=channel_id,
                                    ts=message_ts,
                                    text=result_text
                                )
                        else:
                            # Delete the original mentor check message and replace with error
                            bot.update_message(
                                channel_id=channel_id,
                                ts=message_ts,
                                text=f"Great! Let me help you with your KR request: {search_term} in Sprint {sprint_number}"
                            )
                        
                        # Clear the pending search and sprint
                        bot.pending_kr_search.pop(target_user_id, None)
                        bot.pending_kr_sprint.pop(target_user_id, None)
                    else:
                        # No search term or sprint number, show KR form
                        bot.send_dm(target_user_id, "Great! Let me help you with your KR request. Please use `/kr (sprint_number) (kr_name)` to specify a sprint number and KR name.")
                        
                        # Clear any pending data
                        bot.pending_kr_search.pop(target_user_id, None)
                        bot.pending_kr_sprint.pop(target_user_id, None)
                elif request_type == 'blocker':
                    # User has reached out to mentor, proceed with blocker form
                    # Send a new message with the blocker button instead of updating
                    print(f"🔍 DEBUG: Sending new message with blocker button for blocker request")
                    
                    help_text = "🚨 *Great! Let me help you submit your blocker details.*\n\nI can help you submit a blocker report that will be escalated to the team so anyone can help resolve it.\n\nClick the button below to open the blocker report form."
                    
                    blocks = [
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": help_text}
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Report Blocker"},
                                    "action_id": "open_blocker_report_modal",
                                    "value": f"blocker_report_{target_user_id}",
                                    "style": "primary"
                                }
                            ]
                        }
                    ]
                    
                    # Send a new message instead of updating
                    print(f"🔍 DEBUG: Sending DM with blocker button to user: {target_user_id}")
                    result = bot.send_dm(target_user_id, help_text, blocks=blocks)
                    print(f"🔍 DEBUG: send_dm result: {result}")
                    
                    # Also delete the original mentor check message
                    try:
                        print(f"🔍 DEBUG: Updating original mentor check message")
                        bot.update_message(
                            channel_id=channel_id,
                            ts=message_ts,
                            text="✅ Mentor check completed - see message above for blocker form."
                        )
                    except Exception as e:
                        print(f"❌ Error updating mentor check message: {e}")
                else:
                    print(f"❌ DEBUG: Unknown request type: {request_type}")
            elif mentor_response == 'no':
                # Handle "No" response
                print(f"🔍 DEBUG: Handling mentor 'no' response for {request_type}")
                if request_type == 'kr':
                    bot.update_message(
                        channel_id=channel_id,
                        ts=message_ts,
                        text="I understand! Please reach out to your mentor first, then try the `/kr` command again."
                    )
                elif request_type == 'blocker':
                    # For blockers, still send the blocker form even if they haven't talked to mentor
                    # This allows them to submit the blocker anyway
                    print(f"🔍 DEBUG: Sending blocker form despite mentor 'no' response")
                    
                    help_text = "🚨 *Let me help you submit your blocker details.*\n\nI can help you submit a blocker report that will be escalated to the team so anyone can help resolve it.\n\nClick the button below to open the blocker report form."
                    
                    blocks = [
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": help_text}
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Report Blocker"},
                                    "action_id": "open_blocker_report_modal",
                                    "value": f"blocker_report_{target_user_id}",
                                    "style": "primary"
                                }
                            ]
                        }
                    ]
                    
                    # Send a new message with the blocker button
                    print(f"🔍 DEBUG: Sending DM with blocker button to user: {target_user_id}")
                    result = bot.send_dm(target_user_id, help_text, blocks=blocks)
                    print(f"🔍 DEBUG: send_dm result: {result}")
                    
                    # Update the original mentor check message
                    try:
                        print(f"🔍 DEBUG: Updating original mentor check message")
                        bot.update_message(
                            channel_id=channel_id,
                            ts=message_ts,
                            text="✅ Mentor check completed - see message above for blocker form."
                        )
                    except Exception as e:
                        print(f"❌ Error updating mentor check message: {e}")
            else:
                print(f"❌ DEBUG: Unknown mentor response: {mentor_response}")
        else:
            print(f"❌ DEBUG: Could not parse mentor response value: {value}")
        
        return {"response_action": "clear"}
    except Exception as e:
        print(f"❌ Error in handle_mentor_response: {e}")
        import traceback
        traceback.print_exc()
        return {"response_action": "clear"}

# Moved to handlers.blocker_handlers

# Moved to handlers.blocker_handlers

def handle_view_submission(bot, payload):
    """Handle modal submissions."""
    try:
        callback_id = payload.get('view', {}).get('callback_id', '')
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        
        print(f"🔍 DEBUG: handle_view_submission called with callback_id: '{callback_id}' for user: {user_name}")
        
        # Enhanced submission tracking to prevent duplicates
        submission_key = f"{user_id}_{callback_id}_{int(time.time())}"
        if not hasattr(bot, 'recent_submissions'):
            bot.recent_submissions = {}
        
        # Check if this is a recent duplicate submission (within 10 seconds)
        current_time = time.time()
        recent_submissions = bot.recent_submissions.get(user_id, {})
        
        # Clean up old submissions (older than 15 seconds)
        recent_submissions = {k: v for k, v in recent_submissions.items() if current_time - v < 15}
        bot.recent_submissions[user_id] = recent_submissions
        
        # Check if this callback_id was recently submitted
        if callback_id in recent_submissions:
            print(f"🔍 DEBUG: Duplicate submission detected for {user_name} with callback_id: {callback_id}")
            return {"response_action": "clear"}
        
        # Track this submission
        recent_submissions[callback_id] = current_time
        bot.recent_submissions[user_id] = recent_submissions
        
        # Route to appropriate handler
        if callback_id == 'checkin_submit':
            return handle_checkin_submission(bot, payload)
        elif callback_id == 'daily_checkin_submit':
            return handle_daily_checkin_submission(bot, payload)
        elif callback_id == 'blocker_submit':
            # Use the blocker_details_submission handler for all blocker submissions
            return handle_blocker_details_submission(bot, payload)
        elif callback_id == 'blocker_details_submit':
            return handle_blocker_details_submission(bot, payload)
        elif callback_id == 'blocker_note_submit':
            return handle_blocker_note_submission(bot, payload)
        elif callback_id == 'progress_update_submit':
            return handle_progress_update_submission(bot, payload)
        # Removed blocker_report_submit to prevent duplicate saves
        elif callback_id == 'health_public_share_submit':
            return handle_health_public_share_submission(bot, payload)
        elif callback_id == 'health_private_share_submission':
            return handle_health_private_share_submission(bot, payload)
        elif callback_id == 'blocker_completion_submit':
            return handle_blocker_completion_submission(bot, payload)
        elif callback_id == 'blocker_resolution_submit':
            return handle_blocker_resolution_submission(bot, payload)
        elif callback_id == 'blocker_direct_resolution_submit':
            return handle_blocker_direct_resolution_submission(bot, payload)
        elif callback_id == 'blocker_channel_resolution_submit':
            return handle_blocker_channel_resolution_submission(bot, payload)
        elif callback_id == 'blocker_sprint_modal':
            return handle_blocker_sprint_modal_submission(bot, payload)
        elif callback_id == 'submit_24hr_resolution':
            return handle_24hr_resolution_submission(bot, payload)
        else:
            print(f"Unknown modal callback_id: {callback_id}")
            return {"response_action": "clear"}
    except Exception as e:
        print(f"Error handling view submission: {e}")
        return {"response_action": "clear"}

# Moved to handlers.submission_handlers

# Removed duplicate handle_blocker_submission function - using handle_blocker_details_submission instead

# Moved to handlers.submission_handlers

# Moved to handlers.submission_handlers

# Moved to handlers.submission_handlers

def handle_events(bot, payload):
    """Handle Slack events."""
    try:
        event_type = payload.get('type')
        
        if event_type == 'url_verification':
            return payload.get('challenge')
        
        if event_type == 'event_callback':
            event = payload.get('event', {})
            event_subtype = event.get('subtype')
            
            # Skip bot messages and message edits
            if event_subtype in ['bot_message', 'message_changed']:
                return "OK"
            
            # Handle different event types
            if event.get('type') == 'message':
                return _handle_message_event(bot, event)
            elif event.get('type') == 'reaction_added':
                return _handle_reaction_event(bot, event)
        
        return "OK"
    except Exception as e:
        print(f"Error handling events: {e}")
        return "Error"

# ============================================================================
# 6) Message & Reaction Events
# ----------------------------------------------------------------------------
def _handle_message_event(bot, event):
    """Handle message events."""
    try:
        user_id = event.get('user')
        text = event.get('text', '')
        channel_id = event.get('channel')
        thread_ts = event.get('thread_ts')
        message_ts = event.get('ts')
        
        if not user_id or not text:
            return "OK"
        
        # Skip bot messages to prevent processing our own messages
        if 'bot_id' in event or user_id == bot.config.SLACK_BOT_USER_ID:
            return "OK"
        
        # Check if this is a DM (channel starts with 'D')
        is_dm = channel_id.startswith('D')
        
        if is_dm:
            # Check if this is a reply to a standup prompt (has thread_ts)
            if thread_ts:
                print(f"🔍 DEBUG: Processing as standup response (in thread)")
                # This is a reply in a DM (standup response)
                bot.handle_standup_response(
                    user_id=user_id,
                    message_ts=message_ts,
                    thread_ts=thread_ts,
                    text=text,
                    channel_id=channel_id
                )
                return "standup_response_processed"
            
            # Handle commands in DM
            if bot.handle_commands(user_id, text, channel_id):
                return "command_processed"
        
        # Check for bot mentions
        if f'<@{bot.config.SLACK_BOT_USER_ID}>' in text:
            return _handle_bot_mention(bot, user_id, text, channel_id)
        
        # Check for specific keywords
        if any(keyword in text.lower() for keyword in ['blocker', 'blocked', 'stuck']):
            return _handle_blocker_keyword(bot, user_id, text, channel_id)
        
        return "OK"
    except Exception as e:
        print(f"Error handling message event: {e}")
        return "Error"

def _handle_reaction_event(bot, event):
    """Handle reaction events."""
    try:
        user_id = event.get('user')
        reaction = event.get('reaction')
        item = event.get('item', {})
        
        # Handle daily standup reactions
        if reaction in ['white_check_mark', 'warning', 'rotating_light'] and item.get('type') == 'message':
            message_ts = item.get('ts')
            if message_ts in bot.active_standups:
                bot.handle_quick_reaction(user_id, message_ts, reaction)
                return "OK"
        
        if reaction == 'white_check_mark' and item.get('type') == 'message':
            # Handle completion reaction
            return _handle_completion_reaction(bot, user_id, item)
        
        return "OK"
    except Exception as e:
        print(f"Error handling reaction event: {e}")
        return "Error"

def _handle_bot_mention(bot, user_id, text, channel_id):
    """Handle bot mentions."""
    try:
        user_name = bot.get_user_name(user_id)
        
        # Extract command from mention
        mention_pattern = f'<@{bot.config.SLACK_BOT_USER_ID}>'
        command_text = text.replace(mention_pattern, '').strip()
        
        if not command_text:
            # Show help
            help_text = f"@{user_name} Here are the available commands:\\n"
            help_text += "• `/kr` - View or update your KRs\\n"
            help_text += "• `/checkin` - Check in with your status\\n"
            help_text += "• `/blocked` - Report a blocker\\n"
            help_text += "• `/health` - Health check\\n"
            help_text += "• `/blocker` - View your blockers\\n"
            help_text += "• `/role` - Manage your roles"
            
            bot.send_message(channel_id, help_text)
            return "OK"
        
        # Process as command
        parts = command_text.split(' ', 1)
        command = parts[0].lower()
        text_param = parts[1] if len(parts) > 1 else ""
        
        # Import the command processing function
        from .commands import _process_command
        _process_command(bot, user_id, command, text_param, channel_id)
        return "OK"
    except Exception as e:
        print(f"Error handling bot mention: {e}")
        return "Error"

def _handle_blocker_keyword(bot, user_id, text, channel_id):
    """Handle blocker keywords in messages."""
    try:
        user_name = bot.get_user_name(user_id)
        
        # Check if this is a new blocker report
        if 'blocker' in text.lower() or 'blocked' in text.lower():
            # Ask if they want to report a blocker
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"@{user_name} I noticed you mentioned being blocked. Would you like to report this as a formal blocker?"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Yes, report blocker"},
                            "action_id": "report_blocker",
                            "value": text
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "No, thanks"},
                            "action_id": "dismiss_blocker"
                        }
                    ]
                }
            ]
            
            bot.send_message(channel_id, "", blocks=blocks)
        
        return "OK"
    except Exception as e:
        print(f"Error handling blocker keyword: {e}")
        return "Error"

def _handle_completion_reaction(bot, user_id, item):
    """Handle completion reactions."""
    try:
        # This could be used to mark items as complete
        # For now, just log it
        print(f"User {user_id} marked item {item.get('ts')} as complete")
        return "OK"
    except Exception as e:
        print(f"Error handling completion reaction: {e}")
        return "Error"

# Removed Flask webhook routes - using Socket Mode instead

def handle_interactive_components(bot, payload):
    """Handle interactive components with comprehensive error handling."""
    try:
        # Validate payload structure - be more lenient for different payload types
        if not payload:
            return {"text": "OK"}
        
        # Check if this is a valid interactive component payload
        has_actions = 'actions' in payload and payload['actions']
        has_view = 'view' in payload and payload['view']
        has_user = 'user' in payload and payload['user']
        
        # Handle view_submission payloads (modal submissions)
        if payload.get('type') == 'view_submission':
            return handle_view_submission(bot, payload)
        
        # For block_actions, we need actions and user
        if not has_actions or not has_user:
            # Return OK instead of error to avoid spam
            return {"text": "OK"}
        
        actions = payload.get('actions', [])
        if not actions:
            return {"text": "OK"}
        
        action_id = actions[0].get('action_id', '')
        user_id = payload['user']['id']
        
        # Validate user ID
        if not input_validator.validate_user_id(user_id):
            return {"text": "OK"}
        
        # Route to appropriate handler
        if action_id == 'edit_blocker_note':
            return safe_executor.execute(handle_blocker_note_edit, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id in ['complete_blocker', 'complete_blocker_with_form']:
            return safe_executor.execute(handle_complete_blocker_with_form, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id in ['great', 'okay', 'not_great']:
            return safe_executor.execute(handle_health_response, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id in ['escalate_help', 'monitor_issue']:
            return safe_executor.execute(handle_followup_response, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id in ['health_share_public', 'health_share_private']:
            return safe_executor.execute(handle_health_share_response, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'health_no_share':
            return safe_executor.execute(handle_health_no_share, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id in ['mentor_yes', 'mentor_no']:
            return safe_executor.execute(handle_mentor_response, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id in ['blocker_resolved', 'blocker_still_blocked', 'blocker_need_help', 'claim_and_resolve_blocker', 'blocker_resolved_24hr', 'blocker_reescalate_24hr']:
            return safe_executor.execute(blocker_handle_followup_response, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'claim_blocker':
            return safe_executor.execute(handle_claim_blocker, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'update_progress':
            return safe_executor.execute(handle_update_progress, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'mark_resolved':
            return safe_executor.execute(handle_mark_resolved, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'view_blocker_details':
            return safe_executor.execute(handle_view_blocker_details, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'view_details':
            return safe_executor.execute(handle_view_details, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'submit_blocker_details':
            return safe_executor.execute(handle_submit_blocker_details, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'open_blocker_report_modal':
            return safe_executor.execute(handle_open_blocker_report_modal, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'open_blocker_modal_channel':
            return safe_executor.execute(handle_open_blocker_modal_channel, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'submit_blocker_form':
            return safe_executor.execute(handle_submit_blocker_form, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'open_checkin_modal':
            return safe_executor.execute(handle_open_checkin_modal, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'checkin_no_blocker':
            return safe_executor.execute(handle_checkin_no_blocker, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'view_all_blockers':
            return safe_executor.execute(handle_view_all_blockers, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'open_blocker_sprint_modal':
            return safe_executor.execute(handle_open_blocker_sprint_modal, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'open_kr_continue_modal':
            return safe_executor.execute(handle_open_kr_continue_modal, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'open_blocker_continue_modal':
            return safe_executor.execute(handle_open_blocker_continue_modal, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'view_blockers_with_sprint':
            return safe_executor.execute(handle_view_blockers_with_sprint, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'view_blockers_modal':
            return safe_executor.execute(handle_view_blockers_modal, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'open_view_blockers_modal':
            return safe_executor.execute(handle_open_view_blockers_modal, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'kr_continue_submit':
            return safe_executor.execute(handle_kr_continue_submit, "handle_interactive_components", user_id, bot=bot, payload=payload)
        elif action_id == 'blocker_continue_submit':
            return safe_executor.execute(handle_blocker_continue_submit, "handle_interactive_components", user_id, bot=bot, payload=payload)
        else:
            logger.warning(f"Unhandled action_id: {action_id}")
            return {"text": "OK"}
            
    except Exception as e:
        return error_handler.handle_unexpected_error(
            e, "handle_interactive_components"
        )



# Health handlers moved to handlers/health_handlers.py

def handle_update_progress(bot, payload):
    """Moved to handlers.blocker_handlers.handle_update_progress"""
    from .handlers.blocker_handlers import handle_update_progress as _h
    return _h(bot, payload)

def handle_mark_resolved(bot, payload):
    """Moved to handlers.blocker_handlers.handle_mark_resolved"""
    from .handlers.blocker_handlers import handle_mark_resolved as _h
    return _h(bot, payload)

# Moved to handlers.submission_handlers

# Removed duplicate handle_blocker_report_submission function to prevent duplicate saves



def handle_view_blocker_details(bot, payload):
    """Moved to handlers.blocker_handlers.handle_view_blocker_details"""
    from .handlers.blocker_handlers import handle_view_blocker_details as _h
    return _h(bot, payload)

# Moved to handlers.view_handlers

def handle_submit_blocker_details(bot, payload):
    """Moved to handlers.blocker_handlers.handle_submit_blocker_details"""
    from .handlers.blocker_handlers import handle_submit_blocker_details as _h
    return _h(bot, payload)

def handle_followup_response(bot, payload):
    """Handle followup response buttons."""
    try:
        action_id = payload['actions'][0]['action_id']
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        trigger_id = payload['trigger_id']
        
        if action_id == 'escalate_help':
            # User needs immediate help - send blocker form
            blocks = [
                {
                    "type": "input",
                    "block_id": "blocker_description",
                    "label": {"type": "plain_text", "text": "What's blocking you?"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "blocker_description_input",
                        "multiline": True,
                        "placeholder": {"type": "plain_text", "text": "Describe the blocker in detail..."}
                    }
                },
                {
                    "type": "input",
                    "block_id": "kr_name",
                    "label": {"type": "plain_text", "text": "Key Result (KR) Name"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "kr_name_input",
                        "placeholder": {"type": "plain_text", "text": "e.g., KR1: Increase user engagement"}
                    }
                },
                {
                    "type": "input",
                    "block_id": "urgency",
                    "label": {"type": "plain_text", "text": "Urgency Level"},
                    "element": {
                        "type": "static_select",
                        "action_id": "urgency_input",
                        "placeholder": {"type": "plain_text", "text": "Select urgency level"},
                        "options": [
                            {"text": {"type": "plain_text", "text": "Low - Can wait a few days"}, "value": "Low"},
                            {"text": {"type": "plain_text", "text": "Medium - Need help this week"}, "value": "Medium"},
                            {"text": {"type": "plain_text", "text": "High - Blocking progress now"}, "value": "High"},
                            {"text": {"type": "plain_text", "text": "Critical - Blocking team/delivery"}, "value": "Critical"}
                        ]
                    }
                },
                {
                    "type": "input",
                    "block_id": "notes",
                    "label": {"type": "plain_text", "text": "Additional Notes (Optional)"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "notes_input",
                        "multiline": True,
                        "placeholder": {"type": "plain_text", "text": "Any additional context or details..."}
                    },
                    "optional": True
                }
            ]
            
            bot.open_modal(
                trigger_id=trigger_id,
                title="Submit Blocker Details",
                blocks=blocks,
                submit_text="Submit Blocker",
                callback_id="blocker_details_submit"
            )
            
        elif action_id == 'monitor_issue':
            # User can wait - acknowledge
            bot.send_dm(user_id, f"@{user_name} Thanks for letting us know. We'll check in with you later if needed.")
        
        return {"text": "OK"}
    except Exception as e:
        print(f"Error handling followup response: {e}")
        return {"text": "Error"}

def handle_health_share_response(bot, payload):
    """Moved to handlers.health_handlers.handle_health_share_response"""
    return __import__('slack-bot-1.src.handlers.health_handlers'.replace('-', '_'), fromlist=['handle_health_share_response']).handle_health_share_response(bot, payload)

# Removed duplicate handle_blocker_details_submission function to prevent duplicate saves

def handle_health_public_share_submission(bot, payload):
    """Moved to handlers.health_handlers.handle_health_public_share_submission"""
    return __import__('slack-bot-1.src.handlers.health_handlers'.replace('-', '_'), fromlist=['handle_health_public_share_submission']).handle_health_public_share_submission(bot, payload)

def handle_health_no_share(bot, payload):
    """Moved to handlers.health_handlers.handle_health_no_share"""
    return __import__('slack-bot-1.src.handlers.health_handlers'.replace('-', '_'), fromlist=['handle_health_no_share']).handle_health_no_share(bot, payload)

def handle_health_private_share_submission(bot, payload):
    """Moved to handlers.health_handlers.handle_health_private_share_submission"""
    return __import__('slack-bot-1.src.handlers.health_handlers'.replace('-', '_'), fromlist=['handle_health_private_share_submission']).handle_health_private_share_submission(bot, payload)

# Moved to handlers.blocker_resolution_handlers

# Moved to handlers.blocker_resolution_handlers

# Moved to handlers.blocker_resolution_handlers

# Moved to handlers.blocker_resolution_handlers

# Moved to handlers.modal_handlers

def handle_submit_blocker_form(bot, payload):
    """Handle submission of the blocker form from interactive blocks with duplicate prevention."""
    try:
        print(f"🔍 DEBUG: handle_submit_blocker_form called with payload: {payload}")
        
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        channel_id = payload['channel']['id']
        message_ts = payload['message']['ts']
        
        # Extract form data from the payload
        state = payload.get('state', {})
        values = state.get('values', {})
        
        # Extract the form fields
        sprint_number = values.get('sprint_number', {}).get('sprint_number_input', {}).get('value', '')
        kr_name = values.get('kr_name', {}).get('kr_name_input', {}).get('value', '')
        blocker_description = values.get('blocker_description', {}).get('blocker_description_input', {}).get('value', '')
        urgency = values.get('urgency', {}).get('urgency_select', {}).get('selected_option', {}).get('value', 'medium')
        notes = values.get('notes', {}).get('notes_input', {}).get('value', '')
        
        print(f"🔍 DEBUG: Form data - Sprint: {sprint_number}, KR: {kr_name}, Description: {blocker_description}, Urgency: {urgency}, Notes: {notes}")
        
        # Validate required fields
        missing_fields = []
        if not sprint_number:
            missing_fields.append("Sprint Number")
        if not kr_name:
            missing_fields.append("KR Name")
        if not blocker_description:
            missing_fields.append("Description")
        
        if missing_fields:
            # Store the data for field memory and ask user to complete missing fields
            bot.store_blocker_pending_data(
                user_id,
                sprint_number=sprint_number,
                kr_name=kr_name,
                blocker_description=blocker_description,
                urgency=urgency,
                notes=notes
            )
            
            error_message = f"❌ *Missing Required Fields*\n\nPlease complete the following fields:\n• {', '.join(missing_fields)}\n\nYour progress has been saved. Use `/blocker` again to continue."
            bot.update_message(channel_id, message_ts, error_message)
            return {"response_action": "clear"}
        
        # Check for duplicate submission
        data_hash = f"{sprint_number}_{blocker_description[:50]}_{kr_name[:50]}_{urgency}_{notes[:50]}"
        if not track_submission(user_id, "submit_blocker_form", data_hash):
            bot.update_message(channel_id, message_ts, "⚠️ This blocker submission was already processed. Please wait a moment before trying again.")
            return {"response_action": "clear"}
        
        # Update the message with immediate confirmation
        immediate_message = f"✅ *Blocker Report Submitted!*\n\n*Sprint:* {sprint_number}\n*KR:* {kr_name}\n*Description:* {blocker_description}\n*Urgency:* {urgency.title()}\n*Notes:* {notes if notes else 'None'}\n\nProcessing in background..."
        bot.update_message(channel_id, message_ts, immediate_message)
        
        # Clear pending data since submission is complete
        bot.clear_pending_data(user_id, 'blocker')
        
        # Process the blocker submission in background thread
        def escalate_in_background():
            try:
                bot.escalate_blocker_with_details(
                    user_id=user_id,
                    user_name=user_name,
                    blocker_description=blocker_description,
                    kr_name=kr_name,
                    urgency=urgency,
                    notes=notes,
                    sprint_number=sprint_number
                )
                
                # Update the message with success
                success_message = f"✅ *Blocker Report Processed Successfully!*\n\n*Sprint:* {sprint_number}\n*KR:* {kr_name}\n*Description:* {blocker_description}\n*Urgency:* {urgency.title()}\n*Notes:* {notes if notes else 'None'}\n\nYour blocker has been escalated to the team so anyone can help resolve it!"
                bot.update_message(channel_id, message_ts, success_message)
                
                print(f"✅ Blocker form submitted successfully for {user_name}")
                
            except Exception as e:
                print(f"❌ Error processing blocker submission: {e}")
                error_message = "❌ Sorry, there was an error processing your blocker. Please try again or contact your team lead directly."
                bot.update_message(channel_id, message_ts, error_message)
        
        # Start background thread
        import threading
        background_thread = threading.Thread(target=escalate_in_background)
        background_thread.daemon = True
        background_thread.start()
        
        return {"response_action": "clear"}
        
    except Exception as e:
        print(f"❌ Error in handle_submit_blocker_form: {e}")
        import traceback
        traceback.print_exc()
        return {"response_action": "clear"}

def handle_open_blocker_modal_channel(bot, payload):
    """Handle opening the blocker modal from the public channel."""
    try:
        print(f"🔍 DEBUG: handle_open_blocker_modal_channel called with payload: {payload}")
        
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        
        # Get the user ID from the button value
        actions = payload.get('actions', [])
        if actions:
            value = actions[0].get('value', '')
            print(f"🔍 DEBUG: Button value: {value}")
            
            parts = value.split('_')
            if len(parts) >= 3 and parts[0] == 'blocker' and parts[1] == 'modal':
                actual_user_id = parts[2]
                print(f"🔍 DEBUG: Actual user ID from button value: {actual_user_id}")
            else:
                print(f"❌ DEBUG: Could not parse user ID from button value: {value}")
                return {"response_action": "clear"}
        else:
            print(f"❌ DEBUG: No actions found in payload")
            return {"response_action": "clear"}
        
        # Check if trigger_id exists (should exist in public channel)
        trigger_id = payload.get('trigger_id')
        print(f"🔍 DEBUG: trigger_id: {trigger_id}")
        
        if not trigger_id:
            print(f"❌ DEBUG: No trigger_id found in channel payload")
            return {"response_action": "clear"}
        
        # Create modal for blocker report
        blocks = [
            {
                "type": "input",
                "block_id": "kr_name",
                "label": {"type": "plain_text", "text": "Which KR is this blocker related to?"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "kr_name_input",
                    "placeholder": {"type": "plain_text", "text": "e.g., Implement user authentication"}
                }
            },
            {
                "type": "input",
                "block_id": "blocker_description",
                "label": {"type": "plain_text", "text": "Describe the blocker:"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "blocker_description_input",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "What's blocking your progress?"}
                }
            },
            {
                "type": "input",
                "block_id": "urgency",
                "label": {"type": "plain_text", "text": "Urgency level:"},
                "element": {
                    "type": "static_select",
                    "action_id": "urgency_select",
                    "placeholder": {"type": "plain_text", "text": "Select urgency"},
                    "options": [
                        {"text": {"type": "plain_text", "text": "Low"}, "value": "low"},
                        {"text": {"type": "plain_text", "text": "Medium"}, "value": "medium"},
                        {"text": {"type": "plain_text", "text": "High"}, "value": "high"},
                        {"text": {"type": "plain_text", "text": "Critical"}, "value": "critical"}
                    ]
                }
            },
            {
                "type": "input",
                "block_id": "notes",
                "label": {"type": "plain_text", "text": "Additional notes (optional):"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "notes_input",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "Any additional context..."}
                },
                "optional": True
            }
        ]
        
        # Open modal
        modal_result = bot.open_modal(
            trigger_id=trigger_id,
            title="Report Blocker",
            blocks=blocks,
            submit_text="Submit Blocker Report",
            callback_id="blocker_report_submit"
        )
        
        if modal_result:
            print(f"✅ DEBUG: Blocker report modal opened successfully from channel")
        else:
            print(f"❌ DEBUG: Failed to open blocker report modal from channel")
        
        return {"response_action": "clear"}
    except Exception as e:
        print(f"❌ Error in handle_open_blocker_modal_channel: {e}")
        import traceback
        traceback.print_exc()
        return {"response_action": "clear"}

# Moved to handlers.modal_handlers

def handle_checkin_no_blocker(bot, payload):
    """Handle when user clicks 'No Blocker to Report' after check-in prompt."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        
        # Send acknowledgment message
        bot.send_dm(user_id, "✅ Understood! No blocker to report. If you encounter any issues later, feel free to use `/blocked` to report them.")
        
        return {"text": "OK"}
        
    except Exception as e:
        print(f"Error handling checkin no blocker: {e}")
        return {"text": "OK"}

def handle_blocker_sprint_modal_submission(bot, payload):
    """Handle blocker sprint modal submission - show user's blockers filtered by sprint."""
    try:
        import threading
        
        def process_blocker_sprint_command():
            try:
                user_id = payload['user']['id']
                user_name = bot.get_user_name(user_id)
                values = payload['view']['state']['values']
                
                # Extract sprint number from form
                sprint_input = values.get('sprint_input', {}).get('sprint_number', {})
                sprint_number = sprint_input.get('value', '').strip()
                
                print(f"🔍 DEBUG: Processing blocker sprint command for user {user_name}, sprint: '{sprint_number}'")
                
                # Get user's blockers filtered by sprint
                try:
                    blockers = bot.coda.get_user_blockers_by_sprint(user_id, sprint_number if sprint_number else None)
                    print(f"🔍 DEBUG: Blockers fetched: {len(blockers)} blockers")
                    
                    if not blockers:
                        sprint_text = f" in Sprint {sprint_number}" if sprint_number else ""
                        bot.send_dm(user_id, f"You have no active blockers{sprint_text}.")
                        return
                    
                    # Create blocks for each blocker
                    blocks = []
                    sprint_text = f" (Sprint {sprint_number})" if sprint_number else ""
                    
                    for idx, blocker in enumerate(blockers, 1):
                        block_text = f"*Blocker {idx}:{sprint_text}\\n*KR:* {blocker['kr_name']}\\n*Description:* {blocker['blocker_description']}\\n*Urgency:* {blocker['urgency']}\\n*Notes:* {blocker['notes']}"
                        blocks.append({
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": block_text},
                            "block_id": f"blocker_{blocker['row_id']}"
                        })
                        blocks.append({
                            "type": "actions",
                            "block_id": f"actions_{blocker['row_id']}",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Add/Edit Note"},
                                    "action_id": "edit_blocker_note",
                                    "value": blocker['row_id']
                                },
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Update Progress"},
                                    "action_id": "update_progress",
                                    "value": f"blocker_{blocker['row_id']}_{blocker['kr_name']}"
                                },
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Mark Resolved"},
                                    "style": "primary",
                                    "action_id": "mark_resolved",
                                    "value": f"blocker_{blocker['row_id']}_{blocker['kr_name']}"
                                }
                            ]
                        })
                    
                    sprint_header = f" (Sprint {sprint_number})" if sprint_number else ""
                    print(f"🔍 DEBUG: Sending blocker list with blocks: {len(blocks)} blocks")
                    bot.send_dm(user_id, f"Here are your current blockers{sprint_header}:", blocks=blocks)
                    
                except Exception as e:
                    print(f"❌ Error getting blockers: {e}")
                    bot.send_dm(user_id, "❌ Error retrieving your blockers. Please try again.")
                        
            except Exception as e:
                print(f"❌ Error in background blocker sprint processing: {e}")
                bot.send_dm(user_id, "❌ Error processing blocker command. Please try again.")
        
        thread = threading.Thread(target=process_blocker_sprint_command)
        thread.daemon = True
        thread.start()
        
        return {"response_action": "clear"}
        
    except Exception as e:
        print(f"❌ Error in blocker sprint modal submission handler: {e}")
        return {"response_action": "clear"}

def handle_view_all_blockers(bot, payload):
    """Handle 'View All Blockers' button click."""
    try:
        import threading
        
        def process_view_all_blockers():
            try:
                user_id = payload['user']['id']
                user_name = bot.get_user_name(user_id)
                
                print(f"🔍 DEBUG: Processing view all blockers for user {user_name}")
                
                # Get user's blockers (no sprint filter)
                try:
                    blockers = bot.coda.get_user_blockers_by_sprint(user_id, None)
                    print(f"🔍 DEBUG: Blockers fetched: {len(blockers)} blockers")
                    
                    if not blockers:
                        bot.send_dm(user_id, "You have no active blockers.")
                        return
                    
                    # Create blocks for each blocker
                    blocks = []
                    for idx, blocker in enumerate(blockers, 1):
                        block_text = f"*Blocker {idx}:\\n*KR:* {blocker['kr_name']}\\n*Description:* {blocker['blocker_description']}\\n*Urgency:* {blocker['urgency']}\\n*Notes:* {blocker['notes']}"
                        blocks.append({
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": block_text},
                            "block_id": f"blocker_{blocker['row_id']}"
                        })
                        blocks.append({
                            "type": "actions",
                            "block_id": f"actions_{blocker['row_id']}",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Add/Edit Note"},
                                    "action_id": "edit_blocker_note",
                                    "value": blocker['row_id']
                                },
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Update Progress"},
                                    "action_id": "update_progress",
                                    "value": f"blocker_{blocker['row_id']}_{blocker['kr_name']}"
                                },
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Mark Resolved"},
                                    "style": "primary",
                                    "action_id": "mark_resolved",
                                    "value": f"blocker_{blocker['row_id']}_{blocker['kr_name']}"
                                }
                            ]
                        })
                    
                    print(f"🔍 DEBUG: Sending blocker list with blocks: {len(blocks)} blocks")
                    bot.send_dm(user_id, "Here are your current blockers:", blocks=blocks)
                    
                except Exception as e:
                    print(f"❌ Error getting blockers: {e}")
                    bot.send_dm(user_id, "❌ Error retrieving your blockers. Please try again.")
                        
            except Exception as e:
                print(f"❌ Error in background view all blockers processing: {e}")
                bot.send_dm(user_id, "❌ Error processing blocker command. Please try again.")
        
        thread = threading.Thread(target=process_view_all_blockers)
        thread.daemon = True
        thread.start()
        
        return {"text": "OK"}
        
    except Exception as e:
        print(f"❌ Error in view all blockers handler: {e}")
        return {"text": "OK"}

def handle_open_blocker_sprint_modal(bot, payload):
    """Handle 'Filter by Sprint' button click - open modal to get sprint number."""
    try:
        trigger_id = payload.get('trigger_id')
        if not trigger_id:
            print(f"❌ DEBUG: No trigger_id found in payload")
            return {"text": "OK"}
        
        # Create modal blocks for sprint input
        blocks = [
            {
                "type": "input",
                "block_id": "sprint_input",
                "label": {
                    "type": "plain_text",
                    "text": "Sprint Number"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "sprint_number",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "e.g., 8, 9, 10"
                    }
                },
                "optional": True
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Enter a sprint number to filter blockers, or leave empty to see all blockers"
                    }
                ]
            }
        ]
        
        # Open modal to get sprint number
        success = bot.open_modal(
            trigger_id=trigger_id,
            title="View Blockers by Sprint",
            blocks=blocks,
            submit_text="View Blockers",
            callback_id="blocker_sprint_modal"
        )
        
        if success:
            print(f"✅ DEBUG: Blocker sprint modal opened successfully")
        else:
            print(f"❌ DEBUG: Failed to open blocker sprint modal")
        
        return {"text": "OK"}
        
    except Exception as e:
        print(f"❌ Error in open blocker sprint modal handler: {e}")
        return {"text": "OK"}

# Moved to handlers.kr_handlers

def handle_open_blocker_continue_modal(bot, payload):
    """Handle 'Continue Blocker' button click - open full blocker modal with pre-filled data."""
    try:
        trigger_id = payload.get('trigger_id')
        if not trigger_id:
            print(f"❌ DEBUG: No trigger_id found in payload")
            return {"text": "OK"}
        
        user_id = payload.get('user', {}).get('id')
        if not user_id:
            print(f"❌ DEBUG: No user_id found in payload")
            return {"text": "OK"}
        
        # Get the pending blocker data for this user
        pending_data = bot.pending_blocker_sprint.get(user_id, {})
        
        if not pending_data:
            bot.send_dm(user_id, "No pending blocker data found. Please start a new blocker request.")
            return {"text": "OK"}
        
        # Create the full blocker modal with pre-filled data
        blocks = [
            {
                "type": "input",
                "block_id": "kr_name",
                "label": {
                    "type": "plain_text",
                    "text": "KR Name"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "kr_name",
                    "initial_value": pending_data.get("kr_name", ""),
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter the KR name"
                    }
                }
            },
            {
                "type": "input",
                "block_id": "blocker_description",
                "label": {
                    "type": "plain_text",
                    "text": "Blocker Description"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "blocker_description",
                    "initial_value": pending_data.get("blocker_description", ""),
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Describe the blocker"
                    }
                }
            },
            {
                "type": "input",
                "block_id": "urgency",
                "label": {
                    "type": "plain_text",
                    "text": "Urgency"
                },
                "element": {
                    "type": "static_select",
                    "action_id": "urgency",
                    "initial_option": {
                        "text": {"type": "plain_text", "text": pending_data.get("urgency", "medium").title()},
                        "value": pending_data.get("urgency", "medium")
                    },
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select urgency level"
                    },
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "Low"},
                            "value": "low"
                        },
                        {
                            "text": {"type": "plain_text", "text": "Medium"},
                            "value": "medium"
                        },
                        {
                            "text": {"type": "plain_text", "text": "High"},
                            "value": "high"
                        },
                        {
                            "text": {"type": "plain_text", "text": "Critical"},
                            "value": "critical"
                        }
                    ]
                }
            },
            {
                "type": "input",
                "block_id": "notes",
                "label": {
                    "type": "plain_text",
                    "text": "Notes (Optional)"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "notes",
                    "initial_value": pending_data.get("notes", ""),
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Additional notes or context"
                    }
                },
                "optional": True
            },
            {
                "type": "input",
                "block_id": "sprint_number",
                "label": {
                    "type": "plain_text",
                    "text": "Sprint Number"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "sprint_number",
                    "initial_value": str(pending_data.get("sprint_number", "")),
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter sprint number"
                    }
                }
            }
        ]
        
        # Open the full blocker modal
        success = bot.open_modal(
            trigger_id=trigger_id,
            title="Continue Blocker Entry",
            blocks=blocks,
            submit_text="Submit",
            callback_id="blocker_continue_submit"
        )
        
        if success:
            print(f"✅ DEBUG: Blocker continue modal opened successfully with pre-filled data")
        else:
            print(f"❌ DEBUG: Failed to open blocker continue modal")
        
        return {"text": "OK"}
        
    except Exception as e:
        print(f"❌ Error in open blocker continue modal handler: {e}")
        return {"text": "OK"}

def handle_view_blockers_with_sprint(bot, payload):
    """Handle 'View Blockers with Sprint' button click - show blockers filtered by sprint."""
    try:
        def process_view_blockers_with_sprint():
            try:
                user_id = payload['user']['id']
                user_name = bot.get_user_name(user_id)
                
                # This function is called from a button click, not modal submission
                # For now, show all blockers (no sprint filtering)
                sprint_number = None
                
                print(f"🔍 DEBUG: Processing view blockers command for user {user_name}, sprint: '{sprint_number}'")
                
                # Get user's blockers filtered by sprint
                try:
                    blockers = bot.coda.get_user_blockers_by_sprint(user_id, sprint_number if sprint_number else None)
                    print(f"🔍 DEBUG: Blockers fetched: {len(blockers)} blockers")
                    
                    if not blockers:
                        sprint_text = f" in Sprint {sprint_number}" if sprint_number else ""
                        bot.send_dm(user_id, f"You have no active blockers{sprint_text}.")
                        return
                    
                    # Create blocks for each blocker
                    blocks = []
                    sprint_text = f" (Sprint {sprint_number})" if sprint_number else ""
                    
                    for idx, blocker in enumerate(blockers, 1):
                        block_text = f"*Blocker {idx}:{sprint_text}\\n*KR:* {blocker['kr_name']}\\n*Description:* {blocker['blocker_description']}\\n*Urgency:* {blocker['urgency']}\\n*Notes:* {blocker['notes']}"
                        blocks.append({
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": block_text},
                            "block_id": f"blocker_{blocker['row_id']}"
                        })
                        blocks.append({
                            "type": "actions",
                            "block_id": f"actions_{blocker['row_id']}",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Add/Edit Note"},
                                    "action_id": "edit_blocker_note",
                                    "value": blocker['row_id']
                                },
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Update Progress"},
                                    "action_id": "update_progress",
                                    "value": f"blocker_{blocker['row_id']}_{blocker['kr_name']}"
                                },
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Mark Resolved"},
                                    "style": "primary",
                                    "action_id": "mark_resolved",
                                    "value": f"blocker_{blocker['row_id']}_{blocker['kr_name']}"
                                }
                            ]
                        })
                    
                    sprint_header = f" (Sprint {sprint_number})" if sprint_number else ""
                    print(f"🔍 DEBUG: Sending blocker list with blocks: {len(blocks)} blocks")
                    bot.send_dm(user_id, f"Here are your current blockers{sprint_header}:", blocks=blocks)
                    
                except Exception as e:
                    print(f"❌ Error getting blockers: {e}")
                    bot.send_dm(user_id, "❌ Error retrieving your blockers. Please try again.")
                        
            except Exception as e:
                print(f"❌ Error in background view blockers with sprint processing: {e}")
                bot.send_dm(user_id, "❌ Error processing blocker command. Please try again.")
        
        thread = threading.Thread(target=process_view_blockers_with_sprint)
        thread.daemon = True
        thread.start()
        
        return {"response_action": "clear"}
        
    except Exception as e:
        print(f"❌ Error in view blockers with sprint handler: {e}")
        return {"response_action": "clear"}

def handle_view_blockers_modal(bot, payload):
    """Handle view blockers modal submission."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']
        
        # Extract sprint number from modal
        sprint_input = values.get('sprint_number', {}).get('sprint_number_input', {})
        sprint_number = sprint_input.get('value', '').strip()
        
        print(f"🔍 DEBUG: Processing view blockers modal for user {user_name}, sprint: '{sprint_number}'")
        
        # Get user's blockers filtered by sprint
        try:
            blockers = bot.coda.get_user_blockers_by_sprint(user_id, sprint_number if sprint_number else None)
            print(f"🔍 DEBUG: Blockers fetched: {len(blockers)} blockers")
            
            if not blockers:
                sprint_text = f" in Sprint {sprint_number}" if sprint_number else ""
                bot.send_dm(user_id, f"You have no active blockers{sprint_text}.")
                return {"response_action": "clear"}
            
            # Create blocks for each blocker
            blocks = []
            sprint_text = f" (Sprint {sprint_number})" if sprint_number else ""
            
            for idx, blocker in enumerate(blockers, 1):
                block_text = f"*Blocker {idx}:{sprint_text}\\n*KR:* {blocker['kr_name']}\\n*Description:* {blocker['blocker_description']}\\n*Urgency:* {blocker['urgency']}\\n*Notes:* {blocker['notes']}"
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": block_text},
                    "block_id": f"blocker_{blocker['row_id']}"
                })
                blocks.append({
                    "type": "actions",
                    "block_id": f"actions_{blocker['row_id']}",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Mark Resolved"},
                            "style": "primary",
                            "action_id": "mark_resolved",
                            "value": f"blocker_{blocker['row_id']}_{blocker['kr_name']}"
                        }
                    ]
                })
            
            sprint_header = f" (Sprint {sprint_number})" if sprint_number else ""
            print(f"🔍 DEBUG: Sending blocker list with blocks: {len(blocks)} blocks")
            bot.send_dm(user_id, f"Here are your current blockers{sprint_header}:", blocks=blocks)
            
        except Exception as e:
            print(f"❌ Error getting blockers: {e}")
            bot.send_dm(user_id, "❌ Error retrieving your blockers. Please try again.")
            
        return {"response_action": "clear"}
        
    except Exception as e:
        print(f"❌ Error in view blockers modal handler: {e}")
        return {"response_action": "clear"}

def handle_open_view_blockers_modal(bot, payload):
    """Handle opening the view blockers modal."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        
        print(f"🔍 DEBUG: Opening view blockers modal for user {user_name}")
        
        # Create modal view
        modal_view = {
            "type": "modal",
            "callback_id": "view_blockers_modal",
            "title": {"type": "plain_text", "text": "View Your Blockers"},
            "submit": {"type": "plain_text", "text": "View Blockers"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "sprint_number",
                    "label": {
                        "type": "plain_text",
                        "text": "Sprint Number (Optional)"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "sprint_number_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "e.g., 5 (leave blank for all blockers)"
                        },
                        "optional": True
                    }
                }
            ]
        }
        
        # Open the modal
        try:
            bot.client.views_open(
                trigger_id=payload['trigger_id'],
                view=modal_view
            )
            print(f"✅ Modal opened successfully for {user_name}")
        except Exception as e:
            print(f"❌ Error opening modal: {e}")
            # Fallback: send a simple message asking for sprint number
            bot.send_dm(user_id, "Please type a sprint number to view your blockers (or leave blank for all blockers):")
            
        return {"text": "OK"}
        
    except Exception as e:
        print(f"❌ Error in open view blockers modal handler: {e}")
        return {"text": "OK"}

# Moved to handlers.kr_handlers

def handle_blocker_continue_submit(bot, payload):
    """Handle blocker continue submit form submission."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']
        
        # Extract form data
        kr_name = values.get('kr_name', {}).get('kr_name', {}).get('value', '').strip()
        blocker_description = values.get('blocker_description', {}).get('blocker_description', {}).get('value', '').strip()
        urgency = values.get('urgency', {}).get('urgency', {}).get('selected_option', {}).get('value', 'medium')
        notes = values.get('notes', {}).get('notes', {}).get('value', '').strip()
        sprint_number = values.get('sprint_number', {}).get('sprint_number', {}).get('value', '').strip()
        
        print(f"🔍 DEBUG: Blocker continue submit - kr_name: '{kr_name}', description: '{blocker_description[:50]}...', urgency: '{urgency}', sprint: '{sprint_number}'")
        
        # Validate required fields
        if not kr_name:
            bot.send_dm(user_id, "❌ KR name is required. Please try again.")
            return {"response_action": "clear"}
        
        if not blocker_description:
            bot.send_dm(user_id, "❌ Blocker description is required. Please try again.")
            return {"response_action": "clear"}
        
        if not sprint_number:
            bot.send_dm(user_id, "❌ Sprint number is required. Please try again.")
            return {"response_action": "clear"}
        
        # Clear pending data since we're processing the complete form
        bot.clear_pending_data(user_id, 'blocker')
        
        # Send immediate confirmation and close modal
        bot.send_dm(user_id, f"✅ Blocker submitted! Processing in background...")
        
        # Process blocker submission in background to avoid Slack timeout
        def process_blocker_submission_in_background():
            try:
                # Escalate the blocker to the channel
                bot.escalate_blocker_with_details(
                    user_id=user_id,
                    user_name=user_name,
                    blocker_description=blocker_description,
                    kr_name=kr_name,
                    urgency=urgency,
                    notes=notes,
                    sprint_number=sprint_number
                )
                
                # Send confirmation to user
                bot.send_dm(user_id, f"✅ Blocker submitted successfully!\n\n*KR:* {kr_name}\n*Description:* {blocker_description}\n*Urgency:* {urgency.title()}\n*Sprint:* {sprint_number}\n\nYour blocker has been escalated to the team so anyone can help resolve it!")
                
            except Exception as e:
                print(f"❌ Error processing blocker submission: {e}")
                bot.send_dm(user_id, "❌ Error processing blocker submission. Please try again.")
        
        # Start background processing
        import threading
        thread = threading.Thread(target=process_blocker_submission_in_background)
        thread.daemon = True
        thread.start()
        
        # Return proper response for Socket Mode
        return {"response_action": "clear"}
        
    except Exception as e:
        print(f"Error handling blocker continue submit: {e}")
        bot.send_dm(user_id, "❌ Error processing blocker continue. Please try again.")
        return {"response_action": "clear"}

# Moved to handlers.blocker_resolution_handlers