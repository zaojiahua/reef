from datetime import datetime, timedelta

from elasticsearch_dsl.query import MultiMatch, MatchAll
from rest_framework import generics, status
from rest_framework.response import Response

from apiv1.documents import RdsLogDocument

"""
ES使用第三方插件elasticsearch_dsl，可参考以下文档
https://elasticsearch-dsl.readthedocs.io/en/stable/api.html#search
"""


class RdsLogSearchView(generics.GenericAPIView):

    def get(self, request):
        """
        :param request: {
                           "start_time" = 2020-7-2%2000:00:00
                           "end_time" = 2020-8-18%2023:59:59
                           "q" = 关键字
                           "limit" = 10
                           "offset" = 0
                           "ordering" = start_time desc
                       }
        :return: [ {
                      "id":72,
                      "file_name":"aa"，
                      "job_name":"111”，
                      "device_name":"Device"，
                      "file_path":"/media/rds_1ogs/system_0A1s908_iPAyF51_MfSStDD_8_Ek5TGUM.1og","start_time":"2020-08-06 17:42:30"，
                      "highlight”: "<em>beginning</em>of system\n07-03 17:00:38.620”
                } ]

        """
        data = request.query_params
        limit = data['limit'] if 'limit' in data else 10
        offset = data['offset'] if 'offset' in data else 0
        ordering = 'rds.' + data['ordering'].split(' ')[0] if 'ordering' in data else '-rds.start_time'

        start_time = time_to_utc_es(data['start_time']) if 'start_time' in data else '2020-01-01T00:00:00Z'
        end_time = time_to_utc_es(data['end_time']) if 'end_time' in data else 'now'

        query = MultiMatch(
            fields=['rds', 'file_content', 'file_name', 'log_file'],
            query=data['q'],
        ) if 'q' in data else MatchAll()

        search_hit = RdsLogDocument.search(). \
            query(query). \
            filter('range', **{'rds.start_time': {'gte': start_time, 'lt': end_time}}). \
            sort(ordering). \
            highlight_options(order='score'). \
            highlight('file_content', 'file_name', 'rds', fragment_size=100, pre_tags="<font color='red'>",
                      post_tags='</font>'). \
            extra(from_=offset, size=limit)

        total = search_hit.execute().hits.total['value']
        search_res = search_hit.to_queryset()

        highlight_dict = {}
        for hit in search_hit:
            if hasattr(hit.meta, 'highlight'):
                highlight_dict[hit.meta.id] = hit.meta.highlight.file_content[0]  # highlight只返回一个

        result = {}
        for rds_log in search_res:
            result[rds_log.id] = {
                'id': rds_log.id,
                'file_name': rds_log.file_name,
                'job_name': rds_log.rds.job.job_name,
                'device_name': rds_log.rds.device.device_name,
                'file_path': rds_log.log_file.url,
                'start_time': datetime.strftime(rds_log.rds.start_time + timedelta(hours=8), '%Y-%m-%d %H:%M:%S'),
                'highlight': highlight_dict.get(str(rds_log.id), '')
            }

        return Response(
            result,
            headers={'Total-Count': total},
            status=status.HTTP_200_OK
        )


def time_to_utc_es(local_time):
    local_time = datetime.strptime(local_time, '%Y-%m-%d %H:%M:%S')
    utc_time = datetime.utcfromtimestamp(local_time.timestamp()).strftime('%Y-%m-%dT%H:%M:%SZ')
    return utc_time
