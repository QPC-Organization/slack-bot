import json
import threading
import traceback
import time
# Removed Flask imports - using Socket Mode
from .utils import logger, error_handler, input_validator, safe_executor

def _process_command(bot, user_id, command, text="", channel_id=None):
    """Process slash commands."""
    user_name = bot.get_user_name(user_id)
    print(f"Processing command '{command}' from user {user_name} ({user_id})")
    
    if command == 'help':
        return _handle_help_command(bot, user_id, channel_id)
    elif command == 'kr':
        return _handle_kr_command(bot, user_id, text, channel_id)
    elif command == 'checkin':
        return _handle_checkin_command(bot, user_id, channel_id)
    elif command == 'blocked':
        return _handle_blocked_command(bot, user_id, channel_id)
    elif command == 'health':
        return _handle_health_command(bot, user_id, channel_id)
    elif command == 'role':
        return _handle_role_command(bot, user_id, text, channel_id)
    elif command == 'rolelist':
        return _handle_rolelist_command(bot, user_id, channel_id)
    elif command == 'autorole':
        return _handle_autorole_command(bot, user_id, text, channel_id)
    elif command == 'test_standup':
        return _handle_test_standup_command(bot, user_id, channel_id)
    elif command == 'test_health':
        return _handle_test_health_command(bot, user_id, channel_id)
    elif command in ['blocker', 'blockers']:
        return _handle_blocker_command(bot, user_id, channel_id)
    else:
        print(f"Unknown command: {command}")
        return False

def _handle_help_command(bot, user_id, channel_id):
    """Handle /help command."""
    try:
        user_name = bot.get_user_name(user_id)
        
        # Create properly formatted help blocks
        help_blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🤖 Bot Commands Help",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Daily Workflow Commands:*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "• `/checkin` — Start your daily standup\n• `/health` — Send a health check prompt\n• `/kr (sprint) (kr_name)` — Search for a Key Result in a specific sprint\n• `/kr mine (sprint_number)` — Show your own KRs in a specific sprint\n• `/blocked` — Report a new blocker\n• `/blocker` — View your current blockers"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Role Management Commands:*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "• `/role` — Show role help and manage roles (includes auto-assignment)\n• `/rolelist` — List all roles and users"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Admin Commands:*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "• `/test_standup` — Trigger daily standup (admin only)\n• `/test_health` — Trigger health check (admin only)"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "💡 Use `/role` for detailed role management help"
                }
            ]
        }
    ]
    
        # Send as DM with blocks formatting
        bot.send_dm(user_id, "Here are all available commands:", blocks=help_blocks)
        return True
        
    except Exception as e:
        print(f"❌ Error in _handle_help_command: {e}")
        return False

def _handle_kr_command(bot, user_id, text, channel_id):
    """Handle /kr command with sprint number requirement and field memory."""
    try:
        import threading
        def process_kr_command():
            try:
                time.sleep(1.0)
                try:
                    user_info = bot.client.users_info(user=user_id)
                    user_name = user_info['user']['real_name']
                except Exception as e:
                    print(f"❌ Error getting user info: {e}")
                    user_name = f"User {user_id}"
                
                # Check if user has pending KR data to continue
                if hasattr(bot, 'pending_kr_search') and user_id in bot.pending_kr_search:
                    pending_data = bot.pending_kr_search[user_id]
                    bot.send_kr_continue_form(user_id, user_name, pending_data)
                else:
                    # Parse command text for sprint number and KR name
                    parts = text.split() if text else []
                    sprint_number = None
                    search_term = None
                    is_mine_command = False
                    
                    if parts:
                        # Check if this is a 'mine' command
                        if parts[0].lower() == 'mine':
                            is_mine_command = True
                            if len(parts) > 1:
                                # Try to parse sprint number after 'mine'
                                try:
                                    sprint_number = int(parts[1])
                                except ValueError:
                                    bot.send_dm(user_id, f"❌ *Invalid Format*\n\nPlease use the format: `/kr mine (sprint_number)`\n\n*Examples:*\n• `/kr mine 5` - Show your KRs in Sprint 5\n• `/kr mine 3` - Show your KRs in Sprint 3")
                                    return
                            else:
                                bot.send_dm(user_id, f"❌ *Sprint Number Required*\n\nPlease use the format: `/kr mine (sprint_number)`\n\n*Examples:*\n• `/kr mine 5` - Show your KRs in Sprint 5\n• `/kr mine 3` - Show your KRs in Sprint 3")
                                return

                        else:
                            # Regular KR search - First part should be sprint number
                            try:
                                sprint_number = int(parts[0])
                                # Everything after sprint number is the KR search term
                                if len(parts) > 1:
                                    search_term = ' '.join(parts[1:])
                            except ValueError:
                                # If first part isn't a number, show error
                                bot.send_dm(user_id, f"❌ *Invalid Format*\n\nPlease use the format: `/kr (sprint_number) (kr_name)` or `/kr mine (sprint_number)`\n\n*Examples:*\n• `/kr 5` - Search for KRs in Sprint 5\n• `/kr 5 user engagement` - Search for 'user engagement' in Sprint 5\n• `/kr mine 5` - Show your KRs in Sprint 5")
                                return
                    
                    # If no sprint number provided, ask for it
                    if not sprint_number:
                        bot.send_dm(user_id, f"❌ *Sprint Number Required*\n\nPlease use the format: `/kr (sprint_number) (kr_name)` or `/kr mine (sprint_number)`\n\n*Examples:*\n• `/kr 5` - Search for KRs in Sprint 5\n• `/kr 5 user engagement` - Search for 'user engagement' in Sprint 5\n• `/kr mine 5` - Show your KRs in Sprint 5")
                        return
                    
                    if is_mine_command:
                        # Handle KR mine command - directly get user's KRs
                        print(f"🔍 DEBUG: Processing KR mine command for user {user_name}, sprint: {sprint_number}")
                        print(f"🔍 DEBUG: User ID: {user_id}, Username: {user_name}")
                        
                        # Send initial message
                        bot.send_dm(user_id, f"🔍 Searching for your KRs in Sprint {sprint_number}...")
                        
                        # Get user's KRs from Coda
                        if bot.coda:
                            print(f"🔍 DEBUG: Coda service is available")
                            try:
                                print(f"🔍 DEBUG: Calling bot.coda.get_user_krs({user_id}, {user_name}, {sprint_number})")
                                user_krs = bot.coda.get_user_krs(user_id, user_name, sprint_number)
                                print(f"🔍 DEBUG: get_user_krs returned: {len(user_krs) if user_krs else 0} KRs")
                                
                                if not user_krs:
                                    bot.send_dm(user_id, f"❌ No KRs found assigned to you in Sprint {sprint_number}.")
                                    return
                                
                                # Format and send results
                                result_text = f"✅ *Found {len(user_krs)} KRs assigned to you in Sprint {sprint_number}:*\n\n"
                                
                                for i, kr in enumerate(user_krs, 1):
                                    kr_name = kr.get('kr_name', 'N/A')
                                    owner = kr.get('owner', 'N/A')
                                    assignee = kr.get('assignee', 'N/A')
                                    status = kr.get('status', 'N/A')
                                    sprint = kr.get('sprint', 'N/A')
                                    definition_of_done = kr.get('definition_of_done', 'N/A')
                                    
                                    result_text += f"*KR {i}:* {kr_name}\n"
                                    if owner != 'N/A':
                                        result_text += f"  • Owner: {owner}\n"
                                    if assignee != 'N/A':
                                        result_text += f"  • Assignee: {assignee}\n"
                                    if status != 'N/A':
                                        result_text += f"  • Status: {status}\n"
                                    if sprint != 'N/A':
                                        result_text += f"  • Sprint: {sprint}\n"
                                    if definition_of_done != 'N/A':
                                        # Truncate long definitions
                                        dod_text = definition_of_done[:100] + "..." if len(str(definition_of_done)) > 100 else definition_of_done
                                        result_text += f"  • Definition of Done: {dod_text}\n"
                                    result_text += "\n"
                                
                                # Send the results
                                bot.send_dm(user_id, result_text)
                                
                            except Exception as e:
                                print(f"❌ Error getting user KRs: {e}")
                                bot.send_dm(user_id, f"❌ Error retrieving your KRs. Please try again or contact your team lead.")
                        else:
                            bot.send_dm(user_id, f"✅ KR mine request submitted!\n\n*User:* {user_name}\n*Sprint:* {sprint_number}")
                    else:
                        # Regular KR search - trigger mentor check
                        bot.send_mentor_check(
                            user_id=user_id,
                            standup_ts=None,  # No thread for slash commands
                            user_name=user_name,
                            request_type="kr",
                            channel=user_id,
                            search_term=search_term,
                            sprint_number=sprint_number
                        )
            except Exception as e:
                print(f"❌ Error in background KR processing: {e}")
        thread = threading.Thread(target=process_kr_command)
        thread.daemon = True
        thread.start()
        return True
    except Exception as e:
        print(f"❌ Error in KR command handler: {e}")
        return False

def _handle_checkin_command(bot, user_id, channel_id):
    """Handle /checkin command - send standup prompt to DM."""
    try:
        import threading
        def process_checkin_command():
            try:
                # Add a small delay to avoid rate limiting
                time.sleep(1.0)  # Increased delay for free workspace
                # Send standup with error handling
                try:
                    bot.send_standup_to_dm(user_id)
                    print(f"✅ Standup prompt sent successfully to {user_id}")
                except Exception as e:
                    print(f"❌ Error sending standup prompt: {e}")
                    # Don't try to send error message to avoid cascading failures
            except Exception as e:
                print(f"❌ Error in background checkin processing: {e}")
                # Don't try to send error message to avoid cascading failures
        thread = threading.Thread(target=process_checkin_command)
        thread.daemon = True
        thread.start()
        return True
    except Exception as e:
        print(f"❌ Error in checkin command handler: {e}")
        return False

def _handle_blocked_command(bot, user_id, channel_id):
    """Handle /blocked command - report a new blocker."""
    try:
        import threading
        def process_blocked_command():
            try:
                # Add a small delay to avoid rate limiting
                time.sleep(1.0)  # Increased delay for free workspace
                
                # Get user info with error handling
                try:
                    user_info = bot.client.users_info(user=user_id)
                    user_name = user_info['user']['real_name']
                except Exception as e:
                    print(f"❌ Error getting user info: {e}")
                    user_name = f"User {user_id}"
                
                # Send mentor check for blocker reporting
                try:
                    result = bot.send_mentor_check(
                        user_id=user_id,
                        standup_ts=None,
                        user_name=user_name,
                        request_type="blocker",
                        channel=user_id
                    )
                    
                    if result:
                        print(f"✅ Mentor check sent successfully for blocker reporting to {user_name}")
                    else:
                        print(f"❌ Failed to send mentor check for blocker reporting to {user_name}")
                        
                except Exception as e:
                    print(f"❌ Error sending mentor check for blocker reporting: {e}")
                    # Send a simple fallback message
                    bot.send_dm(user_id, "🚨 Need to report a blocker? Please try again or contact your team lead directly.")
                        
            except Exception as e:
                print(f"❌ Error in background blocked processing: {e}")
                # Don't try to send error message to avoid cascading failures
        
        thread = threading.Thread(target=process_blocked_command)
        thread.daemon = True
        thread.start()
        
        return True
    except Exception as e:
        print(f"❌ Error in blocked command handler: {e}")
        return False

def _handle_health_command(bot, user_id, channel_id):
    """Handle /health command - send health check to DM."""
    try:
        import threading
        def process_health_command():
            try:
                # Add a small delay to avoid rate limiting
                time.sleep(1.0)  # Increased delay for free workspace
                # Send health check with error handling
                try:
                    bot.send_health_check_to_dm(user_id)
                    print(f"✅ Health check prompt sent successfully to {user_id}")
                except Exception as e:
                    print(f"❌ Error sending health check prompt: {e}")
                    # Don't try to send error message to avoid cascading failures
            except Exception as e:
                print(f"❌ Error in background health processing: {e}")
                # Don't try to send error message to avoid cascading failures
        thread = threading.Thread(target=process_health_command)
        thread.daemon = True
        thread.start()
        return True
    except Exception as e:
        print(f"❌ Error in health command handler: {e}")
        return False

def _handle_role_command(bot, user_id, text, channel_id):
    """Handle /role command."""
    try:
        import threading
        def process_role_command():
            try:
                # Add a small delay to avoid rate limiting
                time.sleep(1.0)  # Increased delay for free workspace
                
                # Process role command directly to the user's DM
                try:
                    bot._handle_role_command(user_id, text, user_id)  # Send to user's DM
                    print(f"✅ Role command processed successfully to DM")
                except Exception as e:
                    print(f"❌ Error processing role command to DM: {e}")
                    # Don't try to send error message to avoid cascading failures
                    
            except Exception as e:
                print(f"❌ Error in background role processing: {e}")
                # Don't try to send error message to avoid cascading failures
        
        thread = threading.Thread(target=process_role_command)
        thread.daemon = True
        thread.start()
        
        return True
        
    except Exception as e:
        print(f"❌ Error in role command handler: {e}")
        return False

def _handle_rolelist_command(bot, user_id, channel_id):
    """Handle /rolelist command."""
    try:
        import threading
        def process_rolelist():
            try:
                # Add a small delay to avoid rate limiting
                time.sleep(1.0)  # Increased delay for free workspace
                
                # List roles directly to the user's DM
                try:
                    bot._list_all_roles(user_id)  # Send to user's DM
                    print(f"✅ Role list processed successfully to DM")
                except Exception as e:
                    print(f"❌ Error listing roles to DM: {e}")
                    # Don't try to send error message to avoid cascading failures
                    
            except Exception as e:
                print(f"❌ Error in background rolelist processing: {e}")
                # Don't try to send error message to avoid cascading failures
        
        thread = threading.Thread(target=process_rolelist)
        thread.daemon = True
        thread.start()
        
        return True
        
    except Exception as e:
        print(f"❌ Error in rolelist command handler: {e}")
        return False

def _handle_test_standup_command(bot, user_id, channel_id):
    """Handle /test_standup command - manually trigger daily standup."""
    user_name = bot.get_user_name(user_id)
    
    # Check if user has admin role
    if not bot.has_role(user_id, 'admin'):
        bot.send_dm(user_id, f"❌ @{user_name} Only admins can trigger test standups.")
        return False
    
    # Manually trigger the daily standup
    bot.send_standup_to_all_users()
    bot.send_dm(user_id, f"✅ @{user_name} Daily standup triggered manually!")
    return True

def _handle_test_health_command(bot, user_id, channel_id):
    """Handle /test_health command - manually trigger health check."""
    user_name = bot.get_user_name(user_id)
    
    # Check if user has admin role
    if not bot.has_role(user_id, 'admin'):
        bot.send_dm(user_id, f"❌ @{user_name} Only admins can trigger test health checks.")
        return False
    
    # Manually trigger the health check
    bot.send_health_check_to_all_users()
    bot.send_dm(user_id, f"✅ @{user_name} Health check triggered manually!")
    return True

def _handle_blocker_command(bot, user_id, channel_id):
    """Handle /blocker command with sprint number requirement and field memory."""
    try:
        import threading
        
        def process_blocker_command():
            try:
                # Add a small delay to avoid rate limiting
                time.sleep(1.0)
                
                # Get user info with error handling
                try:
                    user_info = bot.client.users_info(user=user_id)
                    user_name = user_info['user']['real_name']
                except Exception as e:
                    print(f"❌ Error getting user info: {e}")
                    user_name = f"User {user_id}"
                
                # Check if user has pending blocker data to continue
                if hasattr(bot, 'blocker_pending_data') and user_id in bot.blocker_pending_data:
                    pending_data = bot.blocker_pending_data[user_id]
                    bot.send_blocker_continue_form(user_id, user_name, pending_data)
                else:
                    # Send the original form asking for sprint number
                    blocks = [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*View Your Blockers*\n\nPlease specify a sprint number to view your blockers:"
                            }
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
                                "action_id": "sprint_number_input",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "e.g., 5"
                                }
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "View Blockers"
                                    },
                                    "action_id": "view_blockers_with_sprint",
                                    "value": user_id
                                }
                            ]
                        }
                    ]
                    
                    bot.send_dm(user_id, "Please specify a sprint number to view your blockers:", blocks=blocks)
                
            except Exception as e:
                print(f"❌ Error in background blocker processing: {e}")
                bot.send_dm(user_id, "❌ Error processing blocker command. Please try again.")
        
        thread = threading.Thread(target=process_blocker_command)
        thread.daemon = True
        thread.start()
        
        return True
    except Exception as e:
        print(f"❌ Error in blocker command handler: {e}")
        return False

def _handle_autorole_command(bot, user_id, text, channel_id):
    """Handle /autorole command - auto-assign roles to users."""
    try:
        import threading
        def process_autorole_command():
            try:
                # Add a small delay to avoid rate limiting
                time.sleep(1.0)
                
                # Get user info with error handling
                try:
                    user_info = bot.client.users_info(user=user_id)
                    user_name = user_info['user']['real_name']
                except Exception as e:
                    print(f"❌ Error getting user info: {e}")
                    user_name = f"User {user_id}"
                
                # Parse command arguments
                parts = text.split() if text else []
                
                if not parts:  # Just /autorole
                    bot.send_dm(user_id, "🔄 Starting auto-role assignment for all users...")
                    bot.auto_assign_roles()
                    bot.send_dm(user_id, "✅ Auto-role assignment completed!")
                    
                elif parts[0].lower() == 'refresh':
                    bot.send_dm(user_id, "🔄 Refreshing all user roles...")
                    bot.refresh_all_roles()
                    bot.send_dm(user_id, "✅ Role refresh completed!")
                    
                elif parts[0].lower() == 'new':
                    bot.send_dm(user_id, "🔄 Assigning roles to new users...")
                    bot.assign_roles_to_new_users()
                    bot.send_dm(user_id, "✅ New user role assignment completed!")
                    
                elif parts[0].lower() == 'user' and len(parts) >= 2:
                    user_mention = parts[1]
                    target_user_id = bot._extract_user_id_from_mention(user_mention)
                    
                    if target_user_id:
                        bot.send_dm(user_id, f"🔄 Auto-assigning roles to {user_mention}...")
                        bot.auto_assign_roles(user_id=target_user_id)
                        bot.send_dm(user_id, f"✅ Auto-role assignment completed for {user_mention}!")
                    else:
                        bot.send_dm(user_id, f"❌ Could not find user: {user_mention}")
                        
                else:
                    # Create autorole help blocks
                    autorole_blocks = [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "🤖 Auto-Role Assignment Help",
                                "emoji": True
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Auto-Role Commands:*"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "• `/autorole` — Auto-assign roles to all users based on their Slack profile\n• `/autorole refresh` — Force refresh all user roles\n• `/autorole new` — Assign roles only to users who don't have any roles\n• `/autorole user @username` — Auto-assign roles to a specific user"
                            }
                        },
                        {
                            "type": "divider"
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": "💡 The bot analyzes job titles, departments, and Slack profile fields to automatically assign appropriate roles\n\n*Note:* Users need job titles in their Slack profiles for accurate role assignment"
                                }
                            ]
                        }
                    ]
                    bot.send_dm(user_id, "Auto-role assignment help:", blocks=autorole_blocks)
                        
            except Exception as e:
                print(f"❌ Error in background autorole processing: {e}")
                bot.send_dm(user_id, "❌ Error processing autorole command. Please try again.")
        
        thread = threading.Thread(target=process_autorole_command)
        thread.daemon = True
        thread.start()
        
        return True
    except Exception as e:
        print(f"❌ Error in autorole command handler: {e}")
        return False

# Removed Flask webhook routes - using Socket Mode instead 