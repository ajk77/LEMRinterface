"""
WebEmrGui/eye_tracking_scripts.py
version 1.0
package github.com/ajk77/LEMRinterface
Created by AndrewJKing.com|@andrewsjourney

This file is for controlling an eye-tracking peripheral. 

---LICENSE---
This file is part of LEMRinterface

LEMRinterface is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or 
any later version.

LEMRinterface is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with LEMRinterface.  If not, see <https://www.gnu.org/licenses/>.
"""
from gazesdk import *
import time
import sys
import os.path
from os import walk
import numpy as np

t = False

if os.path.isdir("../../models/"):
    local_dir = os.getcwd() + "/../../models/"

out_file = None


class ErrorDistribution:
    """
    Code for each error distribution. Each eye stream data point has its own based off of the x,y coordinate.
      Each inner cell is organized in a 1 dimensional list.
    """
    def __init__(self, distribution, x, y):
        self.pos = [y-50, x-50, y+50, x+50]
        self.D = distribution

    def overlap(self, pos):
        try:
            if self.pos[0] > pos[2] or self.pos[1] > pos[3] or self.pos[2] < pos[0] or self.pos[3] < pos[1]:
                return False
            else:
                return True
        except IndexError:
            print '***caught def overlap IndexError ' + str(pos) + '***'
            return False

    def calc_overlap(self, pos):
        cols = [-1, -1]
        rows = [-1, -1]
        for i in range(100):
            if cols[0] == -1:
                if self.pos[1] + i >= pos[1]:
                    cols[0] = i
            elif cols[1] == -1:
                if self.pos[1] + i > pos[3]:
                    cols[1] = i-1
            if rows[0] == -1:
                if self.pos[0] + i >= pos[0]:
                    rows[0] = i
            elif rows[1] == -1:
                if self.pos[0] + i > pos[2]:
                    rows[1] = i-1
        if cols[0] == -1:
            cols[0] = 0
        if cols[1] == -1:
            cols[1] = 100
        if rows[0] == -1:
            rows[0] = 0
        if rows[1] == -1:
            rows[1] = 100

        return self.D[rows[0]:rows[1], cols[0]: cols[1]].sum()


class Matrix:
    """
    Matrix used for calibration
    """
    def __init__(self):
        self.An = 1.0
        self.Bn = 1.0
        self.Cn = 0.0
        self.Dn = 1.0
        self.En = 1.0
        self.Fn = 0.0

    def __str__(self):
        return "Matrix: [" + str(self.An) + ', ' + str(self.Bn) + ', ' + str(self.Cn) + ', '\
               + str(self.Dn) + ', ' + str(self.En) + ', ' + str(self.Fn) + ']'

    def calc_calibration_values(self, dir, stream_file):
        # load calibration pixelmap file to data structure
        box_start_times = []
        box_x_centers = []
        box_y_centers = []
        box_end_times = []
        cal_pixelmap_file = open(dir + 'pixelmaps/pat_calibration.txt', 'r')
        for q in range(9):
            box_start_times.append(float(cal_pixelmap_file.readline()[3:]))
            location = [int(x) for x in cal_pixelmap_file.readline().split(',')]
            box_x_centers.append(int(location[1]+(location[3]-location[1])/2))  # will be within a pixel of truth
            box_y_centers.append(int(location[0]+(location[2]-location[0])/2))
            box_end_times.append(float(cal_pixelmap_file.readline()[3:]))
            discard = cal_pixelmap_file.readline()
            del q, discard
        cal_pixelmap_file.close()

        # find error in calibration file
        current_box = 0  # the current red box number
        x_es_points = []  # list of eye_stream points for a red box
        y_es_points = []
        x_medians = []  # list of median eye_steam points for each red box
        y_medians = []
        es_file = open(dir + 'eye_stream/' + stream_file, 'r')
        # process eye_stream file line by line
        for line in es_file:
            x, y, time = [float(x) for x in line.rstrip().split(',')]
            x = x * 1920
            y = y * 1080

            if time < box_start_times[current_box]:
                continue  # tracking before interaction started
            elif time >= box_end_times[current_box]:
                # calc and store eye_stream points medians
                if x_es_points:
                    x_medians.append(np.median(np.asarray(x_es_points)))
                    y_medians.append(np.median(np.asarray(y_es_points)))
                else:
                    x_medians.append(box_x_centers[current_box])
                    y_medians.append(box_y_centers[current_box])
                    print "***WARNING this calibration box might not have worked: " + str(current_box) + " ***"
                # reset params
                x_es_points = []
                y_es_points = []
                current_box += 1  # move to next red test box
                if current_box == 9:
                    break
            elif x == 0.0 or y == 0.0:
                continue  # eyes were off screen EyeX
            elif x == -1.0 or y == -1.0:
                continue  # eyes were off screen X2-30
            else:   # found tracking within interaction
                curr_x_e = box_x_centers[current_box] - x
                curr_y_e = box_y_centers[current_box] - y
                if abs(curr_x_e) > 100 or abs(curr_y_e) > 100:
                    continue  # skip values way out of range
                x_es_points.append(x)
                y_es_points.append(y)
        es_file.close()

        # set_calibration_matrix
        x = np.row_stack(box_x_centers)
        y = np.row_stack(box_y_centers)
        x_ = np.asarray(x_medians)
        y_ = np.asarray(y_medians)

        try:
            # calc values
            o = np.ones((x_.size, 1))
            a_ = np.column_stack((x_, y_, o))
            a_t = np.transpose(a_)
            pim = np.dot(np.linalg.inv(np.dot(a_t, a_)), a_t)  # pseudo-inverse matrix
            v_xs = np.dot(pim, x)
            v_ys = np.dot(pim, y)

            # set values
            self.An = v_xs[0, 0]
            self.Bn = v_xs[1, 0]
            self.Cn = v_xs[2, 0]
            self.Dn = v_ys[0, 0]
            self.En = v_ys[1, 0]
            self.Fn = v_ys[2, 0]
        except np.linalg.linalg.LinAlgError:
            print '***caught def calc_calibration_values LinAlgError***'

        return

    def get_fixed_display_point(self, x, y):
        new_x = ((self.An * x) + (self.Bn * y) + self.Cn)
        new_y = ((self.Dn * x) + (self.En * y) + self.Fn)
        return int(round(new_x)), int(round(new_y))


def start_eye_stream(pat_id='0'):
    """
    Code for running eye tracker.
        ->Should be started when on LEMR home screen.
        ->Should be terminated after user unloads page of the last desired patient case.
    """
    global t
    global out_file
    # should be started before going to patient case.
    # could look to see if there is a calibration code bindings
    try:
        url = get_connected_eye_tracker()
        t = Tracker(url)
        t.run_event_loop()
        out_file = open(local_dir + 'eye_stream/'+pat_id+'_'+str(time.time()) + '.txt', 'w+')
        t.connect()
        t.start_tracking()

        try:
            while True:
                curr_time = time.time()
                data = t.event_queue.get()
                left_x = data.left.gaze_point_on_display_normalized[0]
                right_x = data.right.gaze_point_on_display_normalized[0]
                left_y = data.left.gaze_point_on_display_normalized[1]
                right_y = data.right.gaze_point_on_display_normalized[1]
                if left_x != 0.0:
                    if right_x:
                        x = (left_x+right_x)/2.0
                    else:
                        x = left_x
                else:
                    x = right_x
                if left_y != 0.0:
                    if right_y:
                        y = (left_y+right_y)/2.0
                    else:
                        y = left_y
                else:
                    y = right_y

                out_file.write(str(x)+','+str(y)+','+str(curr_time)+'\n')

                t.event_queue.task_done()
        except KeyboardInterrupt:
            print 'eye tracking terminated'

        t.stop_tracking()
        t.disconnect()
        out_file.close()

        t.break_event_loop()
    except TrackerError:
        print '***cannot connect to the eye tracker***'
        return False
    return True


def stop_eye_stream():
    """
    Stops the eye stream output and closes file.
    """
    global t
    global out_file

    try:
        if t:
            t.stop_tracking()
            t.disconnect()
            out_file.close()
            t.break_event_loop()
            t = False
    except TrackerError:
        print '***TrackerError caught at t.stop_tracking***'
    return


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # code that iterates through the different mapping methods and parameters
        print 'no studies coded for analysis'
    else:
        start_eye_stream()
    sys.exit(0)
