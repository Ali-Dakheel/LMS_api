from rest_framework.response import Response
from rest_framework import status

def success_response(data=None, message="Success", meta=None, status_code=status.HTTP_200_OK):
    response_data = {
        "success": True,
        "message": message,
        "data": data,
    }
    if meta:
        response_data["meta"] = meta
    return Response(response_data, status=status_code)

def error_response(message="Error", errors=None, error_code=None, status_code=status.HTTP_400_BAD_REQUEST):
    response_data = {
        "success": False,
        "message": message,
        "errors": errors or {},
    }
    if error_code:
        response_data["error_code"] = error_code
    return Response(response_data, status=status_code)
