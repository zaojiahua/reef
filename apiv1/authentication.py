from rest_framework.authentication import TokenAuthentication


class BareTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'
