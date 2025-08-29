"""Handlers subpackage for modular event handlers (health, blockers, KR, etc.)."""

# Expose health handlers for convenience
from .health_handlers import (
    handle_health_response,
    handle_health_share_response,
    handle_health_public_share_submission,
    handle_health_private_share_submission,
    handle_health_no_share,
)

# Expose blocker handlers for convenience
from .blocker_handlers import (
    handle_blocker_note_edit,
    handle_complete_blocker_with_form,
    handle_blocker_followup_response,
    handle_claim_blocker,
    handle_update_progress,
    handle_mark_resolved,
    handle_view_blocker_details,
    handle_submit_blocker_details,
    handle_followup_response,
)

# Expose KR handlers for convenience
from .kr_handlers import (
    handle_open_kr_continue_modal,
    handle_kr_continue_submit,
)

# Expose modal handlers for convenience
from .modal_handlers import (
    handle_open_blocker_report_modal,
    handle_open_checkin_modal,
)

# Expose submission handlers for convenience
from .submission_handlers import (
    handle_blocker_details_submission,
    handle_blocker_note_submission,
    handle_progress_update_submission,
    handle_checkin_submission,
    handle_daily_checkin_submission,
)

# Expose blocker resolution handlers for convenience
from .blocker_resolution_handlers import (
    handle_blocker_completion_submission,
    handle_blocker_resolution_submission,
    handle_blocker_direct_resolution_submission,
    handle_blocker_channel_resolution_submission,
    handle_24hr_resolution_submission,
)

# Expose view handlers for convenience
from .view_handlers import (
    handle_view_details,
    handle_view_all_blockers,
    handle_view_blockers_with_sprint,
    handle_view_blockers_modal,
)

# Expose modal opening handlers for convenience
from .modal_opening_handlers import (
    handle_open_blocker_modal_channel,
    handle_open_blocker_sprint_modal,
    handle_open_blocker_continue_modal,
    handle_open_view_blockers_modal,
)

__all__ = [
    # Health handlers
    "handle_health_response",
    "handle_health_share_response",
    "handle_health_public_share_submission",
    "handle_health_private_share_submission",
    "handle_health_no_share",
    # Blocker handlers
    "handle_blocker_note_edit",
    "handle_complete_blocker_with_form",
    "handle_blocker_followup_response",
    "handle_claim_blocker",
    "handle_update_progress",
    "handle_mark_resolved",
    "handle_view_blocker_details",
    "handle_submit_blocker_details",
    "handle_followup_response",
    # KR handlers
    "handle_open_kr_continue_modal",
    "handle_kr_continue_submit",
    # Modal handlers
    "handle_open_blocker_report_modal",
    "handle_open_checkin_modal",
    # Submission handlers
    "handle_blocker_details_submission",
    "handle_blocker_note_submission",
    "handle_progress_update_submission",
    "handle_checkin_submission",
    "handle_daily_checkin_submission",
    # Blocker resolution handlers
    "handle_blocker_completion_submission",
    "handle_blocker_resolution_submission",
    "handle_blocker_direct_resolution_submission",
    "handle_blocker_channel_resolution_submission",
    "handle_24hr_resolution_submission",
    # View handlers
    "handle_view_details",
    "handle_view_all_blockers",
    "handle_view_blockers_with_sprint",
    "handle_view_blockers_modal",
    # Modal opening handlers
    "handle_open_blocker_modal_channel",
    "handle_open_blocker_sprint_modal",
    "handle_open_blocker_continue_modal",
    "handle_open_view_blockers_modal",
]


