"""Deterministic decisions. No model output can authorize an external action."""
from datetime import datetime, timezone


def evaluate(opportunity, profile, automation_enabled=False):
    deadline = opportunity.get('deadline')
    if deadline:
        try:
            parsed = datetime.fromisoformat(deadline)
        except (ValueError, TypeError):
            return 'needs_user_action', 'The deadline cannot be verified. Check the source before proceeding.'
        if parsed.tzinfo is None:
            return 'needs_user_action', 'The deadline timezone is unknown. Verify it with the provider.'
        if parsed <= datetime.now(timezone.utc):
            return 'blocked', 'This opportunity has expired.'
    if opportunity.get('countries') and profile['country'] not in opportunity['countries']:
        return 'blocked', 'Your country is outside the published eligibility.'
    if opportunity.get('automation') == 'prohibited':
        return 'blocked', 'The provider prohibits automated registration.'
    if opportunity.get('student') and not profile['student']:
        return 'needs_user_action', 'Student eligibility needs supporting evidence.'
    if opportunity.get('sample'):
        return 'needs_user_action', 'Research example only. Verify current terms with the provider; no external submission is available.'
    if opportunity.get('automation') != 'allowed':
        return 'needs_user_action', 'Provider permission for automation has not been verified.'
    return 'awaiting_approval', 'Review the destination and exact data before authorizing an application.'
