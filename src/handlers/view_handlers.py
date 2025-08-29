import time
from datetime import datetime


def handle_view_details(bot, payload):
    """Handle view details button click - shows comprehensive KR details and replaces reply message."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        value = payload['actions'][0]['value']
        channel_id = payload['channel']['id']
        message_ts = payload['message']['ts']
        
        # Parse value: view_details_user_id_kr_name
        parts = value.split('_')
        if len(parts) >= 3:
            # Format: view_details_user_id_kr_name
            # parts[0] = "view"
            # parts[1] = "details" 
            # parts[2] = "user_id"
            # parts[3:] = KR_NAME_WITH_SPACES
            
            if parts[1] == "details":
                user_id_from_button = parts[2]
                kr_name = '_'.join(parts[3:])  # KR name might contain underscores and spaces
                print(f"🔍 DEBUG: Parsed user_id: {user_id_from_button}, kr_name: {kr_name}")
                
                # For now, we'll use a placeholder blocker_id since we don't have the full blocker details
                blocker_id = f"view_details_{user_id_from_button}_{int(time.time())}"
            else:
                print(f"❌ Unexpected button value format: {value}")
                return {"text": "Error"}
        
        # Get comprehensive KR details from Coda using the same search as /kr command
        kr_matches = bot.coda.search_kr_table(kr_name) if bot.coda else []
        kr_details = None
        kr_blocked_info = None
        kr_progress = bot.get_kr_progress_from_coda(kr_name)
        
        # Use the first match found (same logic as /kr command)
        if kr_matches:
            match = kr_matches[0]  # Use first match
            kr_details = {
                "row_id": match.get("id"),
                "kr_name": match.get("c-yQ1M6UqTSj", ""),
                "owner": match.get("c-efR-vVo_3w", ""),
                "status": match.get("c-cC29Yow8Gr", ""),
                "definition_of_done": match.get("c-P_mQJLObL0", ""),
                "target_date": match.get("c--UuxnDdGq7", ""),
                "progress": match.get("c--I8Kuqx_r3", ""),
                "notes": match.get("c-whRefnNl8_", "")
            }
            # Get blocked info for this specific KR
            kr_blocked_info = bot.coda.get_kr_blocked_info(kr_name) if bot.coda else None
        
        # Create comprehensive details message
        details_text = f"📋 *KR Details for: {kr_name}*\n\n"
        
        # Add note about search results
        if kr_matches:
            details_text += f"*Found in KR database search*\n\n"
        else:
            details_text += f"*⚠️ KR not found in database*\n\n"
        
        # Add KR details if available
        if kr_details:
            details_text += f"*Owner:* {kr_details.get('owner', 'Unknown')}\n"
            details_text += f"*Status:* {kr_details.get('status', 'Unknown')}\n"
            details_text += f"*Definition of Done:* {kr_details.get('definition_of_done', 'Not specified')}\n"
            details_text += f"*Target Date:* {kr_details.get('target_date', 'Not specified')}\n\n"
        
        # Add progress information
        details_text += "*Progress Information:*\n"
        if kr_details and kr_details.get("progress"):
            details_text += f"• *Current Progress:* {kr_details.get('progress')}\n"
        elif kr_progress:
            details_text += f"• *Current Progress:* {kr_progress}\n"
        else:
            details_text += "• *Current Progress:* No progress data available\n"
        
        # Add blocked information if KR is blocked
        if kr_blocked_info and kr_blocked_info.get('is_blocked'):
            details_text += f"\n*🚨 BLOCKED STATUS:*\n"
            details_text += f"• *Blocked At:* {kr_blocked_info.get('blocked_at', 'Unknown')}\n"
            details_text += f"• *Blocked By:* {kr_blocked_info.get('blocked_by', 'Unknown')}\n"
            details_text += f"• *Blocker Context:* {kr_blocked_info.get('blocker_context', 'No context provided')}\n"
        
        # Add blocker context if available
        if hasattr(bot, 'active_blockers') and blocker_id in bot.active_blockers:
            blocker_info = bot.active_blockers[blocker_id]
            details_text += f"\n*Current Blocker Info:*\n"
            details_text += f"• *Status:* {blocker_info.get('status', 'Unknown')}\n"
            if blocker_info.get('claimed_by'):
                claimed_by_name = bot.get_user_name(blocker_info['claimed_by'])
                details_text += f"• *Claimed by:* @{claimed_by_name}\n"
            details_text += f"• *Urgency:* {blocker_info.get('urgency', 'Unknown')}\n"
            details_text += f"• *Notes:* {blocker_info.get('notes', 'None')}\n"
        
        # Check if we have a stored reply timestamp for this blocker
        reply_ts = None
        
        # Initialize active_blockers if it doesn't exist
        if not hasattr(bot, 'active_blockers'):
            bot.active_blockers = {}
        
        # Create a more persistent key for message replacement using KR name and channel
        # This prevents spam even when bot restarts
        message_key = f"{kr_name}_{channel_id}"
        print(f"🔍 DEBUG: Using message key '{message_key}' for KR '{kr_name}' in channel '{channel_id}'")
        print(f"🔍 DEBUG: active_blockers keys: {list(bot.active_blockers.keys()) if hasattr(bot, 'active_blockers') else 'None'}")
        
        # Check if we have a stored reply timestamp for this KR in this channel
        if message_key in bot.active_blockers:
            blocker_info = bot.active_blockers[message_key]
            reply_ts = blocker_info.get('details_reply_ts')
            print(f"🔍 DEBUG: Found existing message info, details_reply_ts: {reply_ts}")
        else:
            print(f"🔍 DEBUG: Message key '{message_key}' not found - creating entry to prevent spam")
            # Create a new entry for this KR/channel combination to prevent future spam
            bot.active_blockers[message_key] = {
                'kr_name': kr_name,
                'channel_id': channel_id,
                'details_reply_ts': None,
                'created_at': datetime.now()
            }
        
        if reply_ts:
            # Try to update the existing reply message
            try:
                bot.update_message(channel_id, reply_ts, details_text)
                print(f"✅ Updated existing details message for KR '{kr_name}' (reply_ts: {reply_ts})")
                return {"text": "OK"}
            except Exception as update_error:
                print(f"⚠️ Error updating existing message: {update_error}")
                # If update fails, we'll send a new message below
        
        # Send a new reply and store its timestamp
        try:
            response = bot.send_message(channel_id, details_text, thread_ts=message_ts)
            if response and message_key in bot.active_blockers:
                # Store the reply timestamp for future updates
                bot.active_blockers[message_key]['details_reply_ts'] = response['ts']
                print(f"✅ Sent new details message for KR '{kr_name}' and stored reply_ts: {response['ts']}")
            else:
                print(f"✅ Sent new details message for KR '{kr_name}'")
        except Exception as send_error:
            print(f"❌ Error sending details message: {send_error}")
    
        return {"text": "OK"}
    except Exception as e:
        print(f"Error handling view details: {e}")
        return {"text": "Error"}


def handle_view_all_blockers(bot, payload):
    """Handle view all blockers button click."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        value = payload['actions'][0]['value']
        
        # Parse value: view_all_blockers_user_id
        parts = value.split('_')
        if len(parts) >= 3:
            target_user_id = parts[2]
            print(f"🔍 DEBUG: Viewing all blockers for user: {target_user_id}")
            
            # Get all blockers for this user
            user_blockers = []
            if hasattr(bot, 'active_blockers'):
                for blocker_id, blocker_info in bot.active_blockers.items():
                    if blocker_info.get('user_id') == target_user_id:
                        user_blockers.append(blocker_info)
            
            if user_blockers:
                # Create blockers list message
                blockers_text = f"📋 *All Blockers for @{bot.get_user_name(target_user_id)}*\n\n"
                
                for i, blocker in enumerate(user_blockers, 1):
                    blockers_text += f"*{i}. {blocker.get('kr_name', 'Unknown KR')}*\n"
                    blockers_text += f"   Status: {blocker.get('status', 'Unknown')}\n"
                    blockers_text += f"   Urgency: {blocker.get('urgency', 'Unknown')}\n"
                    if blocker.get('notes'):
                        blockers_text += f"   Notes: {blocker.get('notes')}\n"
                    blockers_text += "\n"
                
                # Send as DM to the requesting user
                bot.send_dm(user_id, blockers_text)
            else:
                bot.send_dm(user_id, f"✅ No active blockers found for @{bot.get_user_name(target_user_id)}")
        else:
            bot.send_dm(user_id, "❌ Error: Invalid button value format")
        
        return {"text": "OK"}
    except Exception as e:
        print(f"Error handling view all blockers: {e}")
        return {"text": "Error"}


def handle_view_blockers_with_sprint(bot, payload):
    """Handle view blockers with sprint button click."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        value = payload['actions'][0]['value']
        
        # Parse value: view_blockers_sprint_user_id_sprint_number
        parts = value.split('_')
        if len(parts) >= 4:
            target_user_id = parts[2]
            sprint_number = parts[3]
            print(f"🔍 DEBUG: Viewing blockers for user: {target_user_id} in sprint: {sprint_number}")
            
            # Get blockers for this user in this sprint
            sprint_blockers = []
            if hasattr(bot, 'active_blockers'):
                for blocker_id, blocker_info in bot.active_blockers.items():
                    if (blocker_info.get('user_id') == target_user_id and 
                        blocker_info.get('sprint_number') == sprint_number):
                        sprint_blockers.append(blocker_info)
            
            if sprint_blockers:
                # Create sprint blockers list message
                blockers_text = f"📋 *Blockers for @{bot.get_user_name(target_user_id)} in Sprint {sprint_number}*\n\n"
                
                for i, blocker in enumerate(sprint_blockers, 1):
                    blockers_text += f"*{i}. {blocker.get('kr_name', 'Unknown KR')}*\n"
                    blockers_text += f"   Status: {blocker.get('status', 'Unknown')}\n"
                    blockers_text += f"   Urgency: {blocker.get('urgency', 'Unknown')}\n"
                    if blocker.get('notes'):
                        blockers_text += f"   Notes: {blocker.get('notes')}\n"
                    blockers_text += "\n"
                
                # Send as DM to the requesting user
                bot.send_dm(user_id, blockers_text)
            else:
                bot.send_dm(user_id, f"✅ No blockers found for @{bot.get_user_name(target_user_id)} in Sprint {sprint_number}")
        else:
            bot.send_dm(user_id, "❌ Error: Invalid button value format")
        
        return {"text": "OK"}
    except Exception as e:
        print(f"Error handling view blockers with sprint: {e}")
        return {"text": "Error"}


def handle_view_blockers_modal(bot, payload):
    """Handle view blockers modal submission."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']
        
        # Extract form data
        target_user = values.get('target_user', {}).get('target_user_input', {}).get('selected_user', '')
        sprint_filter = values.get('sprint_filter', {}).get('sprint_filter_input', {}).get('selected_option', {}).get('value', '')
        
        if not target_user:
            bot.send_dm(user_id, "❌ Target user is required. Please try again.")
            return {"response_action": "clear"}
        
        # Get blockers for the target user
        user_blockers = []
        if hasattr(bot, 'active_blockers'):
            for blocker_id, blocker_info in bot.active_blockers.items():
                if blocker_info.get('user_id') == target_user:
                    # Apply sprint filter if specified
                    if sprint_filter and sprint_filter != 'all':
                        if blocker_info.get('sprint_number') == sprint_filter:
                            user_blockers.append(blocker_info)
                    else:
                        user_blockers.append(blocker_info)
        
        if user_blockers:
            # Create blockers list message
            blockers_text = f"📋 *Blockers for @{bot.get_user_name(target_user)}*\n"
            if sprint_filter and sprint_filter != 'all':
                blockers_text += f"*Sprint Filter: {sprint_filter}*\n"
            blockers_text += "\n"
            
            for i, blocker in enumerate(user_blockers, 1):
                blockers_text += f"*{i}. {blocker.get('kr_name', 'Unknown KR')}*\n"
                blockers_text += f"   Status: {blocker.get('status', 'Unknown')}\n"
                blockers_text += f"   Urgency: {blocker.get('urgency', 'Unknown')}\n"
                if blocker.get('sprint_number'):
                    blockers_text += f"   Sprint: {blocker.get('sprint_number')}\n"
                if blocker.get('notes'):
                    blockers_text += f"   Notes: {blocker.get('notes')}\n"
                blockers_text += "\n"
            
            # Send as DM to the requesting user
            bot.send_dm(user_id, blockers_text)
        else:
            filter_text = f" in Sprint {sprint_filter}" if sprint_filter and sprint_filter != 'all' else ""
            bot.send_dm(user_id, f"✅ No blockers found for @{bot.get_user_name(target_user)}{filter_text}")
        
        return {"response_action": "clear"}
    except Exception as e:
        print(f"Error handling view blockers modal: {e}")
        return {"response_action": "clear"}
