def handle_open_blocker_modal_channel(bot, payload):
    """Handle opening blocker modal from channel buttons."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        value = payload['actions'][0]['value']
        trigger_id = payload['trigger_id']
        
        # Parse value: open_blocker_modal_user_id_kr_name
        parts = value.split('_')
        if len(parts) >= 4:
            target_user_id = parts[2]
            kr_name = '_'.join(parts[3:])  # KR name might contain underscores
            
            print(f"🔍 DEBUG: Opening blocker modal for {kr_name} by {user_name}")
            
            # Create modal blocks for blocker form
            modal_blocks = [
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
                title=f"Report Blocker for {kr_name}",
                blocks=modal_blocks,
                submit_text="Submit Blocker",
                callback_id="blocker_form_submit",
                private_metadata=f"blocker_modal_{target_user_id}_{kr_name}"
            )
            
            if success:
                print(f"✅ Blocker modal opened successfully for {kr_name}")
            else:
                print(f"❌ Failed to open blocker modal for {kr_name}")
        else:
            print(f"❌ Error: Invalid button value format: {value}")
        
        return {"text": "OK"}
    except Exception as e:
        print(f"Error opening blocker modal: {e}")
        return {"text": "Error"}


def handle_open_blocker_sprint_modal(bot, payload):
    """Handle opening blocker sprint modal."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        value = payload['actions'][0]['value']
        trigger_id = payload['trigger_id']
        
        # Parse value: open_sprint_modal_user_id_kr_name
        parts = value.split('_')
        if len(parts) >= 4:
            target_user_id = parts[2]
            kr_name = '_'.join(parts[3:])  # KR name might contain underscores
            
            print(f"🔍 DEBUG: Opening sprint modal for {kr_name} by {user_name}")
            
            # Create modal blocks for sprint selection
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
                }
            ]
            
            # Open the modal
            success = bot.open_modal(
                trigger_id=trigger_id,
                title=f"Report Blocker for {kr_name}",
                blocks=modal_blocks,
                submit_text="Submit Blocker",
                callback_id="blocker_sprint_modal_submission",
                private_metadata=f"blocker_sprint_{target_user_id}_{kr_name}"
            )
            
            if success:
                print(f"✅ Sprint modal opened successfully for {kr_name}")
            else:
                print(f"❌ Failed to open sprint modal for {kr_name}")
        else:
            print(f"❌ Error: Invalid button value format: {value}")
        
        return {"text": "OK"}
    except Exception as e:
        print(f"Error opening sprint modal: {e}")
        return {"text": "Error"}


def handle_open_blocker_continue_modal(bot, payload):
    """Handle opening blocker continue modal."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        value = payload['actions'][0]['value']
        trigger_id = payload['trigger_id']
        
        # Parse value: open_continue_modal_user_id_kr_name
        parts = value.split('_')
        if len(parts) >= 4:
            target_user_id = parts[2]
            kr_name = '_'.join(parts[3:])  # KR name might contain underscores
            
            print(f"🔍 DEBUG: Opening continue modal for {kr_name} by {user_name}")
            
            # Create modal blocks for blocker continuation
            modal_blocks = [
                {
                    "type": "input",
                    "block_id": "progress_update",
                    "label": {"type": "plain_text", "text": "Progress Update"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "progress_update_input",
                        "multiline": True,
                        "placeholder": {"type": "plain_text", "text": "What progress have you made?..."}
                    }
                },
                {
                    "type": "input",
                    "block_id": "next_steps",
                    "label": {"type": "plain_text", "text": "Next Steps"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "next_steps_input",
                        "multiline": True,
                        "placeholder": {"type": "plain_text", "text": "What are your next steps?..."}
                    }
                }
            ]
            
            # Open the modal
            success = bot.open_modal(
                trigger_id=trigger_id,
                title=f"Continue Blocker for {kr_name}",
                blocks=modal_blocks,
                submit_text="Submit Update",
                callback_id="blocker_continue_submit",
                private_metadata=f"blocker_continue_{target_user_id}_{kr_name}"
            )
            
            if success:
                print(f"✅ Continue modal opened successfully for {kr_name}")
            else:
                print(f"❌ Failed to open continue modal for {kr_name}")
        else:
            print(f"❌ Error: Invalid button value format: {value}")
        
        return {"text": "OK"}
    except Exception as e:
        print(f"Error opening continue modal: {e}")
        return {"text": "Error"}


def handle_open_view_blockers_modal(bot, payload):
    """Handle opening view blockers modal."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        trigger_id = payload['trigger_id']
        
        print(f"🔍 DEBUG: Opening view blockers modal for {user_name}")
        
        # Create modal blocks for viewing blockers
        modal_blocks = [
            {
                "type": "input",
                "block_id": "target_user",
                "label": {"type": "plain_text", "text": "Target User"},
                "element": {
                    "type": "users_select",
                    "action_id": "target_user_input",
                    "placeholder": {"type": "plain_text", "text": "Select user to view blockers for"}
                }
            },
            {
                "type": "input",
                "block_id": "sprint_filter",
                "label": {"type": "plain_text", "text": "Sprint Filter (Optional)"},
                "element": {
                    "type": "static_select",
                    "action_id": "sprint_filter_input",
                    "placeholder": {"type": "plain_text", "text": "Select sprint to filter by"},
                    "options": [
                        {"text": {"type": "plain_text", "text": "All Sprints"}, "value": "all"},
                        {"text": {"type": "plain_text", "text": "Sprint 1"}, "value": "1"},
                        {"text": {"type": "plain_text", "text": "Sprint 2"}, "value": "2"},
                        {"text": {"type": "plain_text", "text": "Sprint 3"}, "value": "3"},
                        {"text": {"type": "plain_text", "text": "Sprint 4"}, "value": "4"},
                        {"text": {"type": "plain_text", "text": "Sprint 5"}, "value": "5"}
                    ]
                }
            }
        ]
        
        # Open the modal
        success = bot.open_modal(
            trigger_id=trigger_id,
            title="View Blockers",
            blocks=modal_blocks,
            submit_text="View Blockers",
            callback_id="view_blockers_modal"
        )
        
        if success:
            print(f"✅ View blockers modal opened successfully for {user_name}")
        else:
            print(f"❌ Failed to open view blockers modal for {user_name}")
        
        return {"text": "OK"}
    except Exception as e:
        print(f"Error opening view blockers modal: {e}")
        return {"text": "Error"}
