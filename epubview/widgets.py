import logging

from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import WebKit2


class EpubWebView(WebKit2.WebView):

    __gsignals__ = {
        'touch-change-page': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE,
                              ([bool])), }

    def __init__(self, only_to_measure=False):
        WebKit2.WebView.__init__(self)
        self._only_to_measure = only_to_measure
        return

        def nt(view, new):
            logging.error('notify::title %r' % (self.props.title))
        self.connect('notify::title', nt)

    def load_file(self, filename):
        self.load_uri('file://' + filename)

    def get_file(self):
        return self.get_uri().replace('file://', '')

    def setup_touch(self):
        self.get_window().set_events(
            self.get_window().get_events() | Gdk.EventMask.TOUCH_MASK)
        self.connect('event', self.__event_cb)

    def __event_cb(self, widget, event):
        if event.type == Gdk.EventType.TOUCH_BEGIN:
            x = event.touch.x
            view_width = widget.get_allocation().width
            if x > view_width * 3 / 4:
                self.emit('touch-change-page', True)
            elif x < view_width * 1 / 4:
                self.emit('touch-change-page', False)

    def get_page_height(self, page_height_cb):
        '''
        Gets height (in pixels) of loaded (X)HTML page.

        WebKit2 4.0 API does not expose the height, or we have not
        found where it does, so we use JavaScript to read it from the
        document.

        JavaScriptCore is not implemented for Python GI API yet, so we
        use the document title as return path for the value.
        '''
        hide_scrollbar_js = ''
        if self._only_to_measure:
            hide_scrollbar_js = \
                'document.documentElement.style.overflow = "hidden";'

        oldtitle = self.get_title()

        js = """
            document.documentElement.style.margin = "50px";
            if (document.body == null) {
                document.title = 0;
            } else {
                %s
                document.title = Math.max(document.body.scrollHeight,
                    document.body.offsetHeight,
                    document.documentElement.clientHeight,
                    document.documentElement.scrollHeight,
                    document.documentElement.offsetHeight);
            };
        """ % hide_scrollbar_js

        def get(view, result):
            value = int(view.get_title())
            view.run_javascript('document.title=%s;' % oldtitle)
            page_height_cb(value)

        self.run_javascript(js, None, get)

    def add_bottom_padding(self, incr):
        '''
        Adds incr pixels of padding to the end of the loaded (X)HTML page.
        This is done via javascript at the moment
        '''
        js = """
            var newdiv = document.createElement("div");
            newdiv.style.height = "%dpx";
            document.body.appendChild(newdiv);
        """ % incr
        self.run_javascript(js)

    def highlight_next_word(self):
        '''
        Highlight next word (for text to speech)
        '''
        self.run_javascript('highLightNextWord();')

    def go_to_link(self, id_link):
        self.run_javascript('window.location.href = "%s";' % id_link)

    def get_vertical_position_element(self, id_link, vertical_position_cb):
        '''
        Get the vertical position of an element, in pixels.

        JavaScriptCore is not implemented for Python GI API yet, so we
        use the document title as return path for the value.
        '''
        # remove the first '#' char
        id_link = id_link[1:]
        oldtitle = self.get_title()
        js = """
            obj = document.getElementById('%s');
            var y = 0;
            if (obj.offsetParent) {
                while (1) {
                    y += obj.offsetTop;
                    if (!obj.offsetParent) {
                        break;
                    };
                    obj = obj.offsetParent;
                };
            } else if (obj.y) {
                y += obj.y;
            };
            document.title=y;""" % id_link

        def get(view, result):
            value = int(self.get_title())
            self.run_javascript('document.title=%s;' % oldtitle)
            vertical_position_cb(value)

        self.run_javascript(js, None, get)

    def move_cursor(self, ms, count):
        logging.error('move_cursor ms %r count %r' % (ms, count))
