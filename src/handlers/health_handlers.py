import threading


def handle_health_response(bot, payload):
    """Handle health check button responses with background processing."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        action_id = payload['actions'][0]['action_id']

        mood_map = {
            'great': '😊 Great',
            'okay': '😐 Okay',
            'not_great': '😕 Not great'
        }
        mood = mood_map.get(action_id, 'Unknown')

        if not hasattr(bot, 'health_responses'):
            bot.health_responses = {}
        bot.health_responses[user_id] = mood

        bot.send_dm(user_id, "✅ Health check response received! Processing in background...")

        def process_health_check_in_background():
            try:
                if bot.coda:
                    try:
                        success = bot.coda.save_health_check(user_id, user_name, mood, "", False)
                        if success:
                            bot.send_dm(user_id, "✅ Your health check has been saved to Coda!")
                    except Exception as e:
                        print(f"❌ Error storing health check in Health_Check table: {e}")
            except Exception as e:
                print(f"Error in background health check processing: {e}")
                bot.send_dm(user_id, "❌ Sorry, there was an error processing your health check. Please try again.")

        background_thread = threading.Thread(target=process_health_check_in_background)
        background_thread.daemon = True
        background_thread.start()

        followup_blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Thanks for your response! Would you like to share anything with the team?"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Public Share", "emoji": True},
                        "value": f"public_{action_id}",
                        "action_id": "health_share_public",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Private Share", "emoji": True},
                        "value": f"private_{action_id}",
                        "action_id": "health_share_private"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "No Thanks", "emoji": True},
                        "value": f"no_share_{action_id}",
                        "action_id": "health_no_share"
                    }
                ]
            }
        ]

        bot.send_dm(user_id, "Thanks for your response! Would you like to share anything with the team?", blocks=followup_blocks)
        return {"response_action": "clear"}
    except Exception as e:
        print(f"❌ Error in handle_health_response: {e}")
        import traceback
        traceback.print_exc()
        return {"response_action": "clear"}


def handle_health_share_response(bot, payload):
    """Handle health share response (public/private/no thanks) with background processing."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        action_id = payload['actions'][0]['action_id']

        mood = bot.health_responses.get(user_id, 'Unknown')

        if action_id == 'health_no_share':
            bot.send_dm(user_id, "Thanks for the health check! Processing in background...")

            def process_no_share_in_background():
                try:
                    if hasattr(bot, 'health_responses'):
                        bot.health_responses.pop(user_id, None)
                    bot.send_dm(user_id, "Thanks for the health check! Take care! 💚")
                except Exception as e:
                    print(f"Error in background no share processing: {e}")

            background_thread = threading.Thread(target=process_no_share_in_background)
            background_thread.daemon = True
            background_thread.start()
            return {"response_action": "clear"}

        elif action_id == 'health_share_private':
            trigger_id = payload['trigger_id']
            blocks = [
                {
                    "type": "input",
                    "block_id": "private_share",
                    "label": {"type": "plain_text", "text": "What would you like to share?"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "private_share_input",
                        "multiline": True,
                        "placeholder": {"type": "plain_text", "text": "Share your thoughts, feelings, or anything else..."}
                    }
                }
            ]

            bot.open_modal(
                trigger_id=trigger_id,
                title="Share Privately",
                blocks=blocks,
                submit_text="Share",
                callback_id="health_private_share_submit"
            )
            return {"response_action": "clear"}

        elif action_id == 'health_share_public':
            trigger_id = payload['trigger_id']
            blocks = [
                {
                    "type": "input",
                    "block_id": "public_share",
                    "label": {"type": "plain_text", "text": "What would you like to share publicly?"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "public_share_input",
                        "multiline": True,
                        "placeholder": {"type": "plain_text", "text": "This will be saved to Coda and shared with your team..."}
                    }
                }
            ]

            bot.open_modal(
                trigger_id=trigger_id,
                title="Share Publicly",
                blocks=blocks,
                submit_text="Share",
                callback_id="health_public_share_submit"
            )
            return {"response_action": "clear"}

        return {"response_action": "clear"}
    except Exception as e:
        print(f"Error handling health share response: {e}")
        return {"text": "Error"}


def handle_health_public_share_submission(bot, payload):
    """Handle health public share submission - saves to Coda with background processing."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']

        share_text = values.get('public_share', {}).get('public_share_input', {}).get('value', '')
        mood = bot.health_responses.get(user_id, 'Unknown')

        def process_public_share_in_background():
            try:
                if bot.coda:
                    try:
                        success = bot.coda.save_health_check_sharing(user_id, user_name, mood, share_text, is_public=True)
                        if not success:
                            bot.send_dm(user_id, "⚠️ Your health check was shared publicly, but there was an issue saving to Coda.")
                    except Exception as e:
                        print(f"Error saving to Coda: {e}")
                        bot.send_dm(user_id, "⚠️ Your health check was shared publicly, but there was an issue saving to Coda.")
                else:
                    bot.send_dm(user_id, "✅ Your health check has been shared publicly!")
                bot.health_responses.pop(user_id, None)
            except Exception as e:
                print(f"Error in background public share processing: {e}")
                bot.send_dm(user_id, "❌ Sorry, there was an error processing your public share. Please try again.")

        background_thread = threading.Thread(target=process_public_share_in_background)
        background_thread.daemon = True
        background_thread.start()

        return {"response_action": "clear"}
    except Exception as e:
        print(f"Error handling health public share submission: {e}")
        return {"response_action": "clear"}


def handle_health_no_share(bot, payload):
    """Handle health check no share response with background processing."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)

        bot.send_dm(user_id, "✅ Processing your response in background...")

        def process_no_share_in_background():
            try:
                if hasattr(bot, 'health_responses'):
                    bot.health_responses.pop(user_id, None)
                bot.send_dm(user_id, "✅ Thanks for your response! Take care! 💚")
            except Exception as e:
                print(f"Error in background no share processing: {e}")

        background_thread = threading.Thread(target=process_no_share_in_background)
        background_thread.daemon = True
        background_thread.start()
        return {"response_action": "clear"}
    except Exception as e:
        print(f"Error handling health no share: {e}")
        return {"response_action": "clear"}


def handle_health_private_share_submission(bot, payload):
    """Handle health private share submission - saves to Coda as private with background processing."""
    try:
        user_id = payload['user']['id']
        user_name = bot.get_user_name(user_id)
        values = payload['view']['state']['values']

        share_text = values.get('private_share', {}).get('private_share_input', {}).get('value', '')
        mood = bot.health_responses.get(user_id, 'Unknown')

        bot.send_dm(user_id, "✅ Processing your private share in background...")

        def process_private_share_in_background():
            try:
                if bot.coda:
                    try:
                        success = bot.coda.save_health_check_sharing(user_id, user_name, mood, share_text, is_public=False)
                        if success:
                            bot.send_dm(user_id, "✅ Your private share has been saved to Coda!")
                        else:
                            bot.send_dm(user_id, "⚠️ There was an issue saving your private share to Coda.")
                    except Exception as e:
                        print(f"Error saving private share to Coda: {e}")
                        bot.send_dm(user_id, "⚠️ There was an issue saving your private share to Coda.")
                bot.health_responses.pop(user_id, None)
            except Exception as e:
                print(f"Error in background private share processing: {e}")
                bot.send_dm(user_id, "❌ Sorry, there was an error processing your private share. Please try again.")

        background_thread = threading.Thread(target=process_private_share_in_background)
        background_thread.daemon = True
        background_thread.start()
        return {"response_action": "clear"}
    except Exception as e:
        print(f"Error handling health private share submission: {e}")
        return {"response_action": "clear"}


