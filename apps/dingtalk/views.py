# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from apiview.err_code import ErrCode
from apiview.exceptions import CustomError
from apiview.views import ViewSite, fields
from dingtalk.client.channel import ChannelClient
from dingtalk.core.constants import SuitePushType
from django.utils.encoding import force_text
from rest_framework.response import Response

from core import view
from example import celery
from . import models, constants, biz, cache


site = ViewSite(name='dingtalk', app_name='apps.dingtalk')


@site
class TestCorpInfo(view.AdminApi):

    def get_context(self, request, *args, **kwargs):
        return biz.sync_corp(request.params.corp_pk)

    class Meta:
        param_fields = (
            ('corp_pk', fields.IntegerField(help_text='corp_pk', required=True)),
        )


@site
class SuiteCallback(view.APIBase):

    name = '授权事件接收URL'

    def proc_message(self, suite_key, message):
        event_type = message.get('EventType', None)
        ret = 'success'
        if event_type in (SuitePushType.CHECK_CREATE_SUITE_URL.value, SuitePushType.CHECK_UPDATE_SUITE_URL.value):
            ret = message.get('Random', '')
        elif event_type == SuitePushType.TMP_AUTH_CODE.value:
            permanent_code_data = message.get('__permanent_code_data', {})
            auth_corp_info = permanent_code_data.get('auth_corp_info', {})
            permanent_code = permanent_code_data.get('permanent_code', None)
            ch_permanent_code = permanent_code_data.get('ch_permanent_code', None)
            corpid = auth_corp_info.get('corpid', None)
            corp_name = auth_corp_info.get('corp_name', None)

            if permanent_code is None or corpid is None or corp_name is None:
                ret = 'fail'
            else:
                corp = models.Corp.objects.get_all_queryset().filter(suite_id=suite_key, corpid=corpid).first()
                if corp is None:
                    corp = models.Corp()
                    corp.suite_id = suite_key
                    corp.corpid = corpid
                if corp.status == constants.CORP_STSTUS_CODE.NO.code:
                    corp.status = constants.CORP_STSTUS_CODE.AUTH.code
                corp.permanent_code = permanent_code
                if ch_permanent_code is not None:
                    corp.ch_permanent_code = ch_permanent_code
                corp.corp_name = corp_name
                corp.save_or_update()
                celery.async_call(biz.sync_corp, corp.pk)

        elif event_type == SuitePushType.CHANGE_AUTH.value:
            pass

        elif event_type == SuitePushType.SUITE_RELIEVE.value:
            corp_id = message.get('AuthCorpId', None)
            if corp_id is None:
                ret = 'fail'
            else:
                corp = models.Corp.objects.get_all_queryset().filter(corpid=corp_id, suite_id=suite_key).first()
                if corp is not None:
                    corp.status = constants.CORP_STSTUS_CODE.NO.code
                    corp.save_changed()
        elif event_type == SuitePushType.CHECK_SUITE_LICENSE_CODE.value:
            pass
        elif event_type != SuitePushType.SUITE_TICKET.value:
            self.logger.warning("unkown event_type : %s %s", suite_key, message)
        return ret

    def get_context(self, request, suite_key=None, *args, **kwargs):
        self.logger.info("receive_ticket msg path: %s query: %s, body: %s",
                         request.path, request.META['QUERY_STRING'], self.get_req_body(request))
        msg = self.get_req_body(request)
        assert msg
        msg = force_text(msg)
        suite = models.Suite.objects.filter(suite_key=suite_key).first()
        assert suite
        client = suite.get_suite_client()
        message = client.parse_message(msg, request.params.signature, request.params.timestamp, request.params.nonce)
        self.logger.info("receive_ticket msg: %s" % force_text(message))

        return Response(client.crypto.encrypt_message(self.proc_message(suite_key, message)))

    class Meta:
        path = "suite/callback/(?P<suite_key>[0-9a-zA-Z]+)"
        param_fields = (
            ('timestamp', fields.CharField(help_text='timestamp', required=True)),
            ('nonce', fields.CharField(help_text='nonce', required=True)),
            ('signature', fields.CharField(help_text='signature', required=True))
        )


class CorpAgentBase(view.APIBase):

    def get_corp_agent_info(self, request):
        corp_agent_id = cache.CorpAgentCache.get("%s|||%s" % (request.params.app_id, request.params.corp_id))
        if corp_agent_id is not None:
            return models.CorpAgent.get_obj_by_pk_from_cache(corp_agent_id)
        agent = models.Agent.get_obj_by_unique_key_from_cache(appid=request.params.app_id)
        if agent is None:
            raise CustomError(ErrCode.ERR_COMMON_BAD_PARAM)
        suite = agent.suite
        corp = models.Corp.objects.filter(corpid=request.params.corp_id, suite_id=suite.pk).first()
        if corp is None:
            raise CustomError(ErrCode.ERR_COMMON_BAD_PARAM)

        corp_agent = models.CorpAgent.objects.filter(agent_id=agent.appid, corp_id=corp.pk).first()
        if corp_agent is None:
            raise CustomError(ErrCode.ERR_COMMON_BAD_PARAM)
        cache.CorpAgentCache.set("%s|||%s" % (request.params.app_id, request.params.corp_id), corp_agent)
        return corp_agent

    def get_context(self, request, *args, **kwargs):
        raise NotImplementedError

    class Meta:
        param_fields = (
            ('corp_id', fields.CharField(help_text='corp_id', required=True)),
            ('app_id', fields.IntegerField(help_text='app_id', required=True)),
        )


@site
class JsConfig(CorpAgentBase):

    def get_context(self, request, *args, **kwargs):
        url = request.META.get('HTTP_REFERER', None)
        if not url:
            raise CustomError(ErrCode.ERR_COMMON_BAD_PARAM, message='cannot found referer')
        corp_agent = self.get_corp_agent_info(request)
        client = corp_agent.get_client()
        if client is None:
            raise CustomError(ErrCode.ERR_COMMON_BAD_PARAM)
        ret = client.get_jsapi_params(url)
        ret['agentId'] = corp_agent.agentid
        return ret


@site
class UserInfo(CorpAgentBase):

    def get_context(self, request, *args, **kwargs):

        corp_agent = self.get_corp_agent_info(request)
        client = corp_agent.get_client()
        if client is None or not isinstance(client, ChannelClient):
            raise CustomError(ErrCode.ERR_COMMON_PERMISSION)
        ret = client.get_by_code(request.params.code)
        return ret

    class Meta:
        param_fields = (
            ('code', fields.CharField(help_text='code', required=True)),
        )


urlpatterns = site.urlpatterns
