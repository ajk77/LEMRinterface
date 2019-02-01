import time
import os.path
import sounddevice as sd
import soundfile as sf
from multiprocessing import Queue

running = True

if os.path.isdir("../../models/"):
    local_dir = os.getcwd() + "/../../models/"


class AudioRecorder:

    def __init__(self, pat_id):
        self.filename = local_dir + 'audio_recordings/' + pat_id+'_'+str(time.time()) + '.wav'
        self.channels = 1
        self.device_info = sd.query_devices(None, 'input')
        self.samplerate = int(self.device_info['default_samplerate'])
        self.q = Queue()
        self.running = False
        self.finished = False

    def start_audio_recording(self):
        """
        Code for running audio recordings
        """
        self.running = True
        try:
            def callback(indata, frames, c_time, status):
                """This is called (from a separate thread) for each audio block."""
                if status:
                    print(status)
                self.q.put(indata.copy())
                del frames, c_time

            # Make sure the file is opened before recording anything:
            with sf.SoundFile(self.filename, mode='x', samplerate=self.samplerate, channels=self.channels) as out_file:
                with sd.InputStream(samplerate=self.samplerate, channels=self.channels, callback=callback):
                    while True:
                        out_file.write(self.q.get())
                        if not self.running:
                            return
        except (IOError, KeyboardInterrupt) as e:
            print '***recording exception raised***'
            del e
        finally:
            self.finished = True
            print '<<< recording finished >>>'
        return

    def stop_audio_recording(self):
        """
        Stops and saves the audio recording
        """
        self.running = False

        return

    def status_audio_recording(self):
        return self.finished
