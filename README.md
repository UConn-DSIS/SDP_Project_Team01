## SDP Project Team01
This is the repo for UConn SoC Project Team01: Benchmarking Large Language Models for Time Series Analysis
## Setup:
1. Clone this repo
1. Create a python virtual environment
1. Pip install –r requirements.txt
1. Download Grafana [locally](https://grafana.com/grafana/download "@embed")
1. Enable anonymous authentication
	1. Locate the file defaults.ini. This is NOT in the files in this repo! It contains the default settings for Grafana and will be wherever Grafana is installed on your machine
	1. Search for the section “[auth.anonymous]”.
	1. Set the variable enabled to true.
	1. Read more about anonymous access [here](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/anonymous-auth/ "@embed") if needed.
1. Configure the app to gain anonymous authentication
	1. On Grafana, Go to Administration → Users and Access → Service Accounts
	1. Click “Add service account”
	1. Set the display name to whatever you want
	1. Set the role to editor or admin. This is so the app can make changes to Grafana.
	1. Click “+ Add service token”
	1. Optionally set a display name
	1. Make sure “No expiration” is selecte1. If not, you’ll eventually need to replace it
	1. Click generate token
	1. Copy the generated token and store it somewhere safe! You will not be able
	to view it again
	1. In backend.py, search for TODO and set the variable token to the one you generated.
	1. Read more about service accounts [here](https://grafana.com/docs/grafana/latest/administration/service-accounts/ "@embed") if needed.
1. Configure the Infinity data source to handle CSV data
	1. On Grafana, go to Data sources
	1. Click “+ Add new data source”
	1. Search and select “Infinity”
	1. Click “Save & test”. You shouldn’t need to change any configuration settings
1. Configure password and username
	1. At the top of the post() function in backend.py, set the password and username variables to whatever you set them as on local Grafana
	1. By default, they are both “admin”

## User Guide (Chronos):
1. Run app.py. This file contains the Flask functionality.
1. Navigate to http://121.0.0.1:5000/.
1. Click the “Generate with Chronos” tab
1. Specify your time and target data fields exactly as they are spelled in your CSV. Typos and incorrect cases will cause errors. These fields are required.
1. Specify the prediction lengt1. You may choose any integer from 1 to 61. It is set to 12 by default when left blank. We have 64 as the maximum because that is the default prediction length limit on Chronos. There is a way to disable this, but there wasn’t a reason to for this app. This field is optional.
1. Specify the number of windows you would like your dataset to be divided into. Chronos has a sequence maximum of 512 values, but the datasets users submit can and often are much longer. As such, we divide the given dataset into smaller partitions to allow for multiple forecasting examples on one dataset. The default is set to 10 windows when left blank. In this scenario, a dataset is divided into 10 smaller slices with their own individual forecasts. This field is optional
1. Select the Chronos model you would like to us1. You can choose from any of the original models, but it is recommended to use one of the BOLT models, as they are newer, faster, and more accurat1. We have BOLT Tiny set as the default because it is the most efficient and least computationally expensive model.
1. Upload data your dat1. We have options for users to upload a file from local devices, from a URL, or by pasting inline text. We also have options for multiple types (CSV, XML, etc). However, we only verified that a CSV uploaded from the user’s computer works. You can optionally specify a delimiter for CSV.
1. Once set, the button “Generate Forecasts” appears. Clicking this button runs the Chronos backend.
1. Once completed, you are brought to a new pag1. Clicking the link “Click here to view results in Grafana” takes the user to a Grafana snapshot. In the top panel, a time series visualization graph plots the actual data the user uploaded against the high, median, and low forecasts. The table below shows the numerical values that correspond to the graph.
1. On the Grafana tab, there are buttons that read “Move window left” and “Move window right”. Initially, Grafana displays the first window. Clicking the move right button updates the data in Grafana to display the next window. Moving left allows you to go return to previous windows. On Grafana, the original data will no longer be displaye1. If the range is far away enough, Grafana will have a “Zoom to data option”. If not, the webpage also displays the updated time bounds. The user can manually set them in the display.


## General Notes:
+ This app only runs locally! We did not have time to deploy this on the clou1. To do this, consider a platform like Amazon Web Services or Heroku.
+ There is a difference between Grafana Cloud and local Grafan1. Any account you make on the cloud is not tied to the settings of your local Grafana
+ To let your data be viewable in Grafana, the app must be running!
+ If the app is running and everything is configured correctly, you may still get an unauthorized error if you have not signed into local Grafana recently. All you need to do to view the data is click sign in.
+ Since we set this app up across our local devices (both Macs and Windows), there may be some inconsistencies in what libraries function. Feel free to update requirements.txt as needed.
 
## Chronos Backend Notes:
+ Running the Chronos backend generates several text files that are necessary for the functionality of the sliding windows:
	+ end_times.txt: contains the ending time bound for each window. The first time is for the first window, the second us for the second, and so on.
	+ input_path.txt: contains the path to the original input dataset
	+ input_step.txt: contains 1) the starting index the app references in the dataset per each window, 2) the step amount between each window, 3) the prediction length, and 4) the delimiter
	+ output_path: contains general path to output files
	+ start_times.txt: contains the starting time bound for each window
	+ window.txt: contains 1) the current window and 2) the total number of windows
