from django.conf.urls import url

from . import views, views_mac, views_playbooks, views_reports, views_templify, views_pa, views_netmagis
from . import api


ASSET_NAME_RE = r'[a-z0-9._-]+'
GROUP_NAME_RE = r'[a-z0-9.-_]+'
VARIABLE_RE = r'[a-z0-9.-_]+'


urlpatterns = [
    # Authentication
    url(r'^login/$', views.login_form, name='login_form'),
    url(r'^logout/$', views.logout_user, name='logout_user'),
    url(r'^auth/$', views.auth_and_login, name='auth_and_login'),

    # Assets
    url(r'^$', views.index, name='index'),
    url(r'^assets/$', views.assets, name='assets'),
    url(r'^assets/(?P<page>[0-9]+)$', views.assets, name='assets'),
    url(r'^assets/(?P<asset_name>%s)/$' % ASSET_NAME_RE, views.asset, name='asset'),
    url(r'^addvariable/$', views.addvariable, name='addvariable'),
    url(r'^deletevariable/asset/(?P<asset_name>%s)/(?P<variable>%s)$' % (ASSET_NAME_RE, VARIABLE_RE), views.deletevariable, name='deletevariable'),
    url(r'^addasset/$', views.addasset, name='addasset'),
    url(r'^insertasset/$', views.insertasset, name='insertasset'),
    url(r'^deleteasset/(?P<asset_name>%s)$' % ASSET_NAME_RE, views.deleteasset, name='deleteasset'),

    # Search
    url(r'^assets/search$', views.search, name='search'),

    # Groups
    url(r'^addgroup/$', views.addgroup, name='addgroup'),
    url(r'^insertgroup/$', views.insertgroup, name='insertgroup'),
    url(r'^groups/$', views.groups, name='groups'),
    url(r'^groups/(?P<group_name>%s)/$' % GROUP_NAME_RE, views.group, name='group'),
    url(r'^deletevariable/group/(?P<group_name>%s)/(?P<variable>%s)$' % (GROUP_NAME_RE, VARIABLE_RE), views.deletevariable, name='deletevariable'),
    url(r'^deletegroup/(?P<group_name>%s)$' % GROUP_NAME_RE, views.deletegroup, name='deletegroup'),

    # Reports
    url(r'^reports/$', views_reports.reports, name='reports'),
    url(r'^reports/models$', views_reports.report_model, name='report_model'),
    url(r'^reports/junosversions$', views_reports.report_junos_version, name='report_junos_version'),
    url(r'^reports/playbookruns$', views_reports.report_playbook_runs, name='report_playbook_runs'),

    # MAC-ARP / IP usage
    url(r'^macs/$', views_mac.macs, name='macs'),
    url(r'^macs/(?P<start>[0-9.-]+)$', views_mac.macs, name='macs'),
    url(r'^macsearch$', views_mac.macsearch, name='macsearch'),
    url(r'^ipusage$', views_mac.ipusage, name='ipusage'),
    url(r'^ipusagesearch$', views_mac.ipusagesearch, name='ipusagesearch'),

    # Playbooks
    url(r'^playbooks/playbooklog$', views_playbooks.playbook_log, name='playbook_log'),
    url(r'^playbooks/logdetails/(?P<log_id>[a-z0-9]+)$', views_playbooks.playbook_log_details, name='playbook_log_details'),
    url(r'^playbooks/$', views_playbooks.playbooks, name='playbooks'),
    url(r'^playbooks/runplaybook', views_playbooks.run_playbook, name='run_playbook'),
    url(r'^playbooks/playbookredirector$', views_playbooks.playbookredirector, name='playbookredirector'),
    url(r'^playbooks/(?P<playbook_id>[0-9]+)', views_playbooks.playbook_input, name='playbook_input'),

    # Deploy ports
    url(r'^deployport/$', views_playbooks.deployport, name='deployport'),

    # Templates / templify
    url(r'^templify/$', views_templify.index, name='templify'),
    url(r'^templify/download/(?P<filename>[0-9a-z/-]+)$', views_templify.download, name='download'),
    url(r'^templify/template/(?P<template_id>[0-9]+)/$', views_templify.template_input, name='template_input'),
    url(r'^templify/template/genconfig$', views_templify.generate_config, name='generate_config'),

    # Ansible jobs
    url(r'^ansibletasks/$', views_playbooks.ansibletasks, name='ansibletasks'),
    url(r'^deletetask/(?P<task_id>[0-9]+)$', views_playbooks.deletetask, name='deletetask'),
    url(r'^retry_task/(?P<log_id>[0-9\w]+)$', views_playbooks.retry_task, name='retry_task'),

    # API version 1
    url(r'^api/v1/getmac/(?P<ip_address>[0-9.-]+)/$', api.api_get_mac, name='api_get_mac'),
    url(r'^api/v1/netmagis_search/(?P<search_keyword>[\w\d.-]+)/$', api.api_netmagis_search, name='api_netmagis_search'),

    # Port automation
    url(r'^pa/port$', views_pa.pa_port, name='pa_port'),
    url(r'^pa/prepare$', views_pa.pa_prepare, name='pa_prepare'),
    url(r'^pa/tsport$', views_pa.pa_ts_port, name='pa_ts_port'),
    url(r'^pa/pa_troubleshoot$', views_pa.pa_troubleshoot, name='pa_troubleshoot'),
    url(r'^pa/dhcp_search$', views_pa.dhcp_search, name='dhcp_search'),

    # NetMagis
    url(r'^nm/nm$', views_netmagis.netmagis, name='netmagis'),
    url(r'^nm/networks$', views_netmagis.networks, name='nm_networks'),
    url(r'^nm/searchhost$', views_netmagis.searchhost, name='nm_searchhost'),
]
