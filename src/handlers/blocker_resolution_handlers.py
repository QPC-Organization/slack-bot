import threading
from datetime import datetime


def handle_blocker_completion_submission(bot, payload):
    """Handle blocker completion form submission."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']
        
        # Extract the resolution notes
        resolution_notes = values.get('resolution_notes', {}).get('resolution_notes_input', {}).get('value', '')
        
        # Get the blocker ID from the modal's private metadata
        blocker_id = payload['view'].get('private_metadata', '')
        
        if not blocker_id:
            print(f"❌ No blocker ID found in modal metadata")
            bot.send_dm(user_id, "❌ Error: Could not identify which blocker to complete. Please try again.")
            return {"response_action": "clear"}
        
        print(f"🔍 DEBUG: Completing blocker {blocker_id} with resolution: {resolution_notes}")
        
        # Get blocker details from Coda
        if bot.coda:
            blocker_details = bot.coda.get_blocker_by_id(blocker_id)
            if blocker_details:
                kr_name = blocker_details.get('kr_name', 'Unknown KR')
                
                # Mark blocker as complete in Coda
                success = bot.coda.mark_blocker_complete(row_id=blocker_id, resolution_notes=resolution_notes)
                if success:
                    # Update KR status if we have the KR name
                    if kr_name and kr_name != 'Unknown KR':
                        try:
                            bot.coda.resolve_blocker_from_kr(
                                kr_name=kr_name,
                                resolved_by=user_name,
                                resolved_by_id=user_id,
                                resolution_notes=resolution_notes
                            )
                        except Exception as kr_error:
                            print(f"⚠️ Error updating KR status: {kr_error}")
                    
                    # Send completion notification to leads channel
                    try:
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        completion_message = f"🎉 *Blocker Resolved* - @{user_name} has successfully resolved a blocker!"
                        completion_message += f"\n• *KR:* {kr_name}"
                        completion_message += f"\n• *Resolved by:* @{user_name}"
                        completion_message += f"\n• *Resolved at:* {current_time}"
                        completion_message += f"\n• *Resolution notes:* {resolution_notes}"
                        completion_message += f"\n• *Status:* KR status updated to 'Unblocked' in Coda"
                        
                        bot.send_completion_message_to_accessible_channel(completion_message)
                        print(f"✅ Sent completion message to leads channel")
                    except Exception as channel_error:
                        print(f"⚠️ Error sending completion message to channel: {channel_error}")
                    
                    # Send confirmation to user
                    bot.send_dm(user_id, f"✅ Blocker completed successfully!\n\n*Resolution:* {resolution_notes}\n\nThis has been saved to Coda and the KR status updated.")
                else:
                    bot.send_dm(user_id, "❌ Error: Failed to mark blocker as complete in Coda. Please try again.")
            else:
                bot.send_dm(user_id, "❌ Error: Could not find blocker details. Please try again.")
        else:
            bot.send_dm(user_id, f"✅ Blocker completion submitted! Resolution notes: {resolution_notes}")
        
        # Return proper response for Socket Mode
        return {"response_action": "clear"}
    except Exception as e:
        print(f"Error handling blocker completion submission: {e}")
        bot.send_dm(user_id, "❌ Error processing blocker completion. Please try again.")
        return {"response_action": "clear"}


def handle_blocker_resolution_submission(bot, payload):
    """Handle blocker resolution modal submission from /blockers command."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']
        private_metadata = payload['view']['private_metadata']
        
        # Extract form data
        resolution_notes = values.get('resolution_notes', {}).get('resolution_notes_input', {}).get('value', '')
        
        # Parse private_metadata: blocker_row_id_kr_name
        parts = private_metadata.split('_')
        if len(parts) >= 2:
            blocker_row_id = parts[0]
            kr_name = '_'.join(parts[1:])  # KR name might contain underscores
            
            # Send immediate confirmation and close modal
            bot.send_dm(user_id, f"✅ Blocker resolution submitted! Processing in background...")
            
            # Process Coda operations in background to avoid Slack timeout
            def process_blocker_resolution_in_background():
                try:
                    if bot.coda:
                        # Mark blocker as complete
                        success = bot.coda.mark_blocker_complete(
                            row_id=blocker_row_id,
                            resolution_notes=resolution_notes
                        )
                        if success:
                            print(f"✅ Blocker resolution saved to Coda for {user_name}")
                            
                            # Send completion notification to leads channel
                            try:
                                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                
                                completion_message = f"🎉 *Blocker Resolved* - @{user_name} has successfully resolved a blocker!"
                                completion_message += f"\n• *KR:* {kr_name}"
                                completion_message += f"\n• *Resolved by:* @{user_name}"
                                completion_message += f"\n• *Resolution notes:* {resolution_notes}"
                                completion_message += f"\n• *Status:* Blocker marked complete in Coda"
                                
                                bot.send_completion_message_to_accessible_channel(completion_message)
                                print(f"✅ Sent completion message to leads channel")
                            except Exception as channel_error:
                                print(f"⚠️ Error sending completion message to channel: {channel_error}")
                        else:
                            print(f"❌ Failed to save blocker resolution to Coda for {user_name}")
                            bot.send_dm(user_id, "⚠️ Failed to save blocker resolution to Coda")
                        
                        # Update KR status
                        kr_success = bot.coda.resolve_blocker_from_kr(
                            kr_name=kr_name,
                            resolution_notes=resolution_notes
                        )
                        if kr_success:
                            print(f"✅ KR status updated to 'Unblocked' for {kr_name}")
                            bot.send_dm(user_id, "✅ KR status also updated to 'Unblocked'!")
                        else:
                            print(f"⚠️ Failed to update KR status for {kr_name}")
                            bot.send_dm(user_id, "⚠️ Blocker saved but KR status update failed")
                            
                    else:
                        print(f"⚠️ Coda service not available - blocker resolution not saved")
                        bot.send_dm(user_id, "⚠️ Coda service not available - resolution not saved")
                        
                except Exception as e:
                    print(f"❌ Error in background blocker resolution processing: {e}")
                    bot.send_dm(user_id, f"❌ Error processing blocker resolution: {e}")
            
            # Start background processing
            thread = threading.Thread(target=process_blocker_resolution_in_background)
            thread.daemon = True
            thread.start()
            
            # Return proper response for Socket Mode
            return {"response_action": "clear"}
    except Exception as e:
        print(f"Error handling blocker resolution submission: {e}")
        return {"response_action": "clear"}


def handle_blocker_direct_resolution_submission(bot, payload):
    """Handle blocker direct resolution modal submission from channel buttons."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']
        private_metadata = payload['view']['private_metadata']
        
        # Extract form data
        resolution_notes = values.get('resolution_notes', {}).get('resolution_notes_input', {}).get('value', '')
        
        # Parse private_metadata: blocked_user_id_kr_name_resolver_id_channel_id_message_ts
        parts = private_metadata.split('_')
        if len(parts) >= 5:
            blocked_user_id = parts[0]
            kr_name = '_'.join(parts[1:-3])  # KR name might contain underscores
            resolver_id = parts[-3]
            channel_id = parts[-2]
            message_ts = parts[-1]
            
            print(f"🔍 DEBUG: Direct resolution for blocker on {kr_name} by {user_name}")
            
            # Send immediate confirmation
            bot.send_dm(user_id, f"✅ Blocker resolution submitted! Processing in background...")
            
            # Process resolution in background
            def process_direct_resolution_in_background():
                try:
                    # Update the original message to show it's resolved
                    updated_text = f"✅ *Blocker Resolved by @{user_name}*\n\n"
                    updated_text += f"*KR:* {kr_name}\n"
                    updated_text += f"*Resolution:* {resolution_notes}\n"
                    updated_text += f"*Resolved at:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    # Update the message
                    bot.update_message(channel_id, message_ts, updated_text)
                    
                    # Notify the blocked user
                    bot.send_dm(blocked_user_id, f"🎉 Your blocker on {kr_name} has been resolved by @{user_name}!\n\n*Resolution:* {resolution_notes}")
                    
                    print(f"✅ Direct blocker resolution processed for {kr_name}")
                    
                except Exception as e:
                    print(f"❌ Error in background direct resolution processing: {e}")
                    bot.send_dm(user_id, f"❌ Error processing resolution: {e}")
            
            # Start background processing
            thread = threading.Thread(target=process_direct_resolution_in_background)
            thread.daemon = True
            thread.start()
            
            return {"response_action": "clear"}
        else:
            bot.send_dm(user_id, "❌ Error: Invalid blocker information. Please try again.")
            return {"response_action": "clear"}
            
    except Exception as e:
        print(f"Error handling blocker direct resolution submission: {e}")
        return {"response_action": "clear"}


def handle_blocker_channel_resolution_submission(bot, payload):
    """Handle blocker channel resolution modal submission."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']
        private_metadata = payload['view']['private_metadata']
        
        # Extract form data
        resolution_notes = values.get('resolution_notes', {}).get('resolution_notes_input', {}).get('value', '')
        
        # Parse private_metadata: blocker_id_channel_id_message_ts
        parts = private_metadata.split('_')
        if len(parts) >= 3:
            blocker_id = parts[0]
            channel_id = parts[1]
            message_ts = parts[2]
            
            print(f"🔍 DEBUG: Channel resolution for blocker {blocker_id} by {user_name}")
            
            # Send immediate confirmation
            bot.send_dm(user_id, f"✅ Blocker resolution submitted! Processing in background...")
            
            # Process resolution in background
            def process_channel_resolution_in_background():
                try:
                    # Update the original message to show it's resolved
                    updated_text = f"✅ *Blocker Resolved by @{user_name}*\n\n"
                    updated_text += f"*Resolution:* {resolution_notes}\n"
                    updated_text += f"*Resolved at:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    # Update the message
                    bot.update_message(channel_id, message_ts, updated_text)
                    
                    print(f"✅ Channel blocker resolution processed for {blocker_id}")
                    
                except Exception as e:
                    print(f"❌ Error in background channel resolution processing: {e}")
                    bot.send_dm(user_id, f"❌ Error processing resolution: {e}")
            
            # Start background processing
            thread = threading.Thread(target=process_channel_resolution_in_background)
            thread.daemon = True
            thread.start()
            
            return {"response_action": "clear"}
        else:
            bot.send_dm(user_id, "❌ Error: Invalid blocker information. Please try again.")
            return {"response_action": "clear"}
            
    except Exception as e:
        print(f"Error handling blocker channel resolution submission: {e}")
        return {"response_action": "clear"}


def handle_24hr_resolution_submission(bot, payload):
    """Handle 24-hour resolution modal submission."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']
        private_metadata = payload['view']['private_metadata']
        
        # Extract form data
        resolution_notes = values.get('resolution_notes', {}).get('resolution_notes_input', {}).get('value', '')
        
        # Parse private_metadata: blocked_user_id_kr_name
        parts = private_metadata.split('_')
        if len(parts) >= 2:
            blocked_user_id = parts[0]
            kr_name = '_'.join(parts[1:])  # KR name might contain underscores
            
            print(f"🔍 DEBUG: 24hr resolution for blocker on {kr_name} by {user_name}")
            
            # Send immediate confirmation
            bot.send_dm(user_id, f"✅ 24-hour resolution submitted! Processing in background...")
            
            # Process resolution in background
            def process_24hr_resolution_in_background():
                try:
                    # Notify the blocked user
                    bot.send_dm(blocked_user_id, f"✅ Your blocker on {kr_name} has been resolved after 24 hours!\n\n*Resolution:* {resolution_notes}")
                    
                    print(f"✅ 24hr blocker resolution processed for {kr_name}")
                    
                except Exception as e:
                    print(f"❌ Error in background 24hr resolution processing: {e}")
                    bot.send_dm(user_id, f"❌ Error processing resolution: {e}")
            
            # Start background processing
            thread = threading.Thread(target=process_24hr_resolution_in_background)
            thread.daemon = True
            thread.start()
            
            return {"response_action": "clear"}
        else:
            bot.send_dm(user_id, "❌ Error: Invalid blocker information. Please try again.")
            return {"response_action": "clear"}
            
    except Exception as e:
        print(f"Error handling 24hr resolution submission: {e}")
        return {"response_action": "clear"}
