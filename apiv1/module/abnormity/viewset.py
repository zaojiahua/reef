from apiv1.core.view.generic import GenericViewSet
from apiv1.module.abnormity.models import Abnormity
from apiv1.module.abnormity.serializer import AbnormitySerializer


class AbnormityViewset(GenericViewSet):
    serializer_class = AbnormitySerializer
    queryset = Abnormity.objects.all()