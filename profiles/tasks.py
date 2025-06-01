from celery import shared_task

@shared_task
def analyze_user_eligibility_task(user_id):
    from announcements.housing_eligibility_analyzer import analyze_user_eligibility
    return analyze_user_eligibility(user_id)