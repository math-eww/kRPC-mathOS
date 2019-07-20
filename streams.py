import krpc

class Streams:
    def __init__(self, conn):
        print("Initializing streams")
        self.conn = conn
        self.vessel = self.conn.space_center.active_vessel
        self.streams = {}
        self._stream_strings = {
            'mean_altitude':        [self.vessel.flight(self.vessel.orbit.body.reference_frame), 'mean_altitude'],
            'surface_altitude':     [self.vessel.flight(self.vessel.orbit.body.reference_frame), 'surface_altitude'],
            'apoapsis_altitude':    [self.vessel.orbit, 'apoapsis_altitude'],
            'periapsis_altitude':   [self.vessel.orbit, 'periapsis_altitude'],
            'srf_speed':            [self.vessel.flight(self.vessel.orbit.body.reference_frame), 'speed'],
            'orb_speed':            [self.vessel.flight(self.vessel.orbit.body.non_rotating_reference_frame), 'speed'],
            'dynamic_pressure':     [self.vessel.flight(self.vessel.orbit.body.reference_frame), 'dynamic_pressure'],
            'ut':                   [self.conn.space_center, 'ut'],
            'vertical_speed':       [self.vessel.flight(self.vessel.orbit.body.reference_frame), 'vertical_speed'],
            'horizontal_speed':     [self.vessel.flight(self.vessel.orbit.body.reference_frame), 'horizontal_speed'],
        }
    
    def add_stream(self, source, stream, name):
        self.streams[name] = self.conn.add_stream(getattr, source, stream)
        return self.streams[name]
    
    def remove_stream(self, stream):
        self.streams[stream].remove()
        del self.streams[stream]
    
    def remove_all_streams(self):
        print("Removing all streams", len(self.streams))
        # self.print_streams()
        for stream in self.streams:
            if self.streams[stream]:
                self.streams[stream].remove()
            # self.remove_stream(stream)
        self.streams = {}
    
    def get_stream(self, stream):
        if stream in self.streams:
            return self.streams[stream]
        elif stream in self._stream_strings:
            return self.add_stream(self._stream_strings[stream][0],self._stream_strings[stream][1],stream)
    
    def create_stream(self, stream):
        if hasattr(self.streams,stream):
            return True
        elif stream in self._stream_strings:
            self.add_stream(self._stream_strings[stream][0],self._stream_strings[stream][1],stream)
            return True
        else:
            return False
    
    def get_all_streams(self):
        return self.streams
    
    def get_stream_data(self, stream):
        return self.get_stream(stream)()

    def print_streams(self):
        for stream in self.streams:
            print("{} ({})".format(stream, self.streams[stream]))



if __name__ == '__main__':
    import time
    conn = krpc.connect(name='mathos:main')
    _Streams = Streams(conn)
    while True:
        _stream = _Streams.get_stream('mean_altitude')
        print(_stream())
        print(_stream)
        _same_stream = _Streams.get_stream('mean_altitude')
        print(_same_stream())
        print(_same_stream)
        _Streams.print_streams()
        time.sleep(1)