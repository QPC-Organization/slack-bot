import threading


def handle_open_kr_continue_modal(bot, payload):
    """Handle 'Continue KR' button click - open full KR modal with pre-filled data."""
    try:
        trigger_id = payload.get('trigger_id')
        if not trigger_id:
            print(f"❌ DEBUG: No trigger_id found in payload")
            return {"text": "OK"}
        
        user_id = payload.get('user', {}).get('id')
        if not user_id:
            print(f"❌ DEBUG: No user_id found in payload")
            return {"text": "OK"}
        
        # Get the pending KR data for this user
        pending_data = bot.pending_kr_search.get(user_id, {})
        
        if not pending_data:
            bot.send_dm(user_id, "No pending KR data found. Please start a new KR request.")
            return {"text": "OK"}
        
        # Create the full KR modal with pre-filled data
        blocks = [
            {
                "type": "input",
                "block_id": "search_term",
                "label": {
                    "type": "plain_text",
                    "text": "Search Term"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "search_term",
                    "initial_value": pending_data.get("search_term", ""),
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter search term for KR"
                    }
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
                    "action_id": "sprint_number",
                    "initial_value": str(pending_data.get("sprint_number", "")),
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter sprint number"
                    }
                }
            }
        ]
        
        # Open the full KR modal
        success = bot.open_modal(
            trigger_id=trigger_id,
            title="Continue KR Entry",
            blocks=blocks,
            submit_text="Submit",
            callback_id="kr_continue_submit"
        )
        
        if success:
            print(f"✅ DEBUG: KR continue modal opened successfully with pre-filled data")
        else:
            print(f"❌ DEBUG: Failed to open KR continue modal")
        
        return {"text": "OK"}
        
    except Exception as e:
        print(f"❌ Error in open kr continue modal handler: {e}")
        return {"text": "OK"}


def handle_kr_continue_submit(bot, payload):
    """Handle KR continue submit form submission."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']
        
        # Extract form data
        search_term = values.get('search_term', {}).get('search_term', {}).get('value', '').strip()
        sprint_number = values.get('sprint_number', {}).get('sprint_number', {}).get('value', '').strip()
        
        print(f"🔍 DEBUG: KR continue submit - search_term: '{search_term}', sprint_number: '{sprint_number}'")
        
        # Validate required fields
        if not search_term:
            bot.send_dm(user_id, "❌ Search term is required. Please try again.")
            return {"response_action": "clear"}
        
        if not sprint_number:
            bot.send_dm(user_id, "❌ Sprint number is required. Please try again.")
            return {"response_action": "clear"}
        
        # Clear pending data since we're processing the complete form
        bot.clear_pending_data(user_id, 'kr')
        
        # Send immediate confirmation and close modal
        bot.send_dm(user_id, f"✅ KR search submitted! Processing in background...")
        
        # Process KR search in background to avoid Slack timeout
        def process_kr_search_in_background():
            try:
                # Search for KR in Coda
                if bot.coda:
                    search_results = bot.coda.search_kr_table(search_term)
                    
                    if search_results:
                        # Format and send results
                        result_text = f"✅ *KR found for Sprint {sprint_number}!*\n\n"
                        for result in search_results[:5]:  # Limit to 5 results
                            result_text += f"• *{result.get('name', 'Unknown')}*\n"
                            if result.get('owner'):
                                result_text += f"  Owner: {result['owner']}\n"
                            if result.get('status'):
                                result_text += f"  Status: {result['status']}\n"
                            result_text += "\n"
                        
                        bot.send_dm(user_id, result_text)
                    else:
                        bot.send_dm(user_id, f"❌ No KR found matching '{search_term}' in Sprint {sprint_number}. Please check your search term and sprint number.")
                else:
                    bot.send_dm(user_id, f"✅ KR request submitted!\n\n*Search Term:* {search_term}\n*Sprint:* {sprint_number}")
                    
            except Exception as e:
                print(f"❌ Error processing KR request: {e}")
                bot.send_dm(user_id, "❌ Error processing KR request. Please try again.")
        
        # Start background processing
        thread = threading.Thread(target=process_kr_search_in_background)
        thread.daemon = True
        thread.start()
        
        # Return proper response for Socket Mode
        return {"response_action": "clear"}
        
    except Exception as e:
        print(f"Error handling KR continue submit: {e}")
        bot.send_dm(user_id, "❌ Error processing KR continue. Please try again.")
        return {"response_action": "clear"}
