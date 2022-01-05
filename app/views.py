from pandas.io import json
from app import app
from flask import render_template, request, redirect, make_response, jsonify, send_from_directory, current_app
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import mmt_functions as mf
import pandas as pd
import datetime
import time
import os

app.config["UPLOAD_FOLDER"] = "static/generated_data/"

@app.route('/')
def index():
    return render_template('sl/index.html')


@app.route("/roster_compare", methods=["GET", "POST"])
def roster_compare():

    if request.method == "POST":
        if request.files["ecase_roster"].filename != "" and request.files["rosterOn_roster"].filename != "":

            eCase_file = pd.read_csv(request.files["ecase_roster"])
            rosterOn_file = pd.read_csv(request.files["rosterOn_roster"])

            eCase_file = mf.rosterClean(eCase_file)
            rosterOn_file = mf.rosterOnClean(rosterOn_file)

            output_file = mf.rosterRosterCheck(eCase_file, rosterOn_file[0])

            return render_template("sl/roster_app/roster_compare.html", output_file=output_file, missing_clients=rosterOn_file[1], missing_staff=rosterOn_file[2])
        else:
            status_text = "Please make sure you've entered the correct files"

            return render_template("sl/roster_app/roster_compare.html", status_text=status_text)

    return render_template('sl/roster_app/roster_compare.html')


@app.route('/progress_note', methods=["GET", "POST"])
def progress_note():

    return render_template('sl/prog_note_app/prog_note_check.html')


@app.route('/progress_note_result', methods=['GET', 'POST'])
def progress_note_result():

    if request.method == "POST":
        if request.files['roster_file'].filename != "" and request.files['prog_note_file'].filename != "":

            cctr = request.form["cctr"]

            roster_file = pd.read_csv(
                request.files["roster_file"])
            prog_note_file = pd.read_csv(request.files["prog_note_file"])

            roster_file = roster_file[~roster_file["ProgramType"].str.contains("Group")]
            roster_file = roster_file[~roster_file["ProgramType"].str.contains("2 to 1")]

            roster_file = mf.rosterClean(roster_file, cctr)
            prog_note_file = mf.cleanNotes(prog_note_file)

            roster_file = mf.progressNoteCheck(roster_file, prog_note_file)

            today = datetime.date.today()
            roster_file = roster_file = roster_file[roster_file["RosterStartDateTime"] <= pd.to_datetime((
                datetime.date.today() - datetime.timedelta(days=1)))]

            binu_reminders = roster_file[roster_file["ValidProgNoteComplete"] == "Missing"]
            date_today = datetime.datetime.now().strftime('%y%m%d_%H%M%S')
            binu_reminders.to_csv(
                f'app/static/data_files/binu_reminders/binu_reminders_{date_today}.csv')

            roster_file = roster_file[roster_file["ValidProgNoteComplete"] != "Accepted"]
            roster_file = roster_file.sort_values("ValidProgNoteComplete")
            roster_file['ServiceDate'] = roster_file['RosterStartDateTime'].apply(
                lambda sd: sd.strftime('%d/%m/%Y'))

            roster_file.to_csv("app/static/data_files/binu_reminders/latest_reminders.csv")

            return render_template('sl/prog_note_app/prog_note_results.html', roster=roster_file)
        else:
            status_text = "Please select all three files"
            return render_template(request.url, status_text=status_text)
    else:
        return redirect('/progress_note')


@ app.route('/vehicle_booking', methods=["GET", "POST"])
def vehicle_booking():

    if request.method == "POST":
        if request.files["ecase_roster"] != "":

            ecase_roster = pd.read_csv(request.files["ecase_roster"], delimiter="\t")

            ecase_roster = mf.carBookings(ecase_roster)

            return render_template("sl/vehicle_booking_app/vehicle_booking.html", bookings=ecase_roster[0], missing=ecase_roster[1])

        return render_template("sl/vehicle_booking_app/vehicle_booking.html")

    return render_template("sl/vehicle_booking_app/vehicle_booking.html")


@ app.route('/pv_logsheet', methods=["GET", "POST"])
def pv_logsheet():

    if request.method == "POST":
        if request.files["prog_note"].filename != "":

            prog_note = pd.read_csv(request.files["prog_note"])

            prog_note = mf.cleanNotes(prog_note)

            # I should probably create a whole new function in mmt_functions
            # for the below code

            # Exclude anyone who has indicate Fleet or House Vehicle usage
            # as they should not be claiming mileage
            prog_note = prog_note[prog_note["Vehicle"] != "F"]
            prog_note = prog_note[prog_note["Vehicle"] != "H"]

            # Excluding under 18's
            # First converting Service Date and DOB to datetime
            # Under 18 should be based on the age of the client at the time of service
            prog_note["StartDate"] = pd.to_datetime(prog_note["StartDate"])
            prog_note["DOB"] = pd.to_datetime(prog_note["DOB"], format="%Y-%m-%d")
            prog_note["Age"] = (prog_note["StartDate"] - prog_note["DOB"]).astype("timedelta64[Y]")
            prog_note = prog_note[prog_note["Age"] >= 18]


            # Excluded anyone who has travelled 0 Km
            prog_note = prog_note[prog_note["Kms Travelled"].astype(str) != "0"]

            # Exclude anyone who has not indicated Kms
            prog_note = prog_note[prog_note["Kms Travelled"].astype(str) != ""]

            # Create an output DataFrame containing the relevant Columns
            output_file = prog_note[["Author", "ClientName", "StartDateTime", "EndDateTime", "Kms Travelled", "Notes"]]

            # Create filename
            time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pv_check/pv_report_{time}.csv"

            # Create CSV report to be downloaded
            output_file.to_csv(f"app/static/generated_data/{filename}")

            return render_template("sl/logsheet_app/logsheet_report.html", filename=filename)

        return redirect("/pv_logsheet")

    return render_template("sl/logsheet_app/logsheet_report.html")


@ app.route('/budget', methods=["GET", "POST"])
@ app.route('/budget/', methods=["GET", "POST"])
def budget():
    return render_template('sl/budget_app/budget_index.html')


@ app.route('/budget/result', methods=["GET", "POST"])
def budget_result():

    if request.method == "POST":
        if request.files['billed'].filename != "" and request.files['budget'].filename != "" and request.files['scheduled'].filename != "":

            print('computing data')

            cctr = request.form["cctr"]

            billedFile = request.files["billed"]
            budgetFile = request.files["budget"]
            scheduledFile = request.files["scheduled"]

            return_file = mf.budgetCheck(
                billedFile, budgetFile, scheduledFile, cctr)

            ndis_codes = pd.read_csv(
                'app/static/data_files/mentoring_codes.csv')
            list_of_codes = ndis_codes['Support Item Number'].to_list()

            # read in all necessary codes and add to DataFrame that gets passed to results
            return render_template("sl/budget_app/budget_result.html", return_file=return_file, ndis_file=list_of_codes)
        else:
            status_text = "Please select all three files"
            return render_template('sl/budget_app/budget_index.html', status_text=status_text)

    return render_template('sl/budget_app/budget_index.html')

@app.route("/billing_report", methods=["GET", "POST"])
def billing_report():

    if request.method == "POST":

        start_time = time.time()

        if request.files['roster_file'].filename != "" and request.files['prog_file'].filename != "":

            cctr = request.form["cctr"]
            roster_file = pd.read_csv(request.files["roster_file"])
            #charge_file = pd.read_csv(request.files["charge_file"])
            prog_file = pd.read_csv(request.files["prog_file"])

            roster_file = mf.rosterClean(roster_file, cctr)
            #roster_file = mf.addChargeDuration(roster_file, charge_file)
            prog_file = mf.cleanNotes(prog_file)
            roster_file = mf.billingStatus(roster_file, prog_file)

            return_file = mf.billingStatusReport(roster_file)
            
            end_time = time.time()

            print(end_time-start_time)

            return render_template("sl/billing_report_app/billing_report.html", return_file=return_file)

    return render_template("sl/billing_report_app/billing_report.html")

@app.route('/admin', methods=["GET", "POST"])
def admin():

    if request.method == "POST":
        
        if request.files['upload_file'].filename != "":

            if request.form['data_select'] == 'staff_data':
                staff_data = pd.read_csv(request.files['upload_file'])

                def create_full_name(df):
                    return f"{df['FirstName']} {df['LastName']}"

                staff_data["FullName"] = staff_data.apply(create_full_name, axis=1)
                staff_data.to_csv("app/static/data_files/staff_details.csv", index=False)
                msg = "Staff Details were succesfully updated."
            elif request.form['data_select'] == 'rosteron_data':
                rosteron_data = pd.read_csv(request.files['upload_file'])
                rosteron_data.to_csv("app/static/data_files/minda_clients.csv", index=False)
                msg = "RosterOn Lookup Data was successfully updated."
            else:
                msg = "Sorry. Upload unsuccesful, please try and again."

            return render_template("sl/admin_app/admin.html", msg=msg)

    return render_template("sl/admin_app/admin.html")

# APIs
@app.route('/budget/ndis_codes', methods=["GET"])
def ndis_codes():

    if request.method == "GET":

        ndis_codes = pd.read_csv(
            'app/static/data_files/mentoring_codes.csv', header=None, index_col=0).to_dict()

        res = make_response(jsonify(ndis_codes))

        return res

@app.route('/progress_note_result/send_bulk', methods=["POST"])
def bulk_email():

    if request.method == "POST":

        user = request.get_json(force=True)

        smtp = smtplib.SMTP('smtp-mail.outlook.com', port='587')
        smtp.ehlo()
        smtp.starttls()
        smtp.login(user['username'], user['password'])

        reminders = pd.read_csv("app/static/data_files/binu_reminders/latest_reminders.csv")

        missing = reminders[reminders["ValidProgNoteComplete"] == "Missing"]

        time_error = reminders[reminders["ValidProgNoteComplete"] == "Time Error"]

        # Fix these emails
        # still need to test to ensure that the formatting is oks
        # add username as the sender, and df['Email'] as the reciever

        def generate_email_missing(df):
            msg = MIMEMultipart()
            msg['Subject'] = f"Missing Progress Note for {df['ClientFullName']} on {df['ServiceDate']}"
            body = f"Hi {df['AllocatedStaff']},\
                \nCould you please complete your Progress Note for {df['ClientFullName']} on {df['ServiceDate']}.\
                \nIf you believe that you have entered this Progress Note, could you please verify that you have entered the correct Service Date.\
                \nIf you have entered the incorrect Service Date by accident, could you please delete the incorrect Progress Note and re-enter it with the correct Service Date (copy-pasting the content is fine).\
                \nThank you.\
                \n\
                \nKind Regards,\
                \nCommunity Support Team Leaders"
            msg.attach(MIMEText(body))

            # first email is from address, second is to address
            smtp.sendmail('asandgren@minda.asn.au', 'asandgren@minda.asn.au', msg.as_string())

            return

        def generate_email_time_error(df):
            msg = MIMEMultipart()
            msg['Subject'] = f"Progress Note timing for {df['ClientFullName']} on {df['ServiceDate']}"
            body = f"Hi {df['AllocatedStaff']},\
                The times you've entered into the Progress Note for {df['ClientFullName']} on {df['ServiceDate']} does not match what we have in our roster.\
                \nCould you please verify that you have entered the correct timings. If you did enter the correct timings, could you please confirm the actual times you worked.\
                \nIf you entered the wrong times by accident (remember to use 24-h time), could you please delete the Progress Note and re-enter it with the correct timings (copy-pasting the content is fine).\
                \nAThank you.\
                \n\
                \nKind Regards,\
                \nCommunity Support Team Leaders"
            msg.attach(MIMEText(body))

            # first email is from address, second is to address
            smtp.sendmail('asandgren@minda.asn.au', 'asandgren@minda.asn.au', msg.as_string())

            return

        missing.apply(generate_email_missing, axis=1)
        time_error.apply(generate_email_time_error, axis=1)      

        res = make_response(jsonify({ 'msg': 'Success' }), 200)

        return res


# Function for downloading generated reports
@app.route('/generated_data/<path:filename>', methods=["GET", "POST"])
def dl_report(filename):
    uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
    return send_from_directory(uploads, filename)


@ app.template_filter()
def currencyFormat(value):
    value = float(value)
    return "${:,.2f}".format(value)
