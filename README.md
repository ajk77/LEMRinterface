# LEMRinterface

A Learning Electronic Medical Record (LEMR) interface. This code can be used for Electronic Medical Record Research.

## Getting Started

First, have a look in the screenshots directory to become familiar with the interface design. 

This code may benefit those interested in either conducting electronic medical record research or those interested in
using eye-tracking on a web-based interface (see https://github.com/ajk77/PatientPyFeatureSelection).

### Prerequisites

Bitnami Django (https://bitnami.com/stack/django/installer).</ br>
MySQl database or equivalent.</ br>
Access to de-identified patient data, such as MIMIC (https://mimic.physionet.org/).

### Installing

After downloading this repositiory, perform the folowing steps:</ br>
1. Database connections
In "/LEMRinterface/WebEmrProject/settings.py" updated DATABASES{} to reflect your databased. </ br>
2. Set SECRET_Key
In "/LEMRinterface/WebEmrProject/settings.py" set you own SECRET_KEY.</ br>
3. Update database definitions in "/LEMRinterface/WebEmrGui/models.py" to reflect the organization of your patient
data.</ br>
4. Create supporting file structure
Move the models directory to two levels up in your directory hierarchy (i.e. "../../models/").</ br>
5. Read README files in models directory. These give give you an idea of the supporting files you must create.</ br>
6. Update ""/LEMRinterface/WebEmrGui/loaddata.py" to reflect the organization of your patient data.</ br>
7. Dig in and debug as errors come up. It may take a significant amount of ETL coding. I recommend starting small. See
if you can get the interface to load with no patient data. Then get it to load with just patient demographic data.

#### Note

Viewing (https://github.com/ajk77/PatientPy) and (https://github.com/ajk77/EyeBrowserPy) may be helpful.

### Deployment

open Bitnami Django Stack Environment with use_djangostack.bat</ br>
cd into your project directory</ br>
enter>python manage.py runserver</ br>
open web browser to http://127.0.0.1:8000/WebEmrGui/

#### Note

The LEMRinterface in meant to run in full screen mode on a 1920 x 1080 resolution monitor. Responsive html is not
currently support.

## Versioning

Version 1.0. For the versions available, see https://github.com/ajk77/LEMRinterface

## Authors

Andrew J King - Doctoral Candidate (at time of creation)<br />
Shyam Visweswaran - Principal Investigator<br />
Gregory F Cooper - Doctoral Advisor

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

## Acknowledgments

* Harry Hochheiser
* Gilles Clermont
* Milos Hauskrecht