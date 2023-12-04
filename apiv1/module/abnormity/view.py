from datetime import datetime

from rest_framework import status, generics
from rest_framework.response import Response

from apiv1.core.response import ReefResponse
from apiv1.core.utils import date_format_transverter
from apiv1.core.view.generic import AutoExecuteSerializerGenericAPIView
from apiv1.module.abnormity.models import AbnormityType, Abnormity, AbnormityDetail
from apiv1.module.abnormity.serializer import GetAbnormityCountSerializer, AbnormityListSerializer, \
    CreateExceptionSerializer
from apiv1.module.device.models import DevicePower
from apiv1.module.tboard.models import TBoard


class GetAbnormityCountView(generics.GenericAPIView):

    serializer_class = GetAbnormityCountSerializer
    queryset = Abnormity.objects.all()

    def get(self, request):
        query_params = request.query_params.dict()
        devices = query_params.get('devices', '').split(',')
        if all(devices):
            query_params['devices'] = devices
        serializer = self.get_serializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        tboard = data.get('tboard', None)
        if tboard:
            start_time, end_time, device_list = get_tboard_info(tboard)
        else:
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            device_list = data.get('devices')
            if not all([start_time, end_time, device_list]):
                return Response({'message': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

        abnm_type_queryset = AbnormityType.objects.all()
        results = []
        for abnm_type_obj in abnm_type_queryset:
            # 没有结束时间的异常区分查找
            if abnm_type_obj.code in [1]:
                abnm_queryset = Abnormity.objects.filter(device_id__in=device_list, abnormity_type=abnm_type_obj,
                                                         start_time__gte=start_time, end_time__lte=end_time)
            else:
                abnm_queryset = Abnormity.objects.filter(device_id__in=device_list, abnormity_type=abnm_type_obj,
                                                         start_time__gte=start_time, start_time__lte=end_time)
            abnm_device_num = abnm_queryset.values('device').distinct().count()
            abnm_num = abnm_queryset.count()
            result = {
                'abnm_type_name': abnm_type_obj.title,
                'abnm_num': abnm_num,
                'abnm_device_num': abnm_device_num,
                'code': abnm_type_obj.code
            }
            results.append(result)
        return Response({'results': results}, status=status.HTTP_200_OK)


class AbnormityListView(generics.GenericAPIView):

    serializer_class = AbnormityListSerializer
    queryset = Abnormity.objects.all()

    def get(self, request):
        query_params = request.query_params.dict()
        devices = query_params.get('devices', '').split(',')
        if all(devices):
            query_params['devices'] = devices
        serializer = self.get_serializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        tboard = data.get('tboard', None)
        if tboard:
            start_time, end_time, device_list = get_tboard_info(tboard)
        else:
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            device_list = data.get('devices')

        abnormity_type = data.get('abnormity_type')
        try:
            abnm_queryset = Abnormity.objects.filter(
                abnormity_type=abnormity_type, start_time__gte=start_time, device_id__in=device_list,
                start_time__lt=end_time
            )
            # 有结束时间的异常添加筛选条件
            if abnormity_type.code in [1]:
                abnm_queryset.filter(end_time__lte=end_time)
            else:
                abnm_queryset.filter(start_time__lt=end_time)

        except Exception as e:
            return Response({'error_message': f'Get abnm_queryset failed: {str(e)}' }, status=status.HTTP_400_BAD_REQUEST)
        if not abnm_queryset.exists():
            return Response({}, status=status.HTTP_200_OK)
        results = []
        abnm_device_queryset = abnm_queryset.distinct('device')
        for abnm_device_obj in abnm_device_queryset:
            result = {'device_name': abnm_device_obj.device.device_name, 'device_id': abnm_device_obj.device.id,
                      'time_section': [], 'device_label': abnm_device_obj.device.device_label}
            abnm_data_queryset = abnm_queryset.filter(device_id=abnm_device_obj.device).order_by('date', 'start_time')
            # 这里使用
            time_template = []
            for abnm_data in abnm_data_queryset:
                if abnm_data.date in time_template:
                    time_info = {'abnm_id': abnm_data.id,
                                 'abnm_start_time': date_format_transverter(abnm_data.start_time),
                                 'abnm_end_time': date_format_transverter(abnm_data.end_time)}
                    # ANR, Crash, Exception 异常添加数据
                    if abnm_data.abnormity_type.code in [2, 3, 4]:
                        abnm_detail = abnm_data.abnm_detail.first()
                        time_info["result_data"] = abnm_detail.result_data
                        time_info["log_list"] = [
                            {"log_file": "/media/" + data[0], "name": data[1]}
                            for data in abnm_detail.abnormitylog.all().values_list('file', 'name')
                        ]
                    # 将数据添加到指定日期内
                    [data['data'].append(time_info) for data in result['time_section'] if data['time'] == abnm_data.date]
                else:
                    time_template.append(abnm_data.date)
                    time_info = {
                         'abnm_id': abnm_data.id,
                         'abnm_start_time': date_format_transverter(abnm_data.start_time),
                         'abnm_end_time': date_format_transverter(abnm_data.end_time)
                    }
                    # ANR, Crash, Exception 异常添加数据
                    if abnm_data.abnormity_type.code in [2, 3, 4]:
                        abnm_detail = abnm_data.abnm_detail.first()
                        time_info["result_data"] = abnm_detail.result_data
                        time_info["log_list"] = [
                            {"log_file": '/media/' + data[0], "name": data[1]}
                            for data in abnm_detail.abnormitylog.all().values_list('file', 'name')
                        ]
                    result['time_section'].append({'time': abnm_data.date, "data": [time_info]})
            result['count'] = len(result['time_section'])
            results.append(result)

        return Response(results, status=status.HTTP_200_OK)


class PowerAbnormityChartView(generics.GenericAPIView):

    def get(self, request):
        query_params = request.query_params
        abnormity_id = query_params.get('abnormity', None)
        try:
            abnm_obj = Abnormity.objects.get(id=abnormity_id)
        except Exception as e:
            return Response({'error_message': f'Get Abnormity obj failed: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        abnm_detail_queryset = AbnormityDetail.objects.filter(abnormity_id=abnormity_id).order_by('time')
        # 电量数据
        abnm_data_list = []
        device_poser_lt = DevicePower.objects.filter(record_datetime__lt=abnm_obj.start_time,
                                                     device=abnm_obj.device).order_by('record_datetime').last()
        abnm_data_list.append([date_format_transverter(device_poser_lt.record_datetime), device_poser_lt.battery_level])
        results = {'data': abnm_data_list, 'abnormity': [date_format_transverter(abnm_obj.start_time), date_format_transverter(abnm_obj.end_time)]}
        for abnm_deail in abnm_detail_queryset:
            result = [date_format_transverter(abnm_deail.time), abnm_deail.result_data.get('power', 0)]
            abnm_data_list.append(result)
        device_poser_gt = DevicePower.objects.filter(record_datetime__gt=abnm_obj.end_time,
                                                     device=abnm_obj.device).order_by('record_datetime').first()
        abnm_data_list.append([date_format_transverter(device_poser_gt.record_datetime), device_poser_gt.battery_level])
        return Response(results, status=status.HTTP_200_OK)


class PowerAbnormityDataView(generics.GenericAPIView):


    def get(self, request):

        query_params = request.query_params
        abnormity_id = query_params.get('abnormity', None)
        try:
            abnm_obj = Abnormity.objects.get(id=abnormity_id)
        except Exception as e:
            return Response({'error_message': f'Get Abnormity obj failed: {e}, abnormity_id [{abnormity_id}] not exit'})
        abnm_detail_queryset = AbnormityDetail.objects.filter(abnormity=abnm_obj).order_by('time')
        # 耗电量
        power_difference = abnm_detail_queryset.first().result_data.get('power', 0) - abnm_detail_queryset.last().result_data.get('power', 0)
        # 时长
        duration = round((abnm_obj.end_time - abnm_obj.start_time).seconds / 60)
        duration_time = duration if duration > 0 else 1
        # 平均耗电
        avg_power = round(power_difference / duration_time, 3)
        results = {'abnm_start_time': date_format_transverter(abnm_obj.start_time), 'device_name': abnm_obj.device.device_name,
                   'device_id': abnm_obj.device.id, 'device_label': abnm_obj.device.device_label,
                   'abnm_end_time': date_format_transverter(abnm_obj.end_time),
                   'duration_time': duration_time, 'power_difference': power_difference,
                   'avg_power': avg_power}
        return Response(results, status=status.HTTP_200_OK)


class CreateExceptionView(AutoExecuteSerializerGenericAPIView):

    serializer_class = CreateExceptionSerializer
    queryset = Abnormity.objects.all()

    def post(self, request):
        serializer = self.execute(request)
        file_path_list = serializer.save()
        return ReefResponse(file_path_list)

####################################
# Helper function                  #
####################################

def get_tboard_info(tboard: TBoard):

    if tboard.finished_flag:
        end_time = tboard.end_time
    else:
        end_time = datetime.now()

    device_id_list = tboard.device.all().values_list('id', flat=True)
    return tboard.board_stamp, end_time, device_id_list









