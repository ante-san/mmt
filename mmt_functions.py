import numpy as np
import pandas as pd
import datetime as dt

# function to add charge duration to an eCase Roster
def addChargeDuration(roster, charge):

    print('Adding Charge Duration')

    # assign the passed in arguments to new DataFrames
    # to avoid mutating arguments
    df_roster = roster
    df_charge = charge

    # Create the appropriate StartDateTime and EndDateTime by combining Time and Date data
    # and converting to datetime for consistency when comparing
    df_charge['StartTime'] = pd.to_datetime(df_charge['StartTime'], format='%H:%M').dt.time
    df_charge['EndTime'] = pd.to_datetime(df_charge['EndTime'], format='%H:%M').dt.time
    df_charge['Date'] = pd.to_datetime(df_charge['Date']).dt.date
    df_charge['StartDateTime'] = df_charge.apply(lambda r: dt.datetime.combine(r['Date'], r['StartTime']), 1)
    df_charge['EndDateTime'] = df_charge.apply(lambda r: dt.datetime.combine(r['Date'], r['EndTime']), 1)

    # create a shiftID for the the Charge Duration DataFrame
    def chargeSK(df):
        return str(df['Client']) + str(df['StartDateTime']) + str(df['EndDateTime']) + str(df['Staff'])

    df_charge["shiftID_Complete"] = df_charge.apply(chargeSK, axis=1)

    # join the Charge Duration from the charge duration DataFrame based
    # on the shiftIDs
    df_roster = pd.merge(df_roster, df_charge[['shiftID_Complete', 'ServiceDuration']], on='shiftID_Complete', how='left')

    # calculate the Charge Difference by subtracting Roster Duration (what staff work) from the
    # charge duration (what we can bill for)
    df_roster['chargeDiff'] = df_roster['RosterDuration'] - df_roster['ServiceDuration']

    return df_roster


# function to check the billings status of shifts,
# looking for information on
# codes, vehicle usage, timings, progress notes
# to verify whether a shift can be billed or needs to be reviewed
# requires that the roster and progress notes have been cleaned, and
# that charge duration has been added
def billingStatus(roster, progNote):

    print('Checking Billing Status')

    df_roster = roster
    df_progNote = progNote

    # merge data frames to get vehicle status into the roster DataFrame
    df_roster = pd.merge(df_roster, df_progNote[['shiftID_Date', 'Vehicle', 'Notes', 'StartTime', 'EndTime', 'Kms Travelled', 'Address']], on='shiftID_Date', how='left')
    df_roster = df_roster.drop_duplicates('shiftID_Complete', keep='last')

    df_roster["Address"] = df_roster["Address"].str.lower()
    df_roster["onCampus"] = df_roster["Address"].str.contains("north brighton")

    validNote = df_progNote['shiftID_Complete'].tolist()
    validNoteDate = df_progNote['shiftID_Date'].tolist()

    # first we need to loop through and check whether there is a valid progress
    # note for each shift, as well as check whether there is a progress note
    # for the day for that client, but not 100% valid (e.g., wrong staff, wrong
    # times).

    def progNoteStatus(df):

        if df["shiftID_Complete"] in validNote:
            return "Accepted"
        if df["shiftID_Date"] in validNoteDate:
            return "TimeError"

        return "Missing"

    def chargeDurationStatus(df):
        
        if df["progNoteStatus"] != "Missing":
            if df["Vehicle"] == "F" and df["onCampus"] == False:
                if df["chargeDiff"] <= 0 or df["chargeDiff"] > 30:
                    return "chargeDurationError"
            if df["Vehicle"] == "F" and df["onCampus"] == True:
                if df["chargeDiff"] != 0:
                    return "chargeDurationError"
            if df["Vehicle"] != "F" and df["chargeDiff"] != 0:
                return "chargeDurationError"

            return "Accepted"
        
        return "Missing"

    def codeErrorCheck(df):
        evening = dt.time(20)

        # hardcoding data like a boss
        code_days = {
            "weekday": ["04_104_0125_6_1", "04_104_0125_6_1_T", "04_102_0136_6_1_T", "01_011_0107_1_1_T", "09_009_0117_6_3"],
            "evening": ["04_103_0125_6_1_T", "04_103_0136_6_1_T", "01_015_0107_1_1_T"],
            "saturday": ["04_105_0125_6_1_T", "04_104_0136_6_1_T", "01_013_0107_1_1_T"],
            "sunday": ["04_106_0125_6_1_T", "04_105_0136_6_1_T", "01_014_0107_1_1_T"],
        }

        if df['ClientCode'] == 'B51D6F2A':
            print(df)
            print(type(df["EndTime"]))
            for num in range(0,4):
                print(num)

        if str(type(df['EndTime'])) == "<class 'datetime.time'>":
            if df['Service Date'].weekday() in range(0, 5):
                if df['ActivityCode'] in code_days["weekday"]:
                    if df['EndTime'] > evening:
                        print(df)
                        return 'Code Error'
                elif df['ActivityCode'] in code_days["evening"]:
                    if df['EndTime'] <= evening:
                        return 'Code Error'
            elif df['Service Date'].weekday() == 5:
                if df["ActivityCode"] not in code_days["saturday"]:
                    return 'Code Error'
            elif df['Service Date'].weekday() == 6:
                if df["ActivityCode"] not in code_days["sunday"]:
                    return 'Code Error'

        return df["progNoteStatus"]

    def billingStatus(df):
        if df["progNoteStatus"] == "Accepted" and df["chargeDurationStatus"] == "Accepted":
            return "Accepted"
        if df["chargeDurationStatus"] == "chargeDurationError":
            return "Error"
        if df["progNoteStatus"] == 'TimeError':
            return "TimeError"

        return "Error"

    df_roster["progNoteStatus"] = df_roster.apply(progNoteStatus, axis=1)
    
    df_roster["chargeDurationStatus"] = df_roster.apply(chargeDurationStatus, axis=1)
    
    df_roster["progNoteStatus"] = df_roster.apply(codeErrorCheck, axis=1)

    df_roster["billingStatus"] = df_roster.apply(billingStatus, axis=1)

    return df_roster

# function to generate a and save a formatted report for
# the billings report generator
def billingStatusReport(roster):
    
    df_roster = roster

    # filter out unnecessary columns
    df_roster = df_roster[['ClientCode', 'ClientFullName', 'ActivityCode', 'ProgramType', 'Service Date', 'RosterStartDateTime', 'RosterEndDateTime',
                           'Instructions', 'AllocatedStaff', 'StartTime',
                           'EndTime', 'RosterDuration', 'ServiceDuration', 'Notes', 'Vehicle', 'Kms Travelled',
                           'chargeDurationStatus', 'progNoteStatus', 'billingStatus']]

    time = dt.datetime.now().strftime('%Y%m%d_%H%M%S')

    filename = f"billing_review/billing_review{time}.xlsx"

    writer = pd.ExcelWriter(f"app/static/generated_data/{filename}", engine='xlsxwriter')

    df_roster.to_excel(writer, sheet_name='Billing_Review', index=False)

    workbook = writer.book
    worksheet = writer.sheets['Billing_Review']

    # create the three formats, where format_1 is Green, format_2 is Orange, and format_3 is Red
    format_1 = workbook.add_format({'bg_color': '#44e371'})
    format_2 = workbook.add_format({'bg_color': '#ffb04f'})
    format_3 = workbook.add_format({'bg_color': 'ff4f4f'})

    # format the returned values in the 'chargeDurationStatus', 'progNoteStatus' and 'billingStatus'
    # columns
    # be mindful to update this formatting if adding additional columns
    # to the report
    # first format accepted in all columns (as this is the same formatting and value
    # in all three columns
    worksheet.conditional_format('Q2:S1048576', {'type': 'text',
                                                 'criteria': 'containing',
                                                 'value': 'Accepted',
                                                 'format': format_1})

    worksheet.conditional_format('Q2:S1048576', {'type': 'text',
                                                 'criteria': 'containing',
                                                 'value': 'Code Error',
                                                 'format': format_2})

    worksheet.conditional_format('Q2:S1048576', {'type': 'text',
                                                 'criteria': 'containing',
                                                 'value': 'Missing',
                                                 'format': format_3})

    # format for 'chargeDurationError' in the 'chargeDurationError column.
    # This value only exists in this column
    worksheet.conditional_format('Q2:Q1048576', {'type': 'text',
                                                 'criteria': 'containing',
                                                 'value': 'chargeDurationError',
                                                 'format': format_2})

    # format for 'AcceptedByDATE' in both the progNoteStatus and billingStatus
    # columns.
    # this value and formatting is consistent between these two columns
    worksheet.conditional_format('R2:S1048576', {'type': 'text',
                                                 'criteria': 'containing',
                                                 'value': 'TimeError',
                                                 'format': format_2})

    # format for 'Missing' in 'progeNoteStatus column. This value only
    # exists in this column
    worksheet.conditional_format('R2:S1048576', {'type': 'text',
                                                 'criteria': 'containing',
                                                 'value': 'Missing',
                                                 'format': format_3})

    # format for 'Error' in the 'billingStatus' column. This value only
    # exists in this column.
    worksheet.conditional_format('S2:S1048576', {'type': 'text',
                                                 'criteria': 'containing',
                                                 'value': 'Error',
                                                 'format': format_3})

    writer.save()

    return filename

# function for extracting vehicle booking information from
# the eCase roster report
def carBookings(roster):

    df_ec = roster
    
    # exclude non-mentoring (302) services
    df_ec = df_ec[df_ec["Cost Center"] == "302 Mentoring Services"]
    df_ec = df_ec[df_ec["Status"] != "Cancelled"]

    # log shifts that are missing instructions
    df_missing = missingInstructions(df_ec)
    time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    missing_filename = f"vh_booking/missing_instructions/missing_instructions_{time}.csv"
    df_missing.to_csv(f"app/static/generated_data/{missing_filename}")

    # excluding shifts without instructions
    df_ec = df_ec.dropna(subset=["Instructions"])

    # extracting Vehicle data into new column/Series object "Vehicle"
    df_ec["Vehicle"] = df_ec["Instructions"].apply(lambda vh: vh[vh.find("Vehicle")+8:vh.find("Shift")])

    # cleaning up vehicle data
    df_ec["Vehicle"] = df_ec["Vehicle"].str.rstrip(".\n* ")
    df_ec["Vehicle"] = df_ec["Vehicle"].str.lstrip(".:; ")

    # excluding shifts that do not require fleet ("N, N/A, Staff Vehicle, SV")
    excluded = ["N", "N/A", "STAFF VEHICLE", "PRIVATE VEHICLE", "HOUSE CAR", "SV", "HC", "SV/HC", "Y/N/SV/HC", ""]
    for item in excluded:
        df_ec = df_ec[df_ec["Vehicle"].str.upper() != item]

    filename = f"vh_booking/vh_booking_report/vh_booking_report_{time}.csv"
    df_ec.to_csv(f"app/static/generated_data/{filename}")

    return filename, missing_filename


# function to check whether there are instructions entered for shifts in the eCase roster
# returns a DataFrame containing the shifts to do not have any instructions
def missingInstructions(roster):

    df = roster
    df_ec_missing = df[df["Instructions"].isna()]

    return df_ec_missing

# function for cleaning progress notes and creating unqiue Shift IDs
def cleanNotes(prog_notes):

    print('Starting Progress Note Clean Up')

    df_progNote = prog_notes

    # extract and format vehicle status
    df_progNote['Vehicle'] = df_progNote['Notes'].apply(
        lambda st: st[st.find('vehicle:')+7:st.find('LOCATION')])
    df_progNote['Vehicle'] = df_progNote['Vehicle'].str.rstrip('\r\n ')
    df_progNote['Vehicle'] = df_progNote['Vehicle'].str.lstrip(':\r\n ')
    df_progNote['Vehicle'] = df_progNote['Vehicle'].astype(str).str[0]
    df_progNote['Vehicle'] = df_progNote['Vehicle'].str.capitalize()

    # need to add cancel status to Roster Maintenance Report, or charge + roster duration
    # to the Appointments view
    # UPDATE: not sure what I meant here, but the code seems to be working fine without
    # it being implemented

    # Extract Km travelled
    df_progNote['Kms Travelled'] = df_progNote['Notes'].apply(
        lambda st: st[st.find("TRAVE")+6:st.find("PERSON")])

    #############################################################################
    #   This can probably be improved with regex
    #############################################################################
    df_progNote['Kms Travelled'] = df_progNote['Kms Travelled'].str.rstrip(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/)('~ +.\r\n\t:Â-;`’")
    df_progNote['Kms Travelled'] = df_progNote['Kms Travelled'].str.lstrip(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/)('~ +.\r\n\t:Â-;`’")


    ############################################################################################
    #   As date cleaning is done in a number of instances, I should put this in a seperate
    #   function. One that would take the date, and format
    ############################################################################################
    # format Start Time and End Time and then join with Service Date to create Date + Time column
    df_progNote['StartTime'] = pd.to_datetime(
        df_progNote['StartTime'], format='%H:%M').dt.time
    df_progNote['EndTime'] = pd.to_datetime(
        df_progNote['EndTime'], format='%H:%M').dt.time
    df_progNote['StartDate'] = pd.to_datetime(
        df_progNote['StartDate'], format="%d %b %Y").dt.date
    df_progNote['EndDate'] = pd.to_datetime(
        df_progNote['EndDate'], format="%d %b %Y").dt.date
    df_progNote['StartDateTime'] = df_progNote.apply(
        lambda r: dt.datetime.combine(r['StartDate'], r['StartTime']), 1)
    df_progNote['EndDateTime'] = df_progNote.apply(
        lambda r: dt.datetime.combine(r['EndDate'], r['EndTime']), 1)

    def progSK(df, type):
        return f"{df['ClientCode'] + str(df['StartDateTime']) + str(df['EndDateTime']) + df['Author']}" if type=="complete" else f"{df['ClientCode'] + str(df['StartDate']) + df['Author']}"

    df_progNote["shiftID_Complete"] = df_progNote.apply(lambda df: progSK(df, "complete"), axis=1)
    df_progNote["shiftID_Date"] = df_progNote.apply(lambda df: progSK(df, "date"), axis=1)

    return df_progNote

def budgetCheck(billed_fname, budget_fname, scheduled_fname, cctr):

    cost_center = cctr

    df_budget = pd.read_csv(budget_fname)
    df_billed = pd.read_csv(billed_fname)
    df_scheduled = pd.read_csv(scheduled_fname)

    # Getting budget value and start date of plan
    df_budget["StartDate"] = pd.to_datetime(df_budget["StartDate"])
    df_budget["EndDate"] = pd.to_datetime(df_budget["EndDate"])
    start_date = df_budget["StartDate"].min()
    end_date = df_budget["EndDate"].max()
    end_date = df_budget["EndDate"].max()
    remaining_weeks = round(
        (abs(pd.to_datetime(dt.date.today())-end_date).days)/7, 2)
    remaining_fortnights = remaining_weeks / 2
    name = df_budget["ClientName"].min()
    quote_no = df_budget["Version"].max()
    df_budget = df_budget[df_budget["CostCenter"] == cost_center]
    df_budget = df_budget.drop_duplicates(subset="ServicePlanOrder")

    
    # remove ABT codes and Transport Codes
    transport_codes = ["04_590_0125_6_1 ~Activity Based Transport", "04_591_0136_6_1 ~Activity Based Transport", "04_592_0104_6_1 ~Activity Based Transport", "09_591_0117_6_3", "02_051_0108_1_1 ~Transport"]
    for code in transport_codes:
        df_budget = df_budget[df_budget["ServiceActivity"] != code]

    budget_total = round(df_budget["ExtendedTotal"].sum(), 2)
    agreed_codes = set(df_budget["ServiceActivity"].to_list())

    # Getting billed amount and last bill date
    df_billed["ServiceDate"] = pd.to_datetime(df_billed["ServiceDate"])
    df_billed = df_billed[df_billed["ServiceDate"] >= start_date]
    df_billed = df_billed[df_billed["ServiceCostCenter"] == cost_center]
    last_bill = df_billed["ServiceDate"].max()
    billed_total = round(df_billed["TotalNetCharge"].sum(), 2)

    # Getting the scheduled services
    df_scheduled["PlannedDate"] = pd.to_datetime(df_scheduled["PlannedDate"])
    # Checking whether we have a bill date. Necessary if not billing has been
    # completed
    if not pd.isnull(last_bill):
        df_scheduled = df_scheduled[df_scheduled["PlannedDate"] > last_bill]
    df_scheduled = df_scheduled[df_scheduled["CostCenter"]
                                == "302 - Mentoring Services"]
    df_scheduled = df_scheduled[df_scheduled["ActiveStatus"]
                                == "Currently Active"]
    scheduled_total = round(df_scheduled["UnitPriceTotal"].sum(), 2)

    # Calculate Available Funds
    unallocated = round(budget_total - (billed_total + scheduled_total), 2)

    budget_container = {
        "name": name,
        "quote_no": quote_no,
        "start_date": start_date,
        "end_date": end_date,
        "cost_center": cost_center,
        "remaining_weeks": remaining_weeks,
        "remaining_fortnights": remaining_fortnights,
        "budget_total": budget_total,
        "billed_total": billed_total,
        "scheduled_total": scheduled_total,
        "unallocated": unallocated,
        "agreed_codes": agreed_codes
    }

    return budget_container


# function to clean up roster data from Roster generated through
# the Roster Maintenance, and creating unique IDs
# this function is used for shifts against progress notes,
# and does not work when information on vehicle usage and mileage
# is required
def rosterClean_deprecated(roster, cctr):
    print('Starting Roster Clean Up')
    df_roster = roster
    cost_center = cctr

    # Filtering for Mentoring shifts and excluding cancelled shifts as we do
    # not expect progress notes for those, and dropping unallocated shifts
    df_roster = df_roster[df_roster['Cost Center'] == cost_center]
    df_roster = df_roster[df_roster['Status'] != 'Cancelled']

    # converting the dates into datetime to ensure consistency when comparing
    df_roster['Start Date Time'] = pd.to_datetime(
        df_roster['Start Date Time'], format='%Y/%m/%d %H:%M')
    df_roster['End Date Time'] = pd.to_datetime(
        df_roster['End Date Time'], format='%Y/%m/%d %H:%M')
    df_roster['Service Date'] = pd.to_datetime(
        df_roster['Start Date Time'], format='%Y/%m/%d').dt.date

    def rosterSK(df, type):
        return f"{df['Client'] + str(df['Start Date Time']) + str(df['End Date Time']) + str(df['Allocated Carer'])}" if type=="complete" else f"{df['Client'] + str(df['Service Date']) + str(df['Allocated Carer'])}"

    def rosterDurationCalc(df):

        roster_duration = df['End Date Time'] - df['Start Date Time']
        roster_duration = roster_duration/np.timedelta64(1, 'm')

        return roster_duration

    df_roster["shiftID_Complete"] = df_roster.apply(lambda df: rosterSK(df, "complete"), axis=1)
    df_roster["shiftID_Date"] = df_roster.apply(lambda df: rosterSK(df, "date"), axis=1)
    df_roster["rosterDuration"] = df_roster.apply(rosterDurationCalc, axis=1)

    # Adding staff email to roster
    df_staff_detail = pd.read_csv(
        "app/static/data_files/staff_details.csv")

    df_roster = pd.merge(
        df_roster, df_staff_detail[['FullName', 'Email', 'FirstName', 'LastName']], left_on='Allocated Carer', right_on='FullName', how='left')
    df_roster = df_roster.drop_duplicates('shiftID_Complete', keep='last')

    return df_roster


# This is an updated version of the roster clean function. The previous function was used
# to clean a roster that was run from the Roster Maintenance. This function is based on
# running a report using the YF_BillingForcastAccruals view within the report generator. It will
# also replace the addChargeDuration function as this view contains the charge duration already.
# I'm keeping the old functions in the code as they may be needed at some point.
def rosterClean(roster, cctr):
    df_roster = roster

    df_roster.to_csv("roster_check.csv")

    df_roster = df_roster[df_roster['CostCenter'] == cctr]
    df_roster = df_roster[df_roster['Status'] != 'Cancelled']

    df_roster["RosterStartDateTime"] = pd.to_datetime(df_roster["RosterStartDateTime"])
    df_roster["RosterEndDateTime"] = pd.to_datetime(df_roster["RosterEndDateTime"])
    df_roster["Service Date"] = df_roster["RosterStartDateTime"].dt.date
    
    # The report from the YF_BillingForecastAccruals does not adjust the roster duration if
    # changes are made in the roster, instead it gives the roster duration that was originally
    # entered when shift was created. It needs to be re-calculated based on the timings (because they
    # do update)
    df_roster["RosterDuration"] = (df_roster["RosterEndDateTime"] - df_roster["RosterStartDateTime"])/np.timedelta64(1, 'm')

    def rosterSK(df, type):
        return f"{df['ClientCode'] + str(df['RosterStartDateTime']) + str(df['RosterEndDateTime']) + str(df['AllocatedStaff'])}" if type=="complete" else f"{df['ClientCode'] + str(df['Service Date']) + str(df['AllocatedStaff'])}"

    df_roster["shiftID_Complete"] = df_roster.apply(lambda df: rosterSK(df, "complete"), axis=1)
    df_roster["shiftID_Date"] = df_roster.apply(lambda df: rosterSK(df, "date"), axis=1)

    df_staff_detail = pd.read_csv("app/static/data_files/staff_details.csv")

    df_roster = pd.merge(df_roster, df_staff_detail[['PayrollID', 'FullName', 'Email', 'FirstName', 'LastName']], on='PayrollID', how='left')
    df_roster = df_roster.drop_duplicates('shiftID_Complete', keep='last')

    df_roster['chargeDiff'] = df_roster['RosterDuration'] - df_roster['ServiceDuration']

    return df_roster



# function to clean up the roster from RosterOn, translating
# RosterOn names and RosterOn client names to eCase namings
# and generating unique shift_IDs
def rosterOnClean(roster):

    df_ro = roster

    # Converting dates to DateTime objects for consistency
    # note that when RosterOn creates it's report, "finish_time" is actually
    # the start time, and "role_desc" is the finish time
    df_ro["finish_time"] = pd.to_datetime(df_ro["finish_time"], format="%d/%m/%Y %H:%M")
    df_ro["role_desc"] = pd.to_datetime(df_ro["role_desc"], format="%d/%m/%Y %H:%M")

    # drop the empty columns data RosterOn produces
    df_ro = df_ro.drop('Unnamed: 8', axis=1)

    # ensure that IDs are stored as int for consistency
    df_ro["area_id"] = df_ro["area_id"].astype('int')
    df_ro["emp_no"] = df_ro["emp_no"].astype('int')

    # read in staff details to translate between RosterOn data and eCase data
    df_staff = pd.read_csv("app/static/data_files/staff_details.csv")

    # drop staff without a PayrollID
    df_staff = df_staff[df_staff["PayrollID"].notna()]

    # make sure we've only got digits before converting to int,
    # cause varchar10000, hehehehehe
    df_staff = df_staff[df_staff["PayrollID"].apply(lambda id: str(id).isdigit())]

    # ensure that PayrollID is an int
    df_staff["PayrollID"] = df_staff["PayrollID"].astype("int")

    # merge staff's eCase names based on PayrollID
    df_ro = pd.merge(df_ro, df_staff[['PayrollID', 'FullName']], left_on='emp_no', right_on='PayrollID', how='left')

    # read in client's eCase name to translate between RosterOn and eCase data
    df_client = pd.read_csv('app/static/data_files/minda_clients.csv')

    # merge based on RosterOn id
    df_ro = pd.merge(df_ro, df_client[['RosteronID', 'FullNameClient', 'eCase ID']], left_on='area_id', right_on='RosteronID', how='left')

    # record clients and staff who are missing so that they can be added in the future
    time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    # for some reason it seems to add spaces instead of NaN values
    df_ro["FullNameClient"] = df_ro["FullNameClient"].str.strip(" ")

    df_missing_clients = df_ro[(df_ro["FullNameClient"] == "") | (df_ro["FullNameClient"] == " ") | (df_ro["FullNameClient"].isna())]
    df_missing_clients = df_missing_clients[df_missing_clients["area_desc"] != "Mentoring - GROUP - LSDM"]
    df_missing_clients = df_missing_clients[df_missing_clients["area_desc"] != "Mentoring Services - CCtr 302"]
    df_missing_clients.to_csv(f"app/static/generated_data/roster_check/missing_clients/missing_clients{str(time)}.csv", index=False)

    df_missing_staff = df_ro[df_ro["FullName"].isna()]
    df_missing_staff.to_csv(f"app/static/generated_data/roster_check/missing_staff/missing_staff{str(time)}.csv", index=False)

    # drop staff and clients that are missing so that the script can continue running
    df_ro = df_ro[df_ro["FullNameClient"] != ""]
    df_ro = df_ro[df_ro["FullName"] != ""]

    def createShiftID(df):
        return str(df['eCase ID']) + str(df['finish_time']) + str(df['role_desc']) + str(df['FullName'])

    df_ro["shiftID_Complete"] = df_ro.apply(createShiftID, axis=1)

    return df_ro, df_missing_clients.drop_duplicates("area_id", keep="first"), df_missing_staff.drop_duplicates("emp_no", keep="first")


# function to compare the roster in eCase with the
# roster in RosterOn
def rosterRosterCheck(ec, ro):
    df_ec = ec
    df_ro = ro

    df_ec["RosterOrigin"] = "eCase"
    df_ro["RosterOrigin"] = "RosterOn"

    df_ro = df_ro.rename(columns={"FullNameClient": "ClientFullName", "finish_time": "RosterStartDateTime", "role_desc": "RosterEndDateTime", "FullName": "AllocatedStaff"})

    df_ro = df_ro.drop_duplicates("shiftID_Complete", keep="first")
    df_ec = df_ec.drop_duplicates("shiftID_Complete", keep="first")

    ro_shifts = df_ro["shiftID_Complete"].tolist()

    ec_shifts = df_ec["shiftID_Complete"].tolist()

    def checkRoster(df, list, msg):
        return True if df["shiftID_Complete"] in list else msg

    df_ec["RosterStatus"] = df_ec.apply(lambda df: checkRoster(df, ro_shifts, "Not found in RosterOn"), axis=1)
    df_ro["RosterStatus"] = df_ro.apply(lambda df: checkRoster(df, ec_shifts, "Not found in eCase"), axis=1)

    df_ec = df_ec[["ClientFullName", "AllocatedStaff", "RosterStartDateTime", "RosterEndDateTime", "RosterStatus", "RosterOrigin"]]
    df_ro = df_ro[["ClientFullName", "AllocatedStaff", "RosterStartDateTime", "RosterEndDateTime", "RosterStatus", "RosterOrigin"]]
    df_ec = df_ec.append(df_ro)
    df_ec = df_ec[df_ec["RosterStatus"] != True]

    df_ec.sort_values(["ClientFullName", "RosterStartDateTime"], inplace=True)

    time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    filename_result = f"roster_check/report/roster_check_{time}.csv"

    df_ec.to_csv(f"app/static/generated_data/{filename_result}", index=False)

    return filename_result

# function to check progress notes entered against rostered
# shifts in eCase
# requires Mentoring Progress Note report and
# roster report from the Roster Maintenance
def progressNoteCheck(roster_file, prog_note_file):

    df_roster = roster_file
    df_prog_note = prog_note_file

    valid_note = df_prog_note["shiftID_Complete"].tolist()
    valid_note_date = df_prog_note["shiftID_Date"].tolist()
    valid_note_hash = {valid_note[i]: 0 for i in range(0, len(valid_note), 1)}
    valid_note_date_hash = {
        valid_note_date[i]: 0 for i in range(0, len(valid_note_date), 1)}

    def checkProgNotes(df):
        if df["shiftID_Complete"] in valid_note_hash:
            return "Accepted"
        if df["shiftID_Date"] in valid_note_date_hash:
            return "Time Error"

        return "Missing"

    df_roster["ValidProgNoteComplete"] = df_roster.apply(checkProgNotes, axis=1)

    return df_roster