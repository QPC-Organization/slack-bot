
def handle_open_blocker_report_modal(bot, payload):
    """Handle opening the blocker report modal."""
    try:
        print(f"🔍 DEBUG: handle_open_blocker_report_modal called with payload: {payload}")
        
        # Get the correct user ID from the mentor check value in the button
        actions = payload.get('actions', [])
        if actions:
            value = actions[0].get('value', '')
            print(f"🔍 DEBUG: Button value: {value}")
            
            # Parse the value to get the actual user ID
            parts = value.split('_')
            if len(parts) >= 3 and parts[0] == 'checkin' and parts[1] == 'prompt':
                actual_user_id = parts[2]  # The user ID is the 3rd part
                print(f"🔍 DEBUG: Actual user ID from button value: {actual_user_id}")
            elif len(parts) >= 3 and parts[0] == 'blocker' and parts[1] == 'report':
                actual_user_id = parts[2]  # The user ID is the 3rd part
                print(f"🔍 DEBUG: Actual user ID from button value: {actual_user_id}")
            else:
                print(f"❌ DEBUG: Could not parse user ID from button value: {value}")
                return {"response_action": "clear"}
        else:
            print(f"❌ DEBUG: No actions found in payload")
            return {"response_action": "clear"}
        
        user_name = bot.get_user_name(actual_user_id)
        print(f"🔍 DEBUG: Creating blocker form for user: {user_name}")
        
        # Open a modal with the blocker form (same as checkin)
        trigger_id = payload.get('trigger_id')
        if not trigger_id:
            print(f"❌ DEBUG: No trigger_id available for modal")
            # Fallback to sending a simple message
            bot.send_dm(actual_user_id, f"🚨 Blocker Report for @{user_name}\n\nPlease use the `/blocked` command again to open the blocker form.")
            return {"response_action": "clear"}
        
        # Create modal blocks (same structure as checkin)
        modal_blocks = [
            {
                "type": "input",
                "block_id": "sprint_number",
                "label": {"type": "plain_text", "text": "Sprint Number"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "sprint_number_input",
                    "placeholder": {"type": "plain_text", "text": "e.g., 5"}
                }
            },
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
                    "placeholder": {"type": "plain_text", "text": "Any additional context or details..."},
                    "optional": True
                }
            }
        ]
        
        # Open the modal
        success = bot.open_modal(
            trigger_id=trigger_id,
            title=f"Blocker Report for @{user_name}",
            blocks=modal_blocks,
            submit_text="Submit Blocker",
            callback_id="blocker_form_submit",
            private_metadata=actual_user_id
        )
        
        if success:
            print(f"✅ DEBUG: Blocker report modal opened successfully for {user_name}")
        else:
            print(f"❌ DEBUG: Failed to open blocker report modal for {user_name}")
        
        return {"response_action": "clear"}
        
    except Exception as e:
        print(f"❌ Error in open blocker report modal handler: {e}")
        return {"response_action": "clear"}


def handle_open_checkin_modal(bot, payload):
    """Handle opening the checkin modal."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        trigger_id = payload['trigger_id']
        
        print(f"🔍 DEBUG: Opening checkin modal for {user_name}")
        
        # Create modal blocks
        blocks = [
            {
                "type": "input",
                "block_id": "yesterday_work",
                "label": {"type": "plain_text", "text": "What did you work on yesterday?"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "yesterday_input",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "Describe your work from yesterday..."}
                }
            },
            {
                "type": "input",
                "block_id": "today_work",
                "label": {"type": "plain_text", "text": "What will you work on today?"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "today_input",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "Describe your planned work for today..."}
                }
            },
            {
                "type": "input",
                "block_id": "blockers",
                "label": {"type": "plain_text", "text": "Any blockers?"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "blockers_input",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "Describe any blockers or issues..."},
                    "optional": True
                }
            }
        ]
        
        # Open the modal
        success = bot.open_modal(
            trigger_id=trigger_id,
            title="Daily Check-in",
            blocks=blocks,
            submit_text="Submit Check-in",
            callback_id="daily_checkin_submit"
        )
        
        if success:
            print(f"✅ Modal opened successfully for {user_name}")
        else:
            print(f"❌ Failed to open modal for {user_name}")
            
        return {"text": "OK"}
        
    except Exception as e:
        print(f"❌ Error in open checkin modal handler: {e}")
        return {"text": "OK"}

