"""
WebEmrGui/views.py
version 1.0
package github.com/ajk77/LEMRinterface
Modified by AndrewJKing.com|@andrewsjourney

This is the view processing file. 

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
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.views.decorators.csrf import ensure_csrf_cookie
from loaddata import *
from utils import load_med_maps
import time
import random
import pickle
import os.path
import threading
import imp

try:    # Option made
    imp.find_module('gazesdk')
    gaze_found = True
    from eye_tracking_scripts import start_eye_stream, stop_eye_stream
except ImportError:
    gaze_found = False
    start_eye_stream = None
    stop_eye_stream = None
    print '***Eye tracking not available on this machine***'


# Global variables
if os.path.isdir("../../models/"):
    local_dir = os.getcwd() + "/../../models/"
active_eye_thread = False
eye_thread = None
# ilmby8


def index(request, user_id=False):
    # end existing eye tracking threads
    print request.path_info
    global active_eye_thread, eye_thread
    if active_eye_thread:
        eye_thread.stop()
        eye_thread = None
        active_eye_thread = False

    users = []
    with open(local_dir + '/evaluation_study/participant_info/participant_info.txt', 'r') as in_file:
        for line in in_file:
            if line[0] == '#':
                continue
            else:
                split_line = line.split(',')
                users.append({'name': split_line[0], 'access': split_line[1], 'count': split_line[2]})

    template = loader.get_template('WebEmrGui/home_screen.html')
    context = RequestContext(request, {
        'full': users
    })
    return HttpResponse(template.render(context))


def end_of_study(request, user_id, previous_patient_id=0):
    """
    Closes the previous cases's final pixelmap and displays completion info to participant.
     Does not need to include study_id info because it will never be navigated to unless within a study.
    """
    print request.path_info
    if user_id != 'interface_demo':
        update_participant_info(user_id, local_dir + 'evaluation_study/participant_info/')
    if previous_patient_id:  # save timestamp for leaving last patient id
        print_to_pixelmap_file(local_dir, 2, previous_patient_id, 0, str(time.time()))
        # this breaks on final case if user does not navigate to another patient to send the ending timestamp.
    return HttpResponse("<h2>You have completed all of the cases!"
                        "</h2><br><a href=http://127.0.0.1:8000/WebEmrGui/home/"+user_id+"/><button>Home</button></a>")


def loadcasedata(request):
    update_cases()
    return HttpResponse("<h2>Cases have been updated!</h2><br>"
                        "<a href=http://127.0.0.1:8000/WebEmrGui/><button>Home</button></a>")


@ensure_csrf_cookie
def eye_test(request, user_id, skip_cal=0):
    # start eye stream
    global active_eye_thread, eye_thread, gaze_found
    if active_eye_thread:
        eye_thread.stop()
        eye_thread = None
        active_eye_thread = False
    if gaze_found:
        eye_thread = EyeThread('calibration')
        eye_thread.start()
        active_eye_thread = True
    else:
        skip_cal = 1
    if user_id in ['27AKF', '27ARF']:
        skip_cal = 1

    template = loader.get_template('WebEmrGui/eye_test_template.html')
    next_case_url = find_first_case(local_dir + 'evaluation_study/participant_info/', user_id)
    if next_case_url == 'end':
        return HttpResponse("<h2>You have completed all of the cases!"
                            "</h2><br><a href=http://127.0.0.1:8000/WebEmrGui/><button>Home</button></a>")
    print next_case_url
    print '^^next case^^'
    context = RequestContext(request, {'skip_eye_cal': skip_cal, 'd_size': 10, 'next_case': next_case_url, 'user_id': user_id})
    return HttpResponse(template.render(context))


def recording(request):
    message = '```recording functionalites have been removed```'
    return HttpResponse(message)


def save_pixelmap(request):
    if request.is_ajax():
        message = "Yes, AJAX!"
        if request.method == 'POST':
            if len(request.POST.get('the_timestamp')) == 0:     # indicates that it is a notemap becasue time is ''
                print_to_notemap_file(local_dir, 0, request.POST.get('pat_id'), request.POST.get('the_pixelmap'))
            elif len(request.POST.get('the_pixelmap')) == 1:  # signifies end of interaction
                print_to_pixelmap_file(local_dir, 2, request.POST.get('pat_id'), 0, request.POST.get('the_timestamp'))
            elif len(request.POST.get('the_pixelmap')) == 0:  # signifies pixelmap before page is loaded
                print_to_pixelmap_file(local_dir, 0, request.POST.get('pat_id'), 'loading,0,0,0,0',
                                       request.POST.get('the_timestamp'))
            else:  # within an interaction
                print_to_pixelmap_file(local_dir, 0, request.POST.get('pat_id'), request.POST.get('the_pixelmap'),
                                       request.POST.get('the_timestamp'))
    else:
        message = "Not Ajax"
    return HttpResponse(message)


def save_input(request):
    if request.is_ajax():
        message = "Yes, AJAX!"
        if request.method == 'POST':
            print_to_manual_input_file(local_dir, request.POST.get('pat_id'), request.POST.get('the_timestamp'),
                                       request.POST.get('selections'), request.POST.get('rating'),
                                       request.POST.get('reason'))
    else:
        message = "Not Ajax"
    return HttpResponse(message)


def save_issue(request):
    if request.is_ajax():
        message = "Yes, AJAX!"
        if request.method == 'POST':
            print_to_issue_report_file(local_dir, request.POST.get('pat_id'), request.POST.get('the_timestamp'),
                                       request.POST.get('issue_text'))
    else:
        message = "Not Ajax"
    return HttpResponse(message)


@ensure_csrf_cookie
def detail(request, patient_id, user_id, time_cutoff=1, previous_patient_id=0):
    time_cutoff = int(time_cutoff)
    if user_id != 'first_four':  # zero is for sandbox mode. -1 is for testing/debugging
        pixelmap_saving = True
    else:
        pixelmap_saving = False

    # first check if pixelmap out_file needs to be closed
    if int(previous_patient_id) and pixelmap_saving and time_cutoff == 1:  # save timestamp for leaving last patient id
        print_to_pixelmap_file(local_dir, 2, previous_patient_id, 0, str(time.time()))
        # this breaks on final case if user does not navigate to another patient to send the ending timestamp.

    template = loader.get_template('WebEmrGui/index_3.html')
    print "New request: " + request.path_info

    # end existing eye tracking threads and start new eye tracking thread
    if user_id != 'first_four' and gaze_found:  # zero is for sandbox mode. -1 is for testing/debugging
        global active_eye_thread, eye_thread
        if active_eye_thread:
            eye_thread.stop()
            eye_thread = None
            active_eye_thread = False
        eye_thread = EyeThread(str(patient_id))
        eye_thread.start()
        active_eye_thread = True

    # open new pixelmap out_file
    if pixelmap_saving:
        print_to_pixelmap_file(local_dir, 1, patient_id, 0, 0)

    p_info_location = local_dir + 'evaluation_study/participant_info/'
    next_patient, next_view, show_highlights, highlights_only = determine_next_url(p_info_location, user_id,
                                                                                    time_cutoff, patient_id)
    current_arm = 'C'
    if time_cutoff == 1:
        first_view = True
        only_show_highlights = 'false'  # first view is always the same
        show_highlights = False  # first view is always the same
    else:
        first_view = False
        show_highlights = int(show_highlights)
        if show_highlights:
            current_arm = '1'
        if highlights_only == '1':  # depends on user
            current_arm = '2'
            only_show_highlights = 'true'
        else:
            only_show_highlights = 'false'

    record_report = 'true'

    load_dir = local_dir + 'evaluation_study/cases_t' + str(time_cutoff) + '/' + str(patient_id) + '/'

    data_fields_to_highlight = []
    if show_highlights:
        # load med mappings. catalog_display is used as machine learning names, ordered as is the longer display name
        catalog_display_dic, ordered_as_dic = load_med_maps(load_dir + 'med-display-id_to_name.txt')
        # highlights = load_highlights(path)
        with open(local_dir + 'evaluation_study/case_highlights.txt', 'r') as f:
            for line in f:
                s_line = line.rstrip().split(': ')
                if s_line[0] == str(patient_id):
                    data_fields_to_highlight = s_line[1].split(',')
                    break

        for idx, data_field in enumerate(data_fields_to_highlight):
            if data_field in catalog_display_dic.keys():
                data_fields_to_highlight[idx] = catalog_display_dic[data_field]

    demographics_dict = pickle.load(open(load_dir + 'demographics.p', 'rb'))
    global_time = pickle.load(open(load_dir + 'global_time.p', 'rb'))
    lab_info = pickle.load(open(load_dir + 'labs.p', 'rb'))
    vital_info = pickle.load(open(load_dir + 'vitals.p', 'rb'))
    group_order_labs = pickle.load(open(local_dir + 'evaluation_study/tests/group_order_labs.p', 'rb'))
    group_info = pickle.load(open(local_dir + 'evaluation_study/tests/group_membership.p', 'rb'))
    global_params = pickle.load(open(local_dir + 'evaluation_study/tests/global_params.p', 'rb'))
    display_names = pickle.load(open(local_dir + 'evaluation_study/tests/display_names.p', 'rb'))
    recent_results = pickle.load(open(load_dir + 'recent_results.p', 'rb'))
    med_info = pickle.load(open(load_dir + 'case_test_meds.p', 'rb'))
    display_med_names = pickle.load(open(load_dir + 'display_med_names.p', 'rb'))
    med_routes = pickle.load(open(load_dir + 'med_routes.p', 'rb'))
    routes_mapping = pickle.load(open(load_dir + 'routes_mapping.p', 'rb'))
    procedure_dict = pickle.load(open(load_dir + 'procedures.p', 'rb'))
    micro_report_dict = pickle.load(open(load_dir + 'micro_report.p', 'rb'))
    op_note = pickle.load(open(load_dir + 'OP.p', 'rb'))
    rad_note = pickle.load(open(load_dir + 'RAD.p', 'rb'))
    ekg_note = pickle.load(open(load_dir + 'EKG.p', 'rb'))
    other_note = pickle.load(open(load_dir + 'other_notes.p', 'rb'))
    pgn_note = pickle.load(open(load_dir + 'PGN.p', 'rb'))
    hp_note = pickle.load(open(load_dir + 'HP.p', 'rb'))

    context = RequestContext(request, {
        'first_view': first_view,
        'global_time': global_time,
        'next_patient': next_patient,
        'next_view': next_view,
        'user_id': str(user_id),
        'demographics_dict': demographics_dict,
        'OP_note': op_note,
        'RAD_note': rad_note,
        'EKG_note': ekg_note,
        'other_note': other_note,
        'PGN_note': pgn_note,
        'HP_note': hp_note,
        'micro_report_dict': micro_report_dict,
        'lab_info': lab_info,
        'vital_info': vital_info,
        'group_info': group_info,
        'global_display_info': global_params,
        'labs_to_highlight': data_fields_to_highlight,
        'only_show_highlights': only_show_highlights,
        'arm': current_arm,
        'display_names': display_names,
        'group_order': group_order_labs,
        'procedures': procedure_dict,
        'recent': recent_results,
        'med_info': med_info,
        'med_routes': med_routes,
        'routes_mapping': routes_mapping,
        'display_med_names': display_med_names,
        'record_report': record_report
    })
    return HttpResponse(template.render(context))


class EyeThread(threading.Thread):
    def __init__(self, pat_id):
        threading.Thread.__init__(self)
        self.pat_id = pat_id

    def run(self):
        print '...starting pat ' + str(self.pat_id)
        result = start_eye_stream(self.pat_id)
        if not result:
            global gaze_found
            gaze_found = False

    def stop(self):
        print '...stopping' + str(self.pat_id)
        stop_eye_stream()

