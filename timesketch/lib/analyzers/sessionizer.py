"""Sessionizing sketch analyzer plugin."""

from __future__ import unicode_literals

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager

class SessionizerSketchPlugin(interface.BaseSketchAnalyzer):
    """Sessionizing sketch analyser. All events in sketch with id sketch_id
    are grouped in sessions based on the time difference between them. Two
    consecutive events are in the same session if the time difference between
    them is less or equal then max_time_diff_micros"""

    NAME = 'sessionizer'
    # TODO max_time_diff_micros should be configurable
    max_time_diff_micros = 300000000
    query = '*'
    session_type = 'all_events_session'

    def run(self):
        """Entry point for the analyzer. Allocates each event a session_id
        attribute.
        Returns:
            String containing the number of sessions created.
        """
        return_fields = ['timestamp']

        # event_stream returns an ordered generator of events (by time)
        # therefore no further sorting is needed.
        events = self.event_stream(query_string=self.query,
                                   return_fields=return_fields)
        session_num = 0
        start_timestamp = None

        try:
            first_event = next(events)
            last_timestamp = first_event.source.get('timestamp')
            start_timestamp = last_timestamp
            session_num = 1
            self.annotateEvent(first_event, session_num)

            for event in events:
                curr_timestamp = event.source.get('timestamp')
                if curr_timestamp - last_timestamp > self.max_time_diff_micros:
                    #new session
                    self.sketch.add_session(self.session_type, session_num,
                                            start_timestamp, last_timestamp)
                    start_timestamp = curr_timestamp
                    session_num += 1
                self.annotateEvent(event, session_num)
                last_timestamp = curr_timestamp

        except StopIteration:
            pass

        if start_timestamp is not None:
            self.sketch.add_session(self.session_type, session_num,
                                    start_timestamp, last_timestamp)

        return ('Sessionizing completed, number of session created:'
                ' {0:d}'.format(session_num))

    def annotateEvent(self, event, session_num):
        event.add_attributes({self.session_type: str(session_num)})
        event.commit()

manager.AnalysisManager.register_analyzer(SessionizerSketchPlugin)
