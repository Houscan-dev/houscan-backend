from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    # 1) DRF 기본 핸들러로 response 객체 생성
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data #원본에러정보
        message = None

        # detail 키 존재 시
        if isinstance(data, dict) and 'detail' in data:
            message = data['detail']

        # serializer 검증 에러 형태 시
        elif isinstance(data, dict):
            first_key = next(iter(data))
            errors = data[first_key]
            message = errors[0] if isinstance(errors, (list, tuple)) else str(errors)

        # list 형태 시
        elif isinstance(data, list) and data:
            message = data[0]

        # response.data를 무조건 message~로 덮어쓰는 줄
        response.data = {'message': message or str(data)}

    return response