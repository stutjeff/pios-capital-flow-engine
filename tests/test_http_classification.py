from pios.core.http import classify_http

def test_http_error_classification():
    assert classify_http(401,'bad key')=='INVALID_KEY'
    assert classify_http(403,'premium plan required')=='PLAN_NOT_SUPPORTED'
    assert classify_http(429,'too many')=='RATE_LIMIT'
    assert classify_http(500,'oops')=='UPSTREAM_ERROR'
