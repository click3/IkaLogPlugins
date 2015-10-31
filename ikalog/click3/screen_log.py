#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time

try:
    import wx
except:
    pass

from ikalog.constants import *
from ikalog.utils import *

class ScreenLog(object):

    def __init__(self, out_dir=None):
        self.on_config_reset()
        self.enabled = not (out_dir is None)
        self.out_dir = out_dir
        self.last_dead_ss_path = None

    def _get_default_out_dir(self):
        return os.path.join(os.getcwd(), 'screen_logs')

    def _death_reason_to_text(self, reason):
        reason_list = {reason: {'ja': 'unknown'}}
        reason_list.update(weapons)
        reason_list.update(sub_weapons)
        reason_list.update(special_weapons)
        return reason_list[reason]['ja']

    def _create_file_path(self, filename):
        postfix = time.strftime('%Y%m%d%H%M%S', time.localtime())
        path = os.path.join(self.out_dir, filename + '_' + postfix + '.png')
        return path

    def _save_screen(self, context, filename):
        if not self.enabled:
            return None
        try:
            os.mkdir(self.out_dir)
        except:
            pass
        temp_path = os.path.join(self.out_dir, 'temp.png')
        IkaUtils.writeScreenshot(temp_path, context['engine']['frame'])
        path = self._create_file_path(filename)
        os.rename(temp_path, path)
        print('save screen log: %s' % path)
        return path

    def on_config_reset(self, context=None):
        self.enabled = False
        self.out_dir = self._get_default_out_dir()

    def on_config_load_from_context(self, context):
        self.on_config_reset(context)
        try:
            conf = context['config']['screen_log']
        except:
            conf = {}

        if 'Enable' in conf:
            self.enabled = conf['Enable']

        if 'OutDir' in conf:
            self.out_dir = conf['OutDir']

        self.checkEnabled.SetValue(self.enabled)
        self.editOutDir.SetValue(self.out_dir or '')
        return True

    def on_config_save_to_context(self, context):
        context['config']['screen_log'] = {
            'Enable': self.enabled,
            'OutDir': self.out_dir,
        }

    def on_config_apply(self, context):
        self.enabled = self.checkEnabled.GetValue()
        self.out_dir = self.editOutDir.GetValue()

    def on_option_tab_create(self, notebook):
        self.panel = wx.Panel(notebook, wx.ID_ANY)
        notebook.InsertPage(0, self.panel, 'ScreenLog')
        self.checkEnabled = wx.CheckBox(self.panel, wx.ID_ANY, u'各種タイミングでスクリーンショットを保存する')
        self.editOutDir = wx.TextCtrl(self.panel, wx.ID_ANY, self._get_default_out_dir())

        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(wx.StaticText(self.panel, wx.ID_ANY, u'保存ディレクトリ'))
        self.layout.Add(self.editOutDir, flag=wx.EXPAND)
        self.layout.Add(self.checkEnabled)
        self.panel.SetSizer(self.layout)

    def on_lobby_matching(self, context):
        self._save_screen(context, 'matching')

    def on_lobby_matched(self, context):
        self._save_screen(context, 'matched')

    def on_game_start(self, context):
        self._save_screen(context, 'start_'
            + IkaUtils.rule2text(context['game']['rule'], unknown='unknown') + '_'
            + IkaUtils.map2text(context['game']['map'], unknown='unknown'))

    def on_game_go_sign(self, context):
        self._save_screen(context, 'go_sign')

    def on_game_finish(self, context):
        self._save_screen(context, 'finish')

    def on_game_killed(self, context):
        self._save_screen(context, 'killed')

    def on_game_dead(self, context):
        self.last_dead_ss_path = self._save_screen(context, 'dead')

    def on_game_death_reason_identified(self, context):
        if (not self.last_dead_ss_path):
            return
        path = self._create_file_path('death_reason_' + self._death_reason_to_text(context['game']['last_death_reason']))
        if os.path.exists(self.last_dead_ss_path):
            os.rename(self.last_dead_ss_path, path)
            print('rename screen log: %s => %s' % (self.last_dead_ss_path, path))
            self.last_dead_ss_path = None

    def on_game_individual_result_analyze(self, context):
        self._save_screen(context, 'result_analyze')

    def on_game_individual_result(self, context):
        self._save_screen(context, 'result_' + IkaUtils.getWinLoseText(context['game']['won']))

    def on_result_gears(self, context):
        self._save_screen(context, 'result_gears')

    def on_game_reset(self, context):
        self._save_screen(context, 'reset')

    def on_game_session_end(self, context):
        self._save_screen(context, 'session_end')


