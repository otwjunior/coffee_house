"""Social Auth pipeline: Extract full name from Google and sve it to 'full_name' field """
from social_core.exceptions import AuthException

def set_full_name(backends, details, user=None, *args, **kwargs):
    """Grab name from Google or any provider save to fullname field
        `details` contains:
        - 'fullname': "John Doe"
        - 'first_name': "John"
        - 'last_name': "Doe"
    
    """
    if not user:
        return
    #get full name from provider
    full_name = details.get('fullname') or \
        f"{details.get('first_name', '')} {details.get('last_name', '')}".strip()
    if full_name and full_name != user.full_name:
        user.full_name = full_name
        user.save(updated_fields=['full_name'])

    return {'user': user}