from django.db import transaction
from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.validators import UniqueValidator

from apiv1.core import constants
from apiv1.module.device.models import PaneView, PaneSlot
from apiv1.module.system.models import Cabinet


class CreateTestBoxPaneviewSerializer(serializers.Serializer):

    name = serializers.CharField(validators=[UniqueValidator(queryset=PaneView.objects.all())])
    cabinet = serializers.PrimaryKeyRelatedField(
        queryset=Cabinet.objects.all(),
        validators=[UniqueValidator(queryset=PaneView.objects.all())]
    )
    type = serializers.ChoiceField(choices=(
        constants.PANEVIEW_TYPE_TEST_BOX,)
    )
    width = serializers.IntegerField(required=False)
    height = serializers.IntegerField(required=False)
    # robot_arm = serializers.CharField()
    # camera = serializers.IntegerField(required=False)


class CreateTestBoxPaneview(generics.GenericAPIView):

    serializer_class = CreateTestBoxPaneviewSerializer
    queryset = PaneView.objects.all()

    def post(self, request):
        req_serializer: CreateTestBoxPaneviewSerializer = self.get_serializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)
        data = req_serializer.validated_data

        with transaction.atomic():
            paneview = PaneView.objects.create(
               **data
            )
            # test_box Paneview目前只会有一个paneslot
            slots = PaneSlot.objects.create(
                paneview=paneview,
                row=1,
                col=1
            )
        return Response({'id':paneview.id}, status=status.HTTP_201_CREATED)
