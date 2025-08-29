import threading
import time


def handle_blocker_details_submission(bot, payload):
    """Handle blocker details modal submission from the blocker report form."""
    print(f"🔍 DEBUG: handle_blocker_details_submission called")
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']
        
        # Extract form data
        sprint_number = values.get('sprint_number', {}).get('sprint_number_input', {}).get('value', '').strip()
        blocker_description = values.get('blocker_description', {}).get('blocker_description_input', {}).get('value', '').strip()
        kr_name = values.get('kr_name', {}).get('kr_name_input', {}).get('value', '').strip()
        urgency = values.get('urgency', {}).get('urgency_input', {}).get('selected_option', {}).get('value', 'medium')
        notes = values.get('notes', {}).get('notes_input', {}).get('value', '').strip()
        
        print(f"🔍 DEBUG: Extracted blocker details - Sprint: {sprint_number}, Description: {blocker_description}, KR: {kr_name}, Urgency: {urgency}, Notes: {notes}")
        
        # Validate required fields
        if not blocker_description:
            bot.send_dm(user_id, "❌ Blocker description is required. Please try again.")
            return {"response_action": "clear"}
        
        if not kr_name:
            bot.send_dm(user_id, "❌ KR name is required. Please try again.")
            return {"response_action": "clear"}
        
        # Check for duplicate submission (placeholder - implement track_submission function)
        # data_hash = f"{blocker_description[:50]}_{kr_name[:50]}_{urgency}"
        # if not track_submission(user_id, "blocker_details_submission", data_hash):
        #     bot.send_dm(user_id, "⚠️ This blocker submission was already processed. Please wait a moment before trying again.")
        #     return {"response_action": "clear"}
        
        # Send immediate confirmation to user
        bot.send_dm(user_id, f"✅ Blocker submitted! Processing in background...")
        
        # Run escalation in background thread to avoid blocking the form
        def escalate_in_background():
            try:
                # Convert sprint number to integer if provided
                sprint_int = None
                if sprint_number:
                    try:
                        sprint_int = int(sprint_number)
                    except ValueError:
                        print(f"⚠️ Invalid sprint number: {sprint_number}")
                
                # Call the escalation method without sprint number to avoid Coda column issues
                bot.escalate_blocker_with_details(user_id, user_name, blocker_description, kr_name, urgency, notes)
                bot.send_dm(user_id, f"✅ Blocker processed and escalated! Your team will be notified.")
                print(f"✅ Blocker submitted successfully by {user_name}")
            except Exception as escalation_error:
                print(f"❌ Error escalating blocker: {escalation_error}")
                bot.send_dm(user_id, "❌ Sorry, there was an error processing your blocker. Please try again or contact support.")
        
        # Start background thread
        background_thread = threading.Thread(target=escalate_in_background)
        background_thread.daemon = True
        background_thread.start()
        
        return {"response_action": "clear"}
        
    except Exception as e:
        print(f"❌ Error handling blocker details submission: {e}")
        try:
            user_id = payload.get('user', {}).get('id') if payload else None
            if user_id:
                bot.send_dm(user_id, "❌ Sorry, there was an error processing your blocker submission. Please try again.")
        except:
            pass
        
        return {"response_action": "clear"}


def handle_blocker_note_submission(bot, payload):
    """Handle blocker note modal submission with comprehensive error handling."""
    try:
        # Validate payload structure (placeholder - implement validation)
        # required_fields = ['user', 'view']
        # is_valid, missing_fields = input_validator.validate_payload_structure(payload, required_fields)
        # if not is_valid:
        #     return error_handler.handle_validation_error(
        #         ValueError(f"Missing required fields: {missing_fields}"),
        #         "handle_blocker_note_submission",
        #         additional_data={'missing_fields': missing_fields}
        #     )
        
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']
        
        # Validate user ID
        if not user_id:
            print(f"❌ Missing user ID in blocker note submission")
            return {"response_action": "clear"}
        
        # Extract note text
        note_input = values.get('note_input', {}).get('note_text', {})
        note_text = note_input.get('value', '').strip() if note_input else ''
        
        if not note_text:
            bot.send_dm(user_id, "❌ Note text is required. Please try again.")
            return {"response_action": "clear"}
        
        # Get the blocker ID from tracked_blockers
        blocker_id = bot.tracked_blockers.get(user_id)
        if not blocker_id:
            bot.send_dm(user_id, "❌ No blocker found for note editing. Please try again.")
            return {"response_action": "clear"}
        
        print(f"🔍 DEBUG: Adding note to blocker {blocker_id} for user {user_name}: {note_text[:50]}...")
        
        # Add note to blocker in background
        def add_note_in_background():
            try:
                # Update the blocker with the note
                if hasattr(bot, 'active_blockers') and blocker_id in bot.active_blockers:
                    bot.active_blockers[blocker_id]['notes'] = note_text
                    bot.active_blockers[blocker_id]['updated_at'] = time.time()
                    print(f"✅ Note added to blocker {blocker_id}")
                
                # Send confirmation
                bot.send_dm(user_id, f"✅ Note added to blocker: {note_text[:100]}{'...' if len(note_text) > 100 else ''}")
                
            except Exception as note_error:
                print(f"❌ Error adding note to blocker: {note_error}")
                bot.send_dm(user_id, "❌ Error adding note. Please try again.")
        
        # Start background thread
        thread = threading.Thread(target=add_note_in_background)
        thread.daemon = True
        thread.start()
        
        # Clear tracked blocker
        if user_id in bot.tracked_blockers:
            del bot.tracked_blockers[user_id]
        
        return {"response_action": "clear"}
        
    except Exception as e:
        print(f"❌ Error handling blocker note submission: {e}")
        return {"response_action": "clear"}


def handle_progress_update_submission(bot, payload):
    """Handle progress update modal submission."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']
        
        # Extract progress text
        progress_input = values.get('progress_input', {}).get('progress_text', {})
        progress_text = progress_input.get('value', '').strip() if progress_input else ''
        
        if not progress_text:
            bot.send_dm(user_id, "❌ Progress update is required. Please try again.")
            return {"response_action": "clear"}
        
        # Get the blocker info from private_metadata or tracked_blockers
        private_metadata = payload['view'].get('private_metadata', '')
        if private_metadata:
            # New format: blocker_row_id_kr_name
            parts = private_metadata.split('_')
            if parts[0] == 'blocker' and len(parts) >= 3:
                blocker_row_id = parts[1]
                kr_name = '_'.join(parts[2:])
                print(f"🔍 DEBUG: Progress update for blocker {blocker_row_id} on KR {kr_name}")
            else:
                print(f"🔍 DEBUG: Progress update with metadata: {private_metadata}")
        else:
            # Legacy format - get from tracked_blockers
            blocker_info = bot.tracked_blockers.get(user_id, '')
            print(f"🔍 DEBUG: Progress update for tracked blocker: {blocker_info}")
        
        print(f"🔍 DEBUG: Progress update from {user_name}: {progress_text[:50]}...")
        
        # Send confirmation
        bot.send_dm(user_id, f"✅ Progress update recorded: {progress_text[:100]}{'...' if len(progress_text) > 100 else ''}")
        
        # Clear tracked blocker if using legacy format
        if not private_metadata and user_id in bot.tracked_blockers:
            del bot.tracked_blockers[user_id]
        
        return {"response_action": "clear"}
        
    except Exception as e:
        print(f"❌ Error handling progress update submission: {e}")
        return {"response_action": "clear"}


def handle_checkin_submission(bot, payload):
    """Handle daily checkin modal submission."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']
        
        # Extract form data
        yesterday = values.get('yesterday_work', {}).get('yesterday_input', {}).get('value', '')
        today = values.get('today_work', {}).get('today_input', {}).get('value', '')
        blockers = values.get('blockers', {}).get('blockers_input', {}).get('value', '')
        
        # Save to Coda
        if bot.coda:
            try:
                # Combine the responses into a single text
                response_text = f"Yesterday: {yesterday}\nToday: {today}\nBlockers: {blockers}"
                success = bot.coda.add_standup_response(
                    user_id=user_id,
                    response_text=response_text,
                    username=user_name
                )
                if success:
                    print(f"✅ Daily checkin response saved to Coda for {user_name}")
                else:
                    print(f"❌ Failed to save daily checkin response to Coda for {user_name}")
            except Exception as e:
                print(f"❌ Error saving daily checkin response to Coda: {e}")
        else:
            print(f"⚠️ Coda service not available - daily checkin response not saved")
        
        # Send confirmation as DM
        response_text = f"✅ @{user_name} Daily check-in submitted!\n\n"
        response_text += f"*Yesterday:* {yesterday}\n"
        response_text += f"*Today:* {today}\n"
        if blockers:
            response_text += f"*Blockers:* {blockers}"
        
        # Send as DM
        bot.send_dm(user_id, response_text)
        
        # Return proper response for Socket Mode
        return {"response_action": "clear"}
    except Exception as e:
        print(f"Error handling daily checkin submission: {e}")
        return {"response_action": "clear"}


def handle_daily_checkin_submission(bot, payload):
    """Handle daily checkin modal submission."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']
        
        # Extract form data
        yesterday = values.get('yesterday_work', {}).get('yesterday_input', {}).get('value', '')
        today = values.get('today_work', {}).get('today_input', {}).get('value', '')
        blockers = values.get('blockers', {}).get('blockers_input', {}).get('value', '')
        
        # Save to Coda
        if bot.coda:
            try:
                # Combine the responses into a single text
                response_text = f"Yesterday: {yesterday}\nToday: {today}\nBlockers: {blockers}"
                success = bot.coda.add_standup_response(
                    user_id=user_id,
                    response_text=response_text,
                    username=user_name
                )
                if success:
                    print(f"✅ Daily checkin response saved to Coda for {user_name}")
                else:
                    print(f"❌ Failed to save daily checkin response to Coda for {user_name}")
            except Exception as e:
                print(f"❌ Error saving daily checkin response to Coda: {e}")
        else:
            print(f"⚠️ Coda service not available - daily checkin response not saved")
        
        # Send confirmation as DM
        response_text = f"✅ @{user_name} Daily check-in submitted!\n\n"
        response_text += f"*Yesterday:* {yesterday}\n"
        response_text += f"*Today:* {today}\n"
        if blockers:
            response_text += f"*Blockers:* {blockers}"
        
        # Send as DM
        bot.send_dm(user_id, response_text)
        
        # Return proper response for Socket Mode
        return {"response_action": "clear"}
    except Exception as e:
        print(f"Error handling daily checkin submission: {e}")
        return {"response_action": "clear"}
