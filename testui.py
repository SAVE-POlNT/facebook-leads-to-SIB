
from PyQt5 import QtWidgets, uic
from tinydb import TinyDB, Query
import sys
import time
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import glob
import os
import pandas as pd
from validate_email import validate_email
from datetime import datetime


# IMPORT CONTACTS TO SENDINBLUE :
def import_to_sib(key, listid, file):
    configuration = sib_api_v3_sdk.Configuration()
    df = pd.read_csv(file)
    configuration.api_key['api-key'] = key

    for index, row in df.iterrows():
        print(index)
        api_instance = sib_api_v3_sdk.ContactsApi(
            sib_api_v3_sdk.ApiClient(configuration))
        create_contact = sib_api_v3_sdk.CreateContact(
            email=row['email'],
            attributes={'nom': row['nom'],
                        "prenom": row['prenom'],
                        'telephone': row['telephone'],
                        'modele': row['modele'],
                        'wilaya': row['wilaya']},
            list_ids=[listid],
            email_blacklisted=False,
            sms_blacklisted=False,
            update_enabled=True
        )
        try:

            api_response = api_instance.create_contact(create_contact)
        except ApiException as e:
            print("Exception when calling ContactsApi->create_contact: %s\n" % e)
    print('done')


# GETTING PROSPECTS FROM FACEBOOK :
def get_fb_prospects(themail, thepass, thelink, thedldir, thename, thesib_api, thelistid, thedl_dir, thefile_name):
    path = thedldir
    # Pofile :
    profile = FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", path)
    profile.set_preference(
        "browser.helperApps.neverAsk.saveToDisk", "text/csv")

    # options :
    Opt = Options()
    Opt.headless = True

    # Instanciate the Driver :
    driver = webdriver.Firefox(options=Opt, firefox_profile=profile)
    driver.get(
        thelink)
    # driver.set_script_timeout(5)

    mail = driver.find_element_by_id("email")
    password = driver.find_element_by_id("pass")
    connect = driver.find_element_by_id("loginbutton")
    mail.clear()
    # elem.text('')
    mail.send_keys(themail)
    password.send_keys(thepass)
    print('mail and password set')
    print("connecting ...")
    connect.click()
    print("connected")

    dlid = 1
    exists = True
    while(exists is True):
        try:
            download = driver.find_element_by_xpath(
                '/html/body/div[1]/div[3]/div[1]/div[2]/span/div/div[2]/div[3]/div/div/div[4]/div[1]/div/div[1]/div/div[3]/div['+str(dlid)+']/div/div/div[2]/div/div[7]/div/div/div')
            download.click()
            time.sleep(2)
            print("selecting xls format...")

            pr = driver.find_element_by_class_name('_4rn1')
            pr.click()
            time.sleep(2)
            print("got prospects")
            XLS = driver.find_element_by_link_text('CSV')
            XLS.click()
            time.sleep(2)

            nom = max(glob.glob(str(path)+"*"), key=os.path.getctime)
            print(nom)

            fname = str(path)+str(thename)+str(dlid)+".csv"
            os.rename(r''+str(nom), r''+fname)
            import_to_sib(thesib_api, thelistid, fname)

            dlid += 1

            cancel = driver.find_element_by_xpath(
                "/html/body/div[7]/div[2]/div/div/div/div/div[3]/div/div/div[2]/div/a")
            cancel.click()
        except:
            exists = False

    ui.alert_profiles.setText("Done Processing .")

    driver.close()


# CHECK IF TIME == TOMORROW TO MODIFY STATE :
def check_time():
    # add time to the db and check if 1 day is over
    pass


# UPDATE PROFILE NAME :
def update_profile():
    try:
        User = Query()
        db.update({'note': str(ui.note.text())}, User.profile_name == str(
            ui.profiles_list.item(ui.profiles_list.currentRow(), 0).text()))
        ui.alert_profiles.setText('Note Updated')
        refresh_list()

    except:
        ui.alert_profiles.setText('Make sure you select a Profile first')


# THE MAIN LOOP :
def profile_data():
    ui.alert_profiles.setText("Processing ... do not leave the app.")
    try:
        User = Query()

        user_data = db.search(User.profile_name == str(
            ui.profiles_list.item(ui.profiles_list.currentRow(), 0).text()))

        try:
            print(user_data[0]['fb_mail'])

            get_fb_prospects(user_data[0]['fb_mail'], user_data[0]['fb_pass'], user_data[0]['fb_page_link'], user_data[0]['dl_dir'], user_data[0]
                             ['file_name'], user_data[0]['sib_api'], user_data[0]['listid'], str(user_data[0]['dl_dir']), str(user_data[0]['file_name'])+'.csv')
            db.update({'etat': ' \t\t✔ '}, User.profile_name == str(
                ui.profiles_list.item(ui.profiles_list.currentRow(), 0).text()))
            refresh_list()
            # import_to_sib(user_data[0]['sib_api'],user_data[0]['listid'],str(user_data[0]['dl_dir'])+str(user_data[0]['file_name'])+'.csv')

        except:
            ui.alert_profiles.setText('Make sure your Profile is Valid')
    except:
        ui.alert_profiles.setText('Make sure you select a Profile first')


# DELETING A PROFILE :
def delete_profile():
    try:
        User = Query()
        db.remove(User.profile_name == str(ui.profiles_list.item(
            ui.profiles_list.currentRow(), 0).text()))
        refresh_list()
        ui.alert_profiles.setText('Profile Removed')
    except:
        ui.alert_profiles.setText('Make sure you select a Profile first')


# REFRESHING THE PROFILES TABLE :
def refresh_list():
    row = 0
    ui.profiles_list.setRowCount(0)
    for dbprofile in db.all():
        ui.profiles_list.insertRow(row)
        ui.profiles_list.setItem(row, 0, QtWidgets.QTableWidgetItem(
            str(dbprofile['profile_name'])))
        ui.profiles_list.setItem(
            row, 1, QtWidgets.QTableWidgetItem(str(dbprofile['etat'])))
        ui.profiles_list.setItem(
            row, 2, QtWidgets.QTableWidgetItem(str(dbprofile['note'])))
        row += 1


# CHECK IF A MAIL IS VALID :
def valid_fb():
    is_valid = validate_email(ui.fb_mail.text(), verify=True)
    if is_valid:
        ui.alert_new.setText('Your mail is Valid')
    else:
        ui.alert_new.setText('Your mail Is Invalid')


# ADD A NEW PROFILE
def add_to_db():
    db_fb_mail = str(ui.fb_mail.text())
    db_fb_pass = str(ui.fb_pass.text())
    db_fb_page_link = str(ui.fb_page_link.text())
    db_sib_api = str(ui.sib_api.text())
    try:
        db_listid = int(ui.sib_list.text())
    except:
        ui.alert_new.setText('List must be integer')

    db_dl_dir = str(ui.download_dir.text())
    db_file_name = str(ui.file_name.text())
    db_profile_name = str(ui.profile_name.text())
    User = Query()
    # test if the profile name exists:
    if len(db.search(User.profile_name == db_profile_name)) != 0:
        ui.alert_new.setText(
            'This Profile Name already exists Please try with anotheer one')
    else:
        db.insert({"fb_mail": db_fb_mail,
                   "fb_pass": db_fb_pass,
                   "fb_page_link": db_fb_page_link,
                   "sib_api": db_sib_api,
                   "listid": db_listid,
                   "dl_dir": db_dl_dir,
                   "file_name": db_file_name,
                   "profile_name": db_profile_name,
                   "etat": "Unseen",
                   "note": "",
                   "time": str(datetime.now())})
        ui.alert_new.setText('Your profile is succesfully saved')
        refresh_list()


def refresh_states():
    for dbprofile in db.all():
        if ((datetime.strptime(db.profile['time']))+datetime.timedelta(hours=24)) < (datetime.now()):
            pass
        # update


db = TinyDB('fb2sib.json')
app = QtWidgets.QApplication(sys.argv)
ui = uic.loadUi('fb2sib.ui')
# ui.import_all.clicked.connect()
ui.import_contacts.clicked.connect(profile_data)
ui.add_note.clicked.connect(update_profile)
ui.fb_check.clicked.connect(valid_fb)
ui.profile_add.clicked.connect(add_to_db)
ui.delete_profile.clicked.connect(delete_profile)
refresh_list()

ui.now = datetime.now()
ui.show()


app.exec_()
