#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import threading

try:
    import wx
except:
    pass

from ikalog.constants import *
from ikalog.utils import *

class RecordKicker(object):

    def __init__(self, monitoring_dir=None, kick_path=None, rename_format=None):
        self.on_config_reset()
        self.enabled = (not (monitoring_dir is None)) and (not (kick_path is None))
        self.monitoring_dir = monitoring_dir
        self.kick_path = kick_path
        self.rename_format = rename_format

    def _weapon_id_to_text(self, id):
        weapon_list = {id: {'ja': 'unknown'}}
        weapon_list.update(weapons)
        return weapon_list[id]['ja']

    def _get_stage_name(self, context):
        return IkaUtils.map2text(context['game']['map'], unknown='unknown')

    def _get_rule_name(self, context):
        return IkaUtils.rule2text(context['game']['rule'], unknown='unknown')

    def _get_weapon_name(self, context):
        return self._weapon_id_to_text(IkaUtils.getMyEntryFromContext(context)['weapon'])

    def _get_kill(self, context):
        return IkaUtils.getMyEntryFromContext(context)['kills']

    def _get_death(self, context):
        return IkaUtils.getMyEntryFromContext(context)['deaths']

    def _get_point(self, context):
        try:
            return IkaUtils.getMyEntryFromContext(context)['score']
        except:
            return 'unknown'

    def _get_won(self, context):
        return IkaUtils.getWinLoseText(context['game']['won'])

    def _get_rank(self, context):
        return IkaUtils.getMyEntryFromContext(context)['rank']

    def _get_udemae(self, context):
        try:
            return IkaUtils.getMyEntryFromContext(context)['udemae_pre']
        except:
            return 'unknown'

    def _get_rank_in_team(self, context):
        return IkaUtils.getMyEntryFromContext(context)['rank_in_team']

    def _create_dest_filename(self, context):
        if (not self.rename_format):
            return None
        now = time.localtime()
        list = [
            ['year', now.tm_year],
            ['month', now.tm_mon, 2],
            ['date', now.tm_mday, 2],
            ['hour', now.tm_hour, 2],
            ['minute', now.tm_min, 2],
            ['second', now.tm_sec, 2],
            ['stage', self._get_stage_name(context)],
            ['rule', self._get_rule_name(context)],
            ['weapon', self._get_weapon_name(context)],
            ['kill', self._get_kill(context)],
            ['death', self._get_death(context)],
            ['point', self._get_point(context)],
            ['won', self._get_won(context)],
            ['rank', self._get_rank(context)],
            ['udemae', self._get_udemae(context)],
            ['rank_in_team', self._get_rank_in_team(context)],
        ]
        result = self.rename_format
        for item in list:
            text = None
            if (len(item) == 2):
                text = str(item[1])
            elif (len(item) == 3):
                text = ('%%0%dd' % item[2]) % item[1]
            result = result.replace('%%%s%%' % item[0], text)
        return result

    def _kick(self, arg):
        if (not self.enabled) or (not self.kick_path) or (not self.monitoring_dir):
            return
        cmd = ('%s %s' % (self.kick_path, arg))
        print('exec: %s' % cmd)
        os.system(cmd)

    def _start_record(self):
        thread = threading.Thread(target=self._kick, args=('start',))
        thread.start()

    def _stop_record(self, context):
        list = [
            ['IKALOG_MP4_DESTDIR', self.monitoring_dir],
            ['IKALOG_MP4_DESTNAME', self._create_dest_filename(context)],
            ['IKALOG_STAGE', self._get_stage_name(context)],
            ['IKALOG_RULE', self._get_rule_name(context)],
            ['IKALOG_WEAPON', self._get_weapon_name(context)],
            ['IKALOG_KILL', self._get_kill(context)],
            ['IKALOG_DEATH', self._get_death(context)],
            ['IKALOG_POINT', self._get_point(context)],
            ['IKALOG_WON', self._get_won(context)],
            ['IKALOG_RANK', self._get_rank(context)],
            ['IKALOG_UDEMAE', self._get_udemae(context)],
            ['IKALOG_RANK_IN_TEAM', self._get_rank_in_team(context)],
        ]
        for item in list:
            if (item[1] == None):
                if (item[0] in os.environ):
                    os.environ.pop(item[0])
                continue
            os.environ[item[0]] = str(item[1])
            print('%s = %s' % (item[0], item[1]))
        thread = threading.Thread(target=self._kick, args=('stop',))
        thread.start()

    def on_config_reset(self, context=None):
        self.enabled = False
        self.monitoring_dir = None
        self.kick_path = os.path.join(os.getcwd(), 'tools', 'ControlAmaRecTV.exe')
        self.rename_format = u'%year%%month%%date%_%hour%%minute%_%stage%_%weapon%_%rule%_%kill%キル%death%デス%point%pt.avi'

    def on_config_load_from_context(self, context):
        self.on_config_reset(context)
        try:
            conf = context['config']['record_kicker']
        except:
            conf = {}

        if 'Enable' in conf:
            self.enabled = conf['Enable']
        if 'MonitoringDir' in conf:
            self.monitoring_dir = conf['MonitoringDir']
        if 'KickPath' in conf:
            self.kick_path = conf['KickPath']
        if 'RenameFormat' in conf:
            self.rename_format = conf['RenameFormat']

        self.checkEnabled.SetValue(self.enabled)
        self.editMonitoringDir.SetValue(self.monitoring_dir or '')
        self.editKickPath.SetValue(self.kick_path or '')
        self.editRenameFormat.SetValue(self.rename_format or '')
        return True

    def on_config_save_to_context(self, context):
        context['config']['record_kicker'] = {
            'Enable': self.enabled,
            'MonitoringDir': self.monitoring_dir,
            'KickPath': self.kick_path,
            'RenameFormat': self.rename_format,
        }

    def on_config_apply(self, context):
        self.enabled = self.checkEnabled.GetValue()
        self.monitoring_dir = self.editMonitoringDir.GetValue()
        self.kick_path = self.editKickPath.GetValue()
        self.rename_format = self.editRenameFormat.GetValue()

    def on_option_tab_create(self, notebook):
        self.panel = wx.Panel(notebook, wx.ID_ANY)
        notebook.InsertPage(0, self.panel, 'RecordKicker')
        self.checkEnabled = wx.CheckBox(self.panel, wx.ID_ANY, u'録画開始と終了をIkaLogから制御する')
        self.editMonitoringDir = wx.TextCtrl(self.panel, wx.ID_ANY, '')
        self.editKickPath = wx.TextCtrl(self.panel, wx.ID_ANY, '')
        self.editRenameFormat = wx.TextCtrl(self.panel, wx.ID_ANY, '')

        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.checkEnabled)
        self.layout.Add(wx.StaticText(self.panel, wx.ID_ANY, u'録画ファイル保存ディレクトリ'))
        self.layout.Add(self.editMonitoringDir, flag=wx.EXPAND)
        self.layout.Add(wx.StaticText(self.panel, wx.ID_ANY, u'録画操作ツールのパス'))
        self.layout.Add(self.editKickPath, flag=wx.EXPAND)
        self.layout.Add(wx.StaticText(self.panel, wx.ID_ANY, u'録画ファイルリネームする場合のフォーマット'))
        self.layout.Add(self.editRenameFormat, flag=wx.EXPAND)
        self.panel.SetSizer(self.layout)

    def on_lobby_matched(self, context):
        self._start_record()

    def on_game_individual_result(self, context):
        self._stop_record(context)

