# encoding: utf-8
from __future__ import absolute_import, unicode_literals

import redis
from dingtalk.storage.kvstorage import KvStorage
from django.conf import settings
from dingtalk.client import isv

from . import models, constants

redis_client = redis.Redis.from_url(settings.REDIS_DINGTALK_URL)


class ISVClient(isv.ISVClient):
    def __init__(self, suite_key, suite_secret, token=None, aes_key=None, storage=None, timeout=None, auto_retry=True):
        if storage is None:
            storage = KvStorage(redis_client)
        super(ISVClient, self).__init__(suite_key, suite_secret, token, aes_key, storage, timeout, auto_retry)

    def get_corp_model(self, corp_id):
        from . import models
        return models.Corp.objects.filter(suite_id=self.suite_key, corpid=corp_id).first()

    def get_permanent_code_from_cache(self, corp_id):
        ret = super(ISVClient, self).get_permanent_code_from_cache(corp_id)
        if not ret:
            corp = self.get_corp_model(corp_id)
            if corp is not None and corp.permanent_code:
                self.cache.permanent_code.set(corp_id, corp.permanent_code)
                ret = corp.permanent_code
        return ret

    def get_ch_permanent_code_from_cache(self, corp_id):
        ret = super(ISVClient, self).get_ch_permanent_code_from_cache(corp_id)
        if not ret:
            corp = self.get_corp_model(corp_id)
            if corp is not None and corp.ch_permanent_code:
                self.cache.ch_permanent_code.set(corp_id, corp.ch_permanent_code)
                ret = corp.ch_permanent_code
        return ret


def set_agent(corp_model, agents, agent_type):
    for agent in agents:
        agent_model = models.Agent.get_obj_by_unique_key_from_cache(appid=agent['appid'])
        if agent_model is None:
            agent_model = models.Agent()
            agent_model.appid = agent['appid']
            agent_model.suite_id = corp_model.suite_id
            agent_model.agent_type = agent_type
        agent_model.name = agent['agent_name']
        agent_model.logo_url = agent['logo_url']
        agent_model.save_or_update()
        ca = models.CorpAgent.objects.get_all_queryset().filter(agentid=agent['agentid'],
                                                                agent_id=agent['appid'], corp_id=corp_model.pk).first()
        if ca is None:
            ca = models.CorpAgent()
            ca.agentid = agent['agentid']
            ca.agent_id = agent['appid']
            ca.corp_id = corp_model.pk
            ca.save(force_insert=True)


def set_corp_info(corp_model, corp_info):
    auth_corp_info = corp_info.get('auth_corp_info', {})
    for key in ('corp_logo_url', 'corp_name', 'industry', 'invite_code', 'license_code', 'auth_channel',
                'auth_channel_type', 'is_authenticated', 'auth_level', 'invite_url'):
        value = auth_corp_info.get(key, None)
        if value is not None:
            setattr(corp_model, key, value)
    corp_model.save_changed()
    agents = corp_info.get('auth_info', {}).get('agent', [])
    set_agent(corp_model, agents, constants.AGENT_TYPE_CODE.MICRO.code)
    channel_agents = corp_info.get('channel_auth_info', {}).get('channelAgent', [])
    set_agent(corp_model, channel_agents, constants.AGENT_TYPE_CODE.CHANNEL.code)


def sync_corp(corppk):
    corp = models.Corp.get_obj_by_pk_from_cache(corppk)
    if corp is None or corp.suite is None:
        return
    client = corp.suite.get_suite_client()
    if corp.status == constants.CORP_STSTUS_CODE.AUTH.code:
        client.activate_suite(corp.corpid)
        corp.status = constants.CORP_STSTUS_CODE.ACTIVE.code
    corp_info = client.get_auth_info(corp.corpid)
    set_corp_info(corp, corp_info)
