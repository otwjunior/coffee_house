"""googl sends full name we store it"""
def set_full_name(backends,details,user=None, *args, **kwargs):
    """Grab name from Google save to fullname field"""
    if user and details.get('fullname'):
        user.full_name = details['fullname']
        user.save()
    return {'user':user}