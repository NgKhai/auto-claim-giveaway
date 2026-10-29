from app.policy import evaluate


def opportunity(**overrides):
    return dict(sample=True, automation='unknown', countries=[], student=False, deadline=None, **overrides)


def test_sample_never_authorizes_submission():
    assert evaluate(opportunity(), {'country': 'VN', 'student': 1}, True)[0] == 'needs_user_action'


def test_ineligible_country_is_blocked():
    item = opportunity(); item['countries'] = ['US']
    assert evaluate(item, {'country': 'VN', 'student': 1}, True)[0] == 'blocked'


def test_unknown_student_is_not_assumed_eligible():
    item = opportunity(); item['student'] = True
    assert evaluate(item, {'country': 'VN', 'student': 0}, True)[0] == 'needs_user_action'


def test_prohibited_is_blocked():
    item = opportunity(); item['automation'] = 'prohibited'
    assert evaluate(item, {'country': 'VN', 'student': 1}, True)[0] == 'blocked'
