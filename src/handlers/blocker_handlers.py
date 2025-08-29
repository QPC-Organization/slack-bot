import time
import threading
from datetime import datetime


def handle_blocker_note_edit(bot, payload):
    """Handle blocker note edit button click."""
    try:
        print(f"🔍 DEBUG: handle_blocker_note_edit called with payload: {payload}")
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        blocker_id = payload['actions'][0]['value']
        
        print(f"🔍 DEBUG: Processing blocker note edit - User: {user_name}, Blocker ID: {blocker_id}")
        
        # Check if trigger_id exists (button clicks don't have trigger_id)
        trigger_id = payload.get('trigger_id')
        if not trigger_id:
            print(f"❌ DEBUG: No trigger_id found in payload - cannot open modal")
            # Send a message to the user instead
            bot.send_dm(user_id, "❌ Sorry, I can't open the note editor right now. Please try again later.")
            return {"response_action": "clear"}
        
        # Create modal for editing note
        blocks = [
            {
                "type": "input",
                "block_id": "note_input",
                "label": {"type": "plain_text", "text": "Add or edit note for this blocker:"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "note_text",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "Enter your note..."}
                }
            }
        ]
        
        # Store blocker_id for modal submission
        if not hasattr(bot, 'tracked_blockers'):
            bot.tracked_blockers = {}
        bot.tracked_blockers[user_id] = blocker_id
        
        print(f"🔍 DEBUG: Stored blocker_id {blocker_id} for user {user_id}")
        
        # Open modal
        modal_result = bot.open_modal(
            trigger_id=trigger_id,
            title="Edit Blocker Note",
            blocks=blocks,
            submit_text="Save Note",
            callback_id="blocker_note_submit"
        )
        
        if modal_result:
            print(f"✅ DEBUG: Modal opened successfully for blocker note edit")
        else:
            print(f"❌ DEBUG: Failed to open modal for blocker note edit")
        
        return {"response_action": "clear"}
    except Exception as e:
        print(f"❌ Error handling blocker note edit: {e}")
        import traceback
        traceback.print_exc()
        return {"response_action": "clear"}


def handle_complete_blocker_with_form(bot, payload):
    """Handle blocker completion with form modal."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        blocker_id = payload['actions'][0]['value']
        trigger_id = payload['trigger_id']
        
        print(f"🔍 DEBUG: Opening completion form for blocker: {blocker_id}")
        
        # Create completion form modal
        blocks = [
            {
                "type": "input",
                "block_id": "resolution_notes",
                "label": {"type": "plain_text", "text": "How was this blocker resolved?"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "resolution_notes_input",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "Describe how the blocker was resolved, what steps were taken, etc..."}
                }
            }
        ]
        
        bot.open_modal(
            trigger_id=trigger_id,
            title="Complete Blocker",
            blocks=blocks,
            submit_text="Mark Complete",
            callback_id="blocker_completion_submit",
            private_metadata=blocker_id
        )
        
        return {"response_action": "clear"}
    except Exception as e:
        print(f"❌ Error opening blocker completion form: {e}")
        return {"response_action": "clear"}


def handle_blocker_followup_response(bot, payload):
    """Handle blocker followup response buttons."""
    try:
        action_id = payload['actions'][0]['action_id']
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        value = payload['actions'][0]['value']
        
        print(f"🔍 DEBUG: handle_blocker_followup_response called - Action: {action_id}, Value: {value}")
        
        # Parse value: action_user_id_kr_name
        parts = value.split('_')
        if len(parts) >= 3:
            action_type = parts[0]  # blocker_resolved, blocker_still_blocked, etc.
            target_user_id = parts[1]
            kr_name = '_'.join(parts[2:])  # KR name might contain underscores
            
            print(f"🔍 DEBUG: Action type: {action_type}, Target user: {target_user_id}, KR: {kr_name}")
            
            if action_type == 'blocker_resolved':
                # User resolved their own blocker
                bot.send_dm(target_user_id, f"🎉 Great job resolving your blocker on {kr_name}! Keep up the momentum!")
                
            elif action_type == 'blocker_still_blocked':
                # User is still blocked - escalate to channel
                escalation_channel = bot.config.BLOCKER_ESCALATION_CHANNEL
                if escalation_channel:
                    try:
                        bot.send_message(
                            channel=escalation_channel,
                            text=f"🚨 *Blocker Still Active*\n\n<@{target_user_id}> is still blocked on *{kr_name}* and needs help. Anyone available to assist?",
                            blocks=[
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": f"🚨 *Blocker Still Active*\n\n<@{target_user_id}> is still blocked on *{kr_name}* and needs help. Anyone available to assist?"
                                    }
                                },
                                {
                                    "type": "actions",
                                    "elements": [
                                        {
                                            "type": "button",
                                            "text": {"type": "plain_text", "text": "I can help"},
                                            "action_id": "claim_blocker",
                                            "value": f"claim_{target_user_id}_{kr_name}",
                                            "style": "primary"
                                        },
                                        {
                                            "type": "button",
                                            "text": {"type": "plain_text", "text": "📋 View Details"},
                                            "action_id": "view_details",
                                            "value": f"view_details_{target_user_id}_{kr_name}"
                                        }
                                    ]
                                }
                            ]
                        )
                        print(f"✅ Escalated still-blocked status for {user_name} to {escalation_channel}")
                    except Exception as e:
                        print(f"❌ Error escalating still-blocked status: {e}")
                        bot.send_dm(target_user_id, f"⚠️ There was an error escalating your blocker. Please try again or contact a team lead.")
                
            elif action_type == 'blocker_need_help':
                # User needs immediate help - escalate to channel
                escalation_channel = bot.config.BLOCKER_ESCALATION_CHANNEL
                if escalation_channel:
                    try:
                        bot.send_message(
                            channel=escalation_channel,
                            text=f"🚨 *URGENT: Blocker Needs Help*\n\n<@{target_user_id}> is blocked on *{kr_name}* and needs immediate assistance!",
                            blocks=[
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": f"🚨 *URGENT: Blocker Needs Help*\n\n<@{target_user_id}> is blocked on *{kr_name}* and needs immediate assistance!"
                                    }
                                },
                                {
                                    "type": "actions",
                                    "elements": [
                                        {
                                            "type": "button",
                                            "text": {"type": "plain_text", "text": "I can help"},
                                            "action_id": "claim_blocker",
                                            "value": f"claim_{target_user_id}_{kr_name}",
                                            "style": "danger"
                                        },
                                        {
                                            "type": "button",
                                            "text": {"type": "plain_text", "text": "📋 View Details"},
                                            "action_id": "view_details",
                                            "value": f"view_details_{target_user_id}_{kr_name}"
                                        }
                                    ]
                                }
                            ]
                        )
                        print(f"✅ Escalated urgent blocker for {user_name} to {escalation_channel}")
                    except Exception as e:
                        print(f"❌ Error escalating urgent blocker: {e}")
                        bot.send_dm(target_user_id, f"⚠️ There was an error escalating your blocker. Please try again or contact a team lead.")
                
            elif action_type == 'claim_and_resolve_blocker':
                # Someone claimed and resolved the blocker
                bot.send_dm(target_user_id, f"🎉 Your blocker on {kr_name} has been claimed and resolved! You're unblocked!")
                
            elif action_type == 'blocker_resolved_24hr':
                # Blocker resolved after 24 hours
                bot.send_dm(target_user_id, f"✅ Your blocker on {kr_name} has been resolved! You're back on track!")
                
            elif action_type == 'blocker_reescalate_24hr':
                # Re-escalate after 24 hours
                escalation_channel = bot.config.BLOCKER_ESCALATION_CHANNEL
                if escalation_channel:
                    try:
                        bot.send_message(
                            channel=escalation_channel,
                            text=f"🚨 *Blocker Re-escalated*\n\n<@{target_user_id}> is still blocked on *{kr_name}* after 24 hours and needs help. Anyone can claim this!",
                            blocks=[
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": f"🚨 *Blocker Re-escalated*\n\n<@{target_user_id}> is still blocked on *{kr_name}* after 24 hours and needs help. Anyone can claim this!"
                                    }
                                },
                                {
                                    "type": "actions",
                                    "elements": [
                                        {
                                            "type": "button",
                                            "text": {"type": "plain_text", "text": "Claim"},
                                            "action_id": "claim_blocker",
                                            "value": f"claim_{target_user_id}_{kr_name}",
                                            "style": "primary"
                                        },
                                        {
                                            "type": "button",
                                            "text": {"type": "plain_text", "text": "📋 View Details"},
                                            "action_id": "view_details",
                                            "value": f"view_details_{target_user_id}_{kr_name}"
                                        }
                                    ]
                                }
                            ]
                        )
                        print(f"✅ Re-escalated blocker for {user_name} to {escalation_channel}")
                    except Exception as e:
                        print(f"❌ Error re-escalating blocker: {e}")
                        bot.send_dm(target_user_id, f"⚠️ There was an error re-escalating your blocker. Please try again or contact a team lead.")
        
        return {"text": "OK"}
    except Exception as e:
        print(f"Error handling blocker followup response: {e}")
        return {"text": "Error"}


def handle_claim_blocker(bot, payload):
    """Handle claiming a blocker by a lead."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        value = payload['actions'][0]['value']
        channel_id = payload['channel']['id']
        message_ts = payload['message']['ts']
        
        # Parse value: claim_user_id_kr_name
        parts = value.split('_')
        if len(parts) >= 3:
            action_type = parts[0]  # claim
            blocked_user_id = parts[1]
            kr_name = '_'.join(parts[2:])  # KR name might contain underscores
            
            # For now, use placeholder values since we don't have the full blocker details
            blocker_description = "Blocker details available in Coda"
            blocker_id = f"claimed_{blocked_user_id}_{int(time.time())}"
            
            # Anyone can claim blockers - no role restrictions
            print(f"✅ {user_name} is claiming blocker for {kr_name}")
            
            # Update the message to show it's claimed
            updated_text = f"✅ *Blocker claimed by @{user_name}*\n\n"
            updated_text += f"*User:* <@{blocked_user_id}>\n"
            updated_text += f"*KR:* {kr_name}\n"
            updated_text += f"*Description:* {blocker_description}\n"
            updated_text += f"*Status:* Being addressed by @{user_name}"
            
            blocks = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": updated_text}
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "📋 View Details"},
                            "action_id": "view_details",
                            "value": f"view_details_{user_id}_{kr_name}"
                        }
                    ]
                }
            ]
            
            bot.update_message(channel_id, message_ts, "", blocks=blocks)
            
            # Update active_blockers tracking
            if hasattr(bot, 'active_blockers') and blocker_id in bot.active_blockers:
                bot.active_blockers[blocker_id]['status'] = 'claimed'
                bot.active_blockers[blocker_id]['claimed_by'] = user_id
                bot.active_blockers[blocker_id]['claimed_at'] = time.time()
            
            # Notify the blocked user via DM
            bot.send_dm(blocked_user_id, f"🎉 Your blocker for {kr_name} has been claimed by @{user_name}! They'll help you resolve it.")
            
            return {"text": "OK"}
        return {"text": "Error"}
    except Exception as e:
        print(f"Error handling claim blocker: {e}")
        return {"text": "Error"}


def handle_update_progress(bot, payload):
    """Handle update progress button click."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        trigger_id = payload['trigger_id']
        value = payload['actions'][0]['value']
        
        # Parse value: could be either "blocker_row_id_kr_name" (from /blockers) or old format
        parts = value.split('_')
        
        if parts[0] == 'blocker' and len(parts) >= 3:
            # From /blockers command
            blocker_row_id = parts[1]
            kr_name = '_'.join(parts[2:])  # KR name might contain underscores
            
            # Create progress update modal
            blocks = [
                {
                    "type": "input",
                    "block_id": "progress_input",
                    "label": {"type": "plain_text", "text": "Progress Update"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "progress_text",
                        "multiline": True,
                        "placeholder": {"type": "plain_text", "text": "What progress have you made on this blocker?"}
                    }
                }
            ]
            
            bot.open_modal(
                trigger_id=trigger_id,
                title="Update Blocker Progress",
                blocks=blocks,
                submit_text="Submit Progress",
                callback_id="progress_update_submit",
                private_metadata=f"{blocker_row_id}_{kr_name}"
            )
        else:
            # Legacy format - store blocker info for modal submission
            bot.tracked_blockers[user_id] = value
            
            # Create progress update modal
            blocks = [
                {
                    "type": "input",
                    "block_id": "progress_input",
                    "label": {"type": "plain_text", "text": "Progress Update"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "progress_text",
                        "multiline": True,
                        "placeholder": {"type": "plain_text", "text": "What progress have you made on this blocker?"}
                    }
                }
            ]
            
            bot.open_modal(
                trigger_id=trigger_id,
                title="Update Blocker Progress",
                blocks=blocks,
                submit_text="Submit Progress",
                callback_id="progress_update_submit"
            )
        
        return {"text": "OK"}
    except Exception as e:
        print(f"Error handling update progress: {e}")
        return {"text": "Error"}


def handle_mark_resolved(bot, payload):
    """Handle mark resolved button click."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        value = payload['actions'][0]['value']
        channel_id = payload['channel']['id']
        message_ts = payload['message']['ts']
        
        # Parse value: could be either "blocker_row_id_kr_name" (from /blockers) or "resolve_blocker_id" (from channel)
        parts = value.split('_')
        
        if parts[0] == 'blocker' and len(parts) >= 3:
            # From /blockers command - open resolution form
            blocker_row_id = parts[1]
            kr_name = '_'.join(parts[2:])  # KR name might contain underscores
            
            # Open resolution form modal
            trigger_id = payload['trigger_id']
            blocks = [
                {
                    "type": "input",
                    "block_id": "resolution_notes",
                    "label": {"type": "plain_text", "text": "Resolution Notes"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "resolution_notes_input",
                        "multiline": True,
                        "placeholder": {"type": "plain_text", "text": "How was this blocker resolved?"}
                    }
                }
            ]
            
            bot.open_modal(
                trigger_id=trigger_id,
                title="Resolve Blocker",
                blocks=blocks,
                submit_text="Mark Resolved",
                callback_id="blocker_resolution_submit",
                private_metadata=f"{blocker_row_id}_{kr_name}"
            )
            
        elif parts[0] == 'resolve' and len(parts) >= 2:
            # From channel escalation - open resolution modal
            blocker_id = parts[1]
            
            # Open resolution modal to get resolution notes
            trigger_id = payload['trigger_id']
            blocks = [
                {
                    "type": "input",
                    "block_id": "resolution_notes",
                    "label": {"type": "plain_text", "text": "Resolution Notes"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "resolution_notes_input",
                        "multiline": True,
                        "placeholder": {"type": "plain_text", "text": "How was this blocker resolved? What was the solution?"}
                    }
                }
            ]
            
            bot.open_modal(
                trigger_id=trigger_id,
                title="Resolve Blocker",
                blocks=blocks,
                submit_text="Mark Resolved",
                callback_id="blocker_channel_resolution_submit",
                private_metadata=f"{blocker_id}_{channel_id}_{message_ts}"
            )
        
        return {"text": "OK"}
    except Exception as e:
        print(f"Error handling mark resolved: {e}")
        return {"text": "Error"}


def handle_view_blocker_details(bot, payload):
    """Handle view blocker details button click."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        value = payload['actions'][0]['value']
        channel_id = payload['channel']['id']
        message_ts = payload['message']['ts']
        
        # Parse value: user_id_kr_name
        parts = value.split('_')
        if len(parts) >= 2:
            blocked_user_id = parts[0]
            kr_name = parts[1]
            
            # Call the bot method to view blocker details
            bot.view_blocker_details(f"{blocked_user_id}_{kr_name}", channel_id, message_ts)
        
        return {"text": "OK"}
    except Exception as e:
        print(f"Error handling view blocker details: {e}")
        return {"text": "Error"}


def handle_submit_blocker_details(bot, payload):
    """Handle submit blocker details button click."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        trigger_id = payload['trigger_id']
        
        # Create blocker details modal
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
        
        return {"response_action": "clear"}
    except Exception as e:
        print(f"Error handling submit blocker details: {e}")
        return {"response_action": "clear"}


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
