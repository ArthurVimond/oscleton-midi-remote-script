from _Framework.SessionComponent import SessionComponent
from OscletonMixin import OscletonMixin

import microjson
import re

class OscletonBrowserComponent(SessionComponent, OscletonMixin):

    _max_items_per_chunk = 30

    def __init__(self):
        self._browser = self.application().browser

        self.add_callback('/live/browser/preview_browser_item', self._preview_browser_item)
        self.add_callback('/live/browser/load_browser_item', self._load_browser_item)
        self.add_callback('/live/browser/get_browser_item_children', self._get_browser_item_children)
        self.add_callback('/live/browser/stop_preview', self._stop_preview)


    def _get_browser_item(self, msg, src, useVST2CustomFolder):
        browser_item_uri = msg[2]

        no_query_uri = self._remove_prefix(browser_item_uri, 'query:')
        decoded_uri = no_query_uri

        # NB: For Plugins/VST folder, if custom folder is not used,
        # the 'Local' folder is hidden, so it needs to be removed from the uri
        if not useVST2CustomFolder:
            decoded_uri = decoded_uri.replace('Plugins#VST:Local', 'Plugins#VST')

        nodes = re.split('[#:]', decoded_uri)
        parent_nodes = nodes[:-1]
        category = nodes[0]

        if 'Sounds' in category:
            browser_item = self._browser.sounds
        elif 'Drums' in category:
            browser_item = self._browser.drums
        elif 'Synths' in category:
            browser_item = self._browser.instruments
        elif 'AudioFx' in category:
            browser_item = self._browser.audio_effects
        elif 'MidiFx' in category:
            browser_item = self._browser.midi_effects
        elif 'M4L' in category:
            browser_item = self._browser.max_for_live
        elif 'Plugins' in category:
            browser_item = self._browser.plugins
        elif 'Clips' in category:
            browser_item = self._browser.clips
        elif 'Samples' in category:
            browser_item = self._browser.samples
        else:
            return

        if len(nodes) == 1:
            return browser_item

        node_index = 1
        browser_item = self._find_next_node_browser_item(browser_item_uri, browser_item, nodes, node_index, useVST2CustomFolder)
        return browser_item


    def _find_next_node_browser_item(self, browser_item_uri, browser_item, nodes, node_index, useVST2CustomFolder):

        if node_index == len(nodes):
            return browser_item

        browser_items = browser_item.children

        if len(browser_items) == 0:
            return browser_item

        sub_nodes = nodes[:node_index+1]

        for child_browser_item in browser_items:

            child_browser_item_no_query_uri = self._remove_prefix(child_browser_item.uri, 'query:')

            # NB: For Plugins/VST folder, if custom folder is not used,
            # the 'Local' folder is hidden, so it needs to be removed from the uri
            if not useVST2CustomFolder:
                child_browser_item_no_query_uri = child_browser_item_no_query_uri.replace('Plugins#VST:Local', 'Plugins#VST')

            child_nodes = re.split('[#:]', child_browser_item_no_query_uri)

            if child_nodes == sub_nodes:
                next_node_index = node_index + 1
                return self._find_next_node_browser_item(browser_item_uri, child_browser_item, nodes, next_node_index, useVST2CustomFolder)


    def _preview_browser_item(self, msg, src):

        useVST2CustomFolder = self._checkVST2CustomFolderUse()

        browser_item = self._get_browser_item(msg, src, useVST2CustomFolder)
        if browser_item is not None:
            self._browser.preview_item(browser_item)


    def _load_browser_item(self, msg, src):

        useVST2CustomFolder = self._checkVST2CustomFolderUse()

        browser_item = self._get_browser_item(msg, src, useVST2CustomFolder)
        if browser_item is not None:
            self._browser.load_item(browser_item)


    def _get_browser_item_children(self, msg, src):
        after_child_browser_item_uri = msg[3]
        page_size = msg[4]

        useVST2CustomFolder = self._checkVST2CustomFolderUse()

        browser_item = self._get_browser_item(msg, src, useVST2CustomFolder)
        if browser_item is not None:
            children_items_json_array = []
            collect_started = False
            collected_count = 0

            if after_child_browser_item_uri == '':
                collect_started = True

            for browser_item_child in browser_item.children:
                if collect_started and collected_count < page_size:
                    browser_item_child_json_str = self._browser_item_to_json_str(browser_item_child)
                    children_items_json_array.append(browser_item_child_json_str)
                    collected_count += 1

                if after_child_browser_item_uri == browser_item_child.uri:
                    collect_started = True

            chunked_list = self._split_list_into_chunks(children_items_json_array, self._max_items_per_chunk)
            for chunk in chunked_list:
                self.send('/live/browser/browser_item_children', *chunk)


    def _browser_item_to_json_str(self, browser_item):

        has_children = len(browser_item.children) > 0

        browser_item_mjson = {
            'name': browser_item.name,
            'uri': browser_item.uri,
            'source': browser_item.source,
            'isDevice': browser_item.is_device,
            'isFolder': browser_item.is_folder,
            'isLoadable': browser_item.is_loadable,
            'hasChildren': has_children
        }
        browser_item_json = microjson.to_json(browser_item_mjson)
        return str(browser_item_json)

    def _checkVST2CustomFolderUse(self):
        plugins_browser_items = self._browser.plugins.children
        for plugin_browser_item in plugins_browser_items:
            if plugin_browser_item.name == 'VST':
                for vst_browser_item_child in plugin_browser_item.children:
                    if vst_browser_item_child.name == 'Custom':
                        return True
        return False


    def _stop_preview(self, msg, src):
        self._browser.stop_preview()


    def _split_list_into_chunks(self, l, n): 
        for i in range(0, len(l), n):  
            yield l[i:i + n]


    def _remove_prefix(self, text, prefix):
        return text[text.startswith(prefix) and len(prefix):]