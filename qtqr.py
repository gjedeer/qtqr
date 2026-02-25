#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
GUI front end for qrencode based on the work of David Green:
<david4dev@gmail.com> https://launchpad.net/qr-code-creator/
and inspired by
http://www.omgubuntu.co.uk/2011/03/how-to-create-qr-codes-in-ubuntu/
uses python-zbar for decoding from files and webcam
"""

import io
import os
import sys
from math import ceil

from PIL import Image
from PyQt5 import QtCore, QtGui, QtNetwork, QtWidgets
from PyQt5.QtMultimedia import QCameraInfo
from PyQt5.QtWidgets import QDialog

from qrtools import QR

__author__ = "Ramiro Algozino"
__email__ = "algozino@gmail.com"
__copyright__ = "copyright (C) 2011-2020 Ramiro Algozino"
__credits__ = "David Green, Boyuan Yang, Ying-Chun Liu"
__license__ = "GPLv3"
__version__ = "2.1"


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        self.setWindowTitle(self.tr("QtQR: QR Code Generator"))
        icon = os.path.join(os.path.dirname(__file__), "icon.png")
        if not QtCore.QFile(icon).exists():
            icon = "/usr/share/pixmaps/qtqr.png"
        self.setWindowIcon(QtGui.QIcon(icon))
        self.w = QtWidgets.QWidget()
        self.setCentralWidget(self.w)
        self.setAcceptDrops(True)

        # Templates for creating QRCodes supported by qrtools
        self.templates = {
            "text": str(self.tr("Text")),
            "url": str(self.tr("URL")),
            "bookmark": str(self.tr("Bookmark")),
            "emailmessage": str(self.tr("E-Mail")),
            "telephone": str(self.tr("Telephone Number")),
            "phonebook": str(self.tr("Contact Information (PhoneBook)")),
            "sms": str(self.tr("SMS")),
            "mms": str(self.tr("MMS")),
            "geo": str(self.tr("Geolocalization")),
            "wifi": str(self.tr("WiFi Network")),
            "sepa": str(self.tr("SEPA Single Payment")),
            "bip21": str(self.tr("Bitcoin Address")),
        }
        # With this we make the dict bidirectional
        self.templates.update(dict((self.templates[k], k) for k in self.templates))

        # Tabs
        # We use this to put the tabs in a desired order.
        self.templateNames = (
            self.templates["text"],
            self.templates["url"],
            self.templates["bookmark"],
            self.templates["emailmessage"],
            self.templates["telephone"],
            self.templates["phonebook"],
            self.templates["sms"],
            self.templates["mms"],
            self.templates["geo"],
            self.templates["wifi"],
            self.templates["sepa"],
            self.templates["bip21"],
        )
        self.selector = QtWidgets.QComboBox()
        self.selector.addItems(self.templateNames)
        self.tabs = QtWidgets.QStackedWidget()
        self.textTab = QtWidgets.QWidget()
        self.urlTab = QtWidgets.QWidget()
        self.bookmarkTab = QtWidgets.QWidget()
        self.emailTab = QtWidgets.QWidget()
        self.telTab = QtWidgets.QWidget()
        self.phonebookTab = QtWidgets.QWidget()
        self.smsTab = QtWidgets.QWidget()
        self.mmsTab = QtWidgets.QWidget()
        self.geoTab = QtWidgets.QWidget()
        self.wifiTab = QtWidgets.QWidget()
        self.sepaTab = QtWidgets.QWidget()
        self.bip21Tab = QtWidgets.QWidget()
        self.tabs.addWidget(self.textTab)
        self.tabs.addWidget(self.urlTab)
        self.tabs.addWidget(self.bookmarkTab)
        self.tabs.addWidget(self.emailTab)
        self.tabs.addWidget(self.telTab)
        self.tabs.addWidget(self.phonebookTab)
        self.tabs.addWidget(self.smsTab)
        self.tabs.addWidget(self.mmsTab)
        self.tabs.addWidget(self.geoTab)
        self.tabs.addWidget(self.wifiTab)
        self.tabs.addWidget(self.sepaTab)
        self.tabs.addWidget(self.bip21Tab)

        # Widgets for Text Tab
        self.l1 = QtWidgets.QLabel(self.tr("Text to be encoded:"))
        self.textEdit = QtWidgets.QPlainTextEdit()

        # Widgets for URL Tab
        self.urlLabel = QtWidgets.QLabel(self.tr("URL to be encoded:"))
        self.urlEdit = QtWidgets.QLineEdit("http://")

        # Widgets for BookMark Tab
        self.bookmarkTitleLabel = QtWidgets.QLabel(self.tr("Title:"))
        self.bookmarkTitleEdit = QtWidgets.QLineEdit()
        self.bookmarkUrlLabel = QtWidgets.QLabel(self.tr("URL:"))
        self.bookmarkUrlEdit = QtWidgets.QLineEdit()

        # Widgets for EMail Tab
        self.emailLabel = QtWidgets.QLabel(self.tr("E-Mail address:"))
        self.emailEdit = QtWidgets.QLineEdit("@.com")
        self.emailSubLabel = QtWidgets.QLabel(self.tr("Subject:"))
        self.emailSubjectEdit = QtWidgets.QLineEdit()
        self.emailBodyLabel = QtWidgets.QLabel(self.tr("Message Body:"))
        self.emailBodyEdit = QtWidgets.QPlainTextEdit()

        # Widgets for Telephone Tab
        self.telephoneLabel = QtWidgets.QLabel(self.tr("Telephone Number:"))
        self.telephoneEdit = QtWidgets.QLineEdit()

        # Widgets for Contact Information Tab
        self.phonebookNameLabel = QtWidgets.QLabel(self.tr("Name:"))
        self.phonebookNameEdit = QtWidgets.QLineEdit()
        self.phonebookTelLabel = QtWidgets.QLabel(self.tr("Telephone:"))
        self.phonebookTelEdit = QtWidgets.QLineEdit()
        self.phonebookEMailLabel = QtWidgets.QLabel(self.tr("E-Mail:"))
        self.phonebookEMailEdit = QtWidgets.QLineEdit()
        self.phonebookNoteLabel = QtWidgets.QLabel(self.tr("Note:"))
        self.phonebookNoteEdit = QtWidgets.QLineEdit()
        self.phonebookBirthdayLabel = QtWidgets.QCheckBox(self.tr("Birthday:"))
        self.phonebookBirthdayEdit = QtWidgets.QDateEdit()
        self.phonebookBirthdayEdit.setCalendarPopup(True)
        self.phonebookAddressLabel = QtWidgets.QLabel(self.tr("Address:"))
        self.phonebookAddressEdit = QtWidgets.QLineEdit()
        self.phonebookAddressEdit.setToolTip(
            self.tr(
                "Insert separated by commas the PO Box, room number, house number, city, prefecture, zip code and country in order"
            )
        )
        self.phonebookUrlLabel = QtWidgets.QLabel(self.tr("URL:"))
        self.phonebookUrlEdit = QtWidgets.QLineEdit()
        self.phonebookLoadButton = QtWidgets.QPushButton(
            QtGui.QIcon.fromTheme("address-book-new"), self.tr("Load from vcard file")
        )

        # Widgets for SMS Tab
        self.smsNumberLabel = QtWidgets.QLabel(self.tr("Telephone Number:"))
        self.smsNumberEdit = QtWidgets.QLineEdit()
        self.smsBodyLabel = QtWidgets.QLabel(self.tr("Message:"))
        self.smsBodyEdit = QtWidgets.QPlainTextEdit()
        self.smsCharCount = QtWidgets.QLabel(self.tr("characters count: 0"))

        # Widgets for MMS Tab
        self.mmsNumberLabel = QtWidgets.QLabel(self.tr("Telephone Number:"))
        self.mmsNumberEdit = QtWidgets.QLineEdit()
        self.mmsBodyLabel = QtWidgets.QLabel(self.tr("Content:"))
        self.mmsBodyEdit = QtWidgets.QPlainTextEdit()

        # Widgets for GEO Tab
        self.geoLatLabel = QtWidgets.QLabel(self.tr("Latitude:"))
        self.geoLatEdit = QtWidgets.QLineEdit()
        self.geoLongLabel = QtWidgets.QLabel(self.tr("Longitude:"))
        self.geoLongEdit = QtWidgets.QLineEdit()

        # Widgets for WiFi Tab
        self.wifiSSIDLabel = QtWidgets.QLabel(self.tr("SSID:"))
        self.wifiSSIDEdit = QtWidgets.QLineEdit()
        self.wifiPasswordLabel = QtWidgets.QLabel(self.tr("Password:"))
        self.wifiPasswordEdit = QtWidgets.QLineEdit()
        self.wifiShowPassword = QtWidgets.QCheckBox(self.tr("Show Password"))
        self.wifiEncryptionLabel = QtWidgets.QLabel(self.tr("Encryption:"))
        self.wifiEncryptionType = QtWidgets.QComboBox()
        self.wifiEncryptionType.addItems(
            (
                self.tr("WEP"),
                self.tr("WPA/WPA2"),
                self.tr("No Encryption"),
            )
        )
        self.wifiHiddenNetwork = QtWidgets.QCheckBox(self.tr("Hidden network"))

        # Widgets for SEPA Überweisung Tab
        # Reference: http://www.bezahlcode.de/wp-content/uploads/BezahlCode_TechDok.pdf
        self.sepaNameLabel = QtWidgets.QLabel(self.tr("Name:"))
        self.sepaNameEdit = QtWidgets.QLineEdit()
        self.sepaAccountLabel = QtWidgets.QLabel(self.tr("Account:"))
        self.sepaAccountEdit = QtWidgets.QLineEdit()
        self.sepaBNCLabel = QtWidgets.QLabel(self.tr("BNC:"))
        self.sepaBNCEdit = QtWidgets.QLineEdit()
        self.sepaAmountLabel = QtWidgets.QLabel(self.tr("Amount:"))
        self.sepaAmountEdit = QtWidgets.QLineEdit()
        self.sepaReasonLabel = QtWidgets.QLabel(self.tr("Reason:"))
        self.sepaReasonEdit = QtWidgets.QLineEdit()
        self.sepaCurrencyLabel = QtWidgets.QLabel(self.tr("Currency:"))
        self.sepaCurrencyEdit = QtWidgets.QLineEdit("EUR")
        # self.sepaIBANLabel = QtWidgets.QLabel(self.tr("IBAN:"))
        # self.sepaIBANEdit = QtWidgets.QLineEdit()
        # self.sepaBICLabel = QtWidgets.QLabel(self.tr("BIC:"))
        # self.sepaBICEdit = QtWidgets.QLineEdit()

        # Widgets for BIP0021 Bitcoin Address
        # Reference: https://en.bitcoin.it/wiki/BIP_0021
        self.bip21AddressLabel = QtWidgets.QLabel(self.tr("Address:"))
        self.bip21AddressEdit = QtWidgets.QLineEdit()
        self.bip21AmountLabel = QtWidgets.QLabel(self.tr("Amount:"))
        self.bip21AmountEdit = QtWidgets.QLineEdit()
        self.bip21LabelLabel = QtWidgets.QLabel(self.tr("Label:"))
        self.bip21LabelEdit = QtWidgets.QLineEdit()
        self.bip21MessageLabel = QtWidgets.QLabel(self.tr("Message:"))
        self.bip21MessageEdit = QtWidgets.QLineEdit()

        # Widgets for QREncode Parameters Configuration
        self.optionsGroup = QtWidgets.QGroupBox(self.tr("Parameters:"))

        self.l2 = QtWidgets.QLabel(self.tr("&Pixel Size:"))
        self.pixelSize = QtWidgets.QSpinBox()

        self.l3 = QtWidgets.QLabel(self.tr("&Error Correction:"))
        self.ecLevel = QtWidgets.QComboBox()
        self.ecLevel.addItems(
            (
                self.tr("Lowest"),
                self.tr("Medium"),
                self.tr("QuiteGood"),
                self.tr("Highest"),
            )
        )

        self.l4 = QtWidgets.QLabel(self.tr("&Margin Size:"))
        self.marginSize = QtWidgets.QSpinBox()

        self.addBom = QtWidgets.QCheckBox(self.tr("Add BOM character"))

        # QLabel for displaying the Generated QRCode
        self.qrcode = QtWidgets.QLabel(
            self.tr(
                "Start typing to create QR Code\n or  drop here image files for decoding."
            )
        )
        self.qrcode.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.qrcode)

        # Save and Decode Buttons
        self.saveButton = QtWidgets.QPushButton(
            QtGui.QIcon.fromTheme("document-save"), self.tr("&Save QRCode")
        )
        self.decodeButton = QtWidgets.QPushButton(
            QtGui.QIcon.fromTheme("preview-file"), self.tr("&Decode")
        )

        self.decodeFileButton = QtWidgets.QPushButton(
            QtGui.QIcon.fromTheme("document-open"), self.tr("Decode from &File")
        )
        self.decodeClipboardButton = QtWidgets.QPushButton(
            QtGui.QIcon.fromTheme("edit-paste"), self.tr("Decode from &Clipboard")
        )
        self.decodeWebcamButton = QtWidgets.QPushButton(
            QtGui.QIcon.fromTheme("camera-web"), self.tr("Decode from &Webcam")
        )

        self.exitAction = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("application-exit"), self.tr("E&xit"), self
        )
        self.addAction(self.exitAction)
        self.aboutAction = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("help-about"), self.tr("&About"), self
        )
        self.addAction(self.aboutAction)

        # UI Tunning
        self.saveButton.setEnabled(False)
        self.pixelSize.setValue(3)
        self.pixelSize.setMinimum(1)
        self.marginSize.setValue(4)
        self.l1.setBuddy(self.textEdit)
        self.l2.setBuddy(self.pixelSize)
        self.l3.setBuddy(self.ecLevel)
        self.l4.setBuddy(self.marginSize)
        self.ecLevel.setToolTip(self.tr("Error Correction Level"))
        self.l3.setToolTip(self.tr("Error Correction Level"))
        self.addBom.setToolTip(
            self.tr(
                'Uncheck this if you are having issues decoding your QR codes on mobile apps. Applies only to "Text" type.'
            )
        )
        self.decodeFileButton.setShortcut("Ctrl+O")
        self.decodeWebcamButton.setShortcut("Ctrl+W")
        self.saveButton.setShortcut("Ctrl+S")
        self.exitAction.setShortcut("Ctrl+Q")
        self.aboutAction.setShortcut("F1")

        self.buttons = QtWidgets.QHBoxLayout()
        self.buttons.addWidget(self.saveButton)
        self.buttons.addWidget(self.decodeClipboardButton)
        self.buttons.addWidget(self.decodeFileButton)
        self.buttons.addWidget(self.decodeWebcamButton)

        # Text Tab
        self.codeControls = QtWidgets.QVBoxLayout()
        self.codeControls.addWidget(self.l1)
        self.codeControls.addWidget(self.textEdit, 1)
        self.textTab.setLayout(self.codeControls)

        # URL Tab
        self.urlTabLayout = QtWidgets.QVBoxLayout()
        self.urlTabLayout.addWidget(self.urlLabel)
        self.urlTabLayout.addWidget(self.urlEdit)
        self.urlTabLayout.addStretch()
        self.urlTab.setLayout(self.urlTabLayout)

        # Bookmark Tab
        self.bookmarkTabLayout = QtWidgets.QVBoxLayout()
        self.bookmarkTabLayout.addWidget(self.bookmarkTitleLabel)
        self.bookmarkTabLayout.addWidget(self.bookmarkTitleEdit)
        self.bookmarkTabLayout.addWidget(self.bookmarkUrlLabel)
        self.bookmarkTabLayout.addWidget(self.bookmarkUrlEdit)
        self.bookmarkTabLayout.addStretch()
        self.bookmarkTab.setLayout(self.bookmarkTabLayout)

        # Email Tab
        self.emailTabLayout = QtWidgets.QVBoxLayout()
        self.emailTabLayout.addWidget(self.emailLabel)
        self.emailTabLayout.addWidget(self.emailEdit)
        self.emailTabLayout.addWidget(self.emailSubLabel)
        self.emailTabLayout.addWidget(self.emailSubjectEdit)
        self.emailTabLayout.addWidget(self.emailBodyLabel)
        self.emailTabLayout.addWidget(self.emailBodyEdit, 1)
        self.emailTabLayout.addStretch()
        self.emailTab.setLayout(self.emailTabLayout)

        # Telephone Tab
        self.telTabLayout = QtWidgets.QVBoxLayout()
        self.telTabLayout.addWidget(self.telephoneLabel)
        self.telTabLayout.addWidget(self.telephoneEdit)
        self.telTabLayout.addStretch()
        self.telTab.setLayout(self.telTabLayout)

        # Contact Tab
        self.phonebookTabLayout = QtWidgets.QVBoxLayout()
        self.phonebookTabLayout.addWidget(self.phonebookLoadButton)
        self.phonebookTabLayout.addWidget(self.phonebookNameLabel)
        self.phonebookTabLayout.addWidget(self.phonebookNameEdit)
        self.phonebookTabLayout.addWidget(self.phonebookTelLabel)
        self.phonebookTabLayout.addWidget(self.phonebookTelEdit)
        self.phonebookTabLayout.addWidget(self.phonebookEMailLabel)
        self.phonebookTabLayout.addWidget(self.phonebookEMailEdit)
        self.phonebookTabLayout.addWidget(self.phonebookNoteLabel)
        self.phonebookTabLayout.addWidget(self.phonebookNoteEdit)
        self.phonebookTabLayout.addWidget(self.phonebookBirthdayLabel)
        self.phonebookTabLayout.addWidget(self.phonebookBirthdayEdit)
        self.phonebookTabLayout.addWidget(self.phonebookAddressLabel)
        self.phonebookTabLayout.addWidget(self.phonebookAddressEdit)
        self.phonebookTabLayout.addWidget(self.phonebookUrlLabel)
        self.phonebookTabLayout.addWidget(self.phonebookUrlEdit)
        self.phonebookTabLayout.addStretch()
        self.phonebookTab.setLayout(self.phonebookTabLayout)

        # SMS Tab
        self.smsTabLayout = QtWidgets.QVBoxLayout()
        self.smsTabLayout.addWidget(self.smsNumberLabel)
        self.smsTabLayout.addWidget(self.smsNumberEdit)
        self.smsTabLayout.addWidget(self.smsBodyLabel)
        self.smsTabLayout.addWidget(self.smsBodyEdit, 1)
        self.smsTabLayout.addWidget(self.smsCharCount)
        self.smsTabLayout.addStretch()
        self.smsTab.setLayout(self.smsTabLayout)

        # MMS Tab
        self.mmsTabLayout = QtWidgets.QVBoxLayout()
        self.mmsTabLayout.addWidget(self.mmsNumberLabel)
        self.mmsTabLayout.addWidget(self.mmsNumberEdit)
        self.mmsTabLayout.addWidget(self.mmsBodyLabel)
        self.mmsTabLayout.addWidget(self.mmsBodyEdit, 1)
        self.mmsTabLayout.addStretch()
        self.mmsTab.setLayout(self.mmsTabLayout)

        # Geolocalization Tab
        self.geoTabLayout = QtWidgets.QVBoxLayout()
        self.geoTabLayout.addWidget(self.geoLatLabel)
        self.geoTabLayout.addWidget(self.geoLatEdit)
        self.geoTabLayout.addWidget(self.geoLongLabel)
        self.geoTabLayout.addWidget(self.geoLongEdit)
        self.geoTabLayout.addStretch()
        self.geoTab.setLayout(self.geoTabLayout)

        # WiFi Network Tab
        self.wifiTabLayout = QtWidgets.QVBoxLayout()
        self.wifiTabLayout.addWidget(self.wifiSSIDLabel)
        self.wifiTabLayout.addWidget(self.wifiSSIDEdit)
        self.wifiTabLayout.addWidget(self.wifiPasswordLabel)
        self.wifiTabLayout.addWidget(self.wifiPasswordEdit)
        self.wifiTabLayout.addWidget(self.wifiShowPassword)
        self.wifiShowPassword.setChecked(True)
        self.wifiTabLayout.addWidget(self.wifiEncryptionLabel)
        self.wifiTabLayout.addWidget(self.wifiEncryptionType)
        self.wifiTabLayout.addWidget(self.wifiHiddenNetwork)
        self.wifiTabLayout.addStretch()
        self.wifiTab.setLayout(self.wifiTabLayout)

        # SEPA Tab
        self.sepaTabLayout = QtWidgets.QVBoxLayout()
        self.sepaTabLayout.addWidget(self.sepaNameLabel)
        self.sepaTabLayout.addWidget(self.sepaNameEdit)
        self.sepaTabLayout.addWidget(self.sepaAccountLabel)
        self.sepaTabLayout.addWidget(self.sepaAccountEdit)
        self.sepaTabLayout.addWidget(self.sepaBNCLabel)
        self.sepaTabLayout.addWidget(self.sepaBNCEdit)
        self.sepaTabLayout.addWidget(self.sepaAmountLabel)
        self.sepaTabLayout.addWidget(self.sepaAmountEdit)
        self.sepaTabLayout.addWidget(self.sepaReasonLabel)
        self.sepaTabLayout.addWidget(self.sepaReasonEdit)
        self.sepaTabLayout.addWidget(self.sepaCurrencyLabel)
        self.sepaTabLayout.addWidget(self.sepaCurrencyEdit)
        self.sepaTabLayout.addStretch()
        self.sepaTab.setLayout(self.sepaTabLayout)

        # BIP21 Tab
        self.bip21TabLayout = QtWidgets.QVBoxLayout()
        self.bip21TabLayout.addWidget(self.bip21AddressLabel)
        self.bip21TabLayout.addWidget(self.bip21AddressEdit)
        self.bip21TabLayout.addWidget(self.bip21AmountLabel)
        self.bip21TabLayout.addWidget(self.bip21AmountEdit)
        self.bip21TabLayout.addWidget(self.bip21LabelLabel)
        self.bip21TabLayout.addWidget(self.bip21LabelEdit)
        self.bip21TabLayout.addWidget(self.bip21MessageLabel)
        self.bip21TabLayout.addWidget(self.bip21MessageEdit)
        self.bip21TabLayout.addStretch()
        self.bip21Tab.setLayout(self.bip21TabLayout)

        # Pixel Size Controls
        self.pixControls = QtWidgets.QVBoxLayout()
        self.pixControls.addWidget(self.l2)
        self.pixControls.addWidget(self.pixelSize)

        # Error Correction Level Controls
        self.levelControls = QtWidgets.QVBoxLayout()
        self.levelControls.addWidget(self.l3)
        self.levelControls.addWidget(self.ecLevel)

        # Margin Size Controls
        self.marginControls = QtWidgets.QVBoxLayout()
        self.marginControls.addWidget(self.l4)
        self.marginControls.addWidget(self.marginSize)

        # BOM Char Controls
        self.bomControls = QtWidgets.QVBoxLayout()
        self.bomControls.addWidget(self.addBom)

        # Controls Layout
        self.controls = QtWidgets.QHBoxLayout()
        self.controls.addLayout(self.pixControls)
        self.controls.addSpacing(10)
        self.controls.addLayout(self.levelControls)
        self.controls.addSpacing(10)
        self.controls.addLayout(self.marginControls)
        self.controls.addSpacing(10)
        self.controls.addLayout(self.bomControls)
        self.controls.addStretch()
        self.optionsGroup.setLayout(self.controls)

        # Main Window Layout
        self.selectorBox = QtWidgets.QGroupBox(self.tr("Select data type:"))

        self.vlayout1 = QtWidgets.QVBoxLayout()
        self.vlayout1.addWidget(self.selector)
        self.vlayout1.addWidget(self.tabs, 1)

        self.vlayout2 = QtWidgets.QVBoxLayout()
        self.vlayout2.addWidget(self.optionsGroup)
        self.vlayout2.addWidget(self.scroll, 1)
        self.vlayout2.addLayout(self.buttons)

        self.layout = QtWidgets.QHBoxLayout(self.w)
        self.selectorBox.setLayout(self.vlayout1)
        self.layout.addWidget(self.selectorBox)
        self.layout.addLayout(self.vlayout2, 1)

        # Signals
        self.selector.currentIndexChanged.connect(self.tabs.setCurrentIndex)
        self.tabs.currentChanged.connect(self.selector.setCurrentIndex)
        self.textEdit.textChanged.connect(self.qrencode)
        self.urlEdit.textChanged.connect(self.qrencode)
        self.bookmarkTitleEdit.textChanged.connect(self.qrencode)
        self.bookmarkUrlEdit.textChanged.connect(self.qrencode)
        self.emailEdit.textChanged.connect(self.qrencode)
        self.emailSubjectEdit.textChanged.connect(self.qrencode)
        self.emailBodyEdit.textChanged.connect(self.qrencode)
        self.phonebookNameEdit.textChanged.connect(self.qrencode)
        self.phonebookTelEdit.textChanged.connect(self.qrencode)
        self.phonebookEMailEdit.textChanged.connect(self.qrencode)
        self.phonebookNoteEdit.textChanged.connect(self.qrencode)
        self.phonebookAddressEdit.textChanged.connect(self.qrencode)
        self.phonebookBirthdayLabel.stateChanged.connect(self.qrencode)
        self.phonebookBirthdayEdit.dateChanged.connect(self.qrencode)
        self.phonebookUrlEdit.textChanged.connect(self.qrencode)
        self.phonebookLoadButton.clicked.connect(self.loadVCardFile)
        self.smsNumberEdit.textChanged.connect(self.qrencode)
        self.smsBodyEdit.textChanged.connect(self.qrencode)
        self.smsBodyEdit.textChanged.connect(
            lambda: self.smsCharCount.setText(
                str(self.tr("characters count: %s - %d message(s)"))
                % (
                    len(self.smsBodyEdit.toPlainText()),
                    ceil(len(self.smsBodyEdit.toPlainText()) / 160.0),
                )
            )
        )
        self.mmsNumberEdit.textChanged.connect(self.qrencode)
        self.mmsBodyEdit.textChanged.connect(self.qrencode)
        self.telephoneEdit.textChanged.connect(self.qrencode)
        self.geoLatEdit.textChanged.connect(self.qrencode)
        self.geoLongEdit.textChanged.connect(self.qrencode)
        self.wifiSSIDEdit.textChanged.connect(self.qrencode)
        self.wifiPasswordEdit.textChanged.connect(self.qrencode)
        self.wifiShowPassword.stateChanged.connect(self.toggleShowPassword)
        self.wifiEncryptionType.currentIndexChanged.connect(self.qrencode)
        self.wifiHiddenNetwork.stateChanged.connect(self.qrencode)
        self.sepaNameEdit.textChanged.connect(self.qrencode)
        self.sepaAccountEdit.textChanged.connect(self.qrencode)
        self.sepaBNCEdit.textChanged.connect(self.qrencode)
        self.sepaAmountEdit.textChanged.connect(self.qrencode)
        self.sepaReasonEdit.textChanged.connect(self.qrencode)
        self.sepaCurrencyEdit.textChanged.connect(self.qrencode)
        self.bip21LabelEdit.textChanged.connect(self.qrencode)
        self.bip21AddressEdit.textChanged.connect(self.qrencode)
        self.bip21MessageEdit.textChanged.connect(self.qrencode)
        self.bip21AmountEdit.textChanged.connect(self.qrencode)

        self.pixelSize.valueChanged.connect(self.qrencode)
        self.ecLevel.currentIndexChanged.connect(self.qrencode)
        self.marginSize.valueChanged.connect(self.qrencode)
        self.addBom.stateChanged.connect(self.qrencode)
        self.saveButton.clicked.connect(self.saveCode)
        self.exitAction.triggered.connect(self.close)
        self.aboutAction.triggered.connect(self.about)
        self.decodeFileButton.clicked.connect(self.decodeFile)
        self.decodeClipboardButton.clicked.connect(self.decodeClipboard)
        self.decodeWebcamButton.clicked.connect(self.decodeWebcam)

        self.qrcode.setAcceptDrops(True)
        self.qrcode.__class__.dragEnterEvent = self.dragEnterEvent
        self.qrcode.__class__.dropEvent = self.dropEvent
        self.qrcode.__class__.closeEvent = self.closeEvent

        # Network acces for remote images drag&drop support
        self.NetAccessMgr = QtNetwork.QNetworkAccessManager()
        self.NetAccessMgr.finished.connect(self.handleNetworkData)

        self.read_settings()

    def read_settings(self):
        """Read saved Window settings such as position"""
        self.settings = QtCore.QSettings("qr-tools", "QtQR")
        self.settings.beginGroup("MainWindow")
        self.resize(self.settings.value("size", QtCore.QSize(10, 10)))
        self.move(self.settings.value("pos", QtCore.QPoint(10, 10)))
        self.pixelSize.setValue(int(self.settings.value("pixelSize", "3")))
        self.ecLevel.setCurrentIndex(int(self.settings.value("errorCorrection", 0)))
        self.marginSize.setValue(int(self.settings.value("marginSize", 4)))
        self.addBom.setChecked((self.settings.value("addBom", "true")) == "true")
        self.settings.endGroup()

    def write_settings(self):
        """Save Window settings such as position"""
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("pixelSize", self.pixelSize.value())
        self.settings.setValue("errorCorrection", self.ecLevel.currentIndex())
        self.settings.setValue("marginSize", self.marginSize.value())
        self.settings.setValue("addBom", self.addBom.isChecked())
        self.settings.endGroup()

    def qrencode(self, *args, **kargs):
        fileName = kargs.get("fileName")
        # Functions to get the correct data
        data_fields = {
            "text": str(self.textEdit.toPlainText()),
            "url": str(self.urlEdit.text()),
            "bookmark": (
                str(self.bookmarkTitleEdit.text()),
                str(self.bookmarkUrlEdit.text()),
            ),
            "email": str(self.emailEdit.text()),
            "emailmessage": (
                str(self.emailEdit.text()),
                str(self.emailSubjectEdit.text()),
                str(self.emailBodyEdit.toPlainText()),
            ),
            "telephone": str(self.telephoneEdit.text()),
            "phonebook": (
                ("N", str(self.phonebookNameEdit.text())),
                ("TEL", str(self.phonebookTelEdit.text())),
                ("EMAIL", str(self.phonebookEMailEdit.text())),
                ("NOTE", str(self.phonebookNoteEdit.text())),
                (
                    "BDAY",
                    str(self.phonebookBirthdayEdit.date().toString("yyyyMMdd"))
                    if self.phonebookBirthdayLabel.isChecked()
                    else "",
                ),  # YYYYMMDD
                (
                    "ADR",
                    str(self.phonebookAddressEdit.text()),
                ),  # The fields divided by commas (,) denote PO box, room number, house number, city, prefecture, zip code and country, in order.
                ("URL", str(self.phonebookUrlEdit.text())),
                # ('NICKNAME', ''),
            ),
            "sms": (
                str(self.smsNumberEdit.text()),
                str(self.smsBodyEdit.toPlainText()),
            ),
            "mms": (
                str(self.mmsNumberEdit.text()),
                str(self.mmsBodyEdit.toPlainText()),
            ),
            "geo": (str(self.geoLatEdit.text()), str(self.geoLongEdit.text())),
            "wifi": (
                str(self.wifiSSIDEdit.text()),
                ("WEP", "WPA", "nopass")[self.wifiEncryptionType.currentIndex()],
                str(self.wifiPasswordEdit.text()),
                str("true" if self.wifiHiddenNetwork.isChecked() else ""),
            ),
            "sepa": (
                str(self.sepaNameEdit.text()),
                str(self.sepaAccountEdit.text()),
                str(self.sepaBNCEdit.text()),
                str(self.sepaAmountEdit.text()),
                str(self.sepaReasonEdit.text()),
                str(self.sepaCurrencyEdit.text()),
            ),
            "bip21": (
                str(self.bip21AddressEdit.text()),
                str(self.bip21AmountEdit.text()),
                str(self.bip21LabelEdit.text()),
                str(self.bip21MessageEdit.text()),
            ),
        }

        data_type = str(self.templates[str(self.selector.currentText())])
        data = data_fields[data_type]

        level = ("L", "M", "Q", "H")

        if data:
            if data_type == "emailmessage" and data[1] == "" and data[2] == "":
                data_type = "email"
                data = data_fields[data_type]
            qr = QR(
                pixel_size=str(self.pixelSize.value()),
                data=data,
                level=str(level[self.ecLevel.currentIndex()]),
                margin_size=str(self.marginSize.value()),
                data_type=data_type,
                add_bom=self.addBom.isChecked(),
            )
            error = 1
            if not isinstance(fileName, str):
                try:
                    error = qr.encode()
                except QR.EncodeError as e:
                    print("Error while encoding: ", e)
                    error = 2
            else:
                error = qr.encode(fileName)
            if error == 0:
                self.qrcode.setPixmap(QtGui.QPixmap(qr.filename))
                self.saveButton.setEnabled(True)
            elif error == 2:
                QtWidgets.QMessageBox.information(
                    self, self.tr("Bad input"), self.tr("Invalid input data")
                )
            else:
                print("Something went wrong while trying to generate the QR Code")
            qr.destroy()
        else:
            self.saveButton.setEnabled(False)
        self.write_settings()

    def saveCode(self):
        filterStr = ""
        showFileExtensionWarning = False
        for saveType in QR().get_qrencode_types():
            filterStr += saveType + "(*." + saveType.lower() + ");;"
        fn = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr("Save QRCode"), filter=filterStr
        )
        if fn != ("", ""):
            filePath, fileExtension = fn
            if os.path.splitext(filePath)[1] == "":
                # FIXME: qrtools uses the file extension to detect the file type.
                # if the file does not have an explicit extension, qrtools will fall back to PNG and add the '.png' extension to the filename.
                # To prevent this, we add always the extension of the chosen format.
                # This needs to be fixed in qrtools.
                print(
                    f"WARN: chosen file path {filePath} does not have an explicit extension. Adding {fileExtension} to it so qrtools does not crash."
                )
                filePath += "." + fileExtension.split("(")[0].lower()
                print(f"New file path is: {filePath}")
                showFileExtensionWarning = True
            self.qrencode(fileName=str(filePath))
            QtWidgets.QMessageBox.information(
                self,
                str(self.tr("Save QRCode")),
                str(self.tr("QRCode succesfully saved to <b>%s</b>.")) % filePath,
            )
            if showFileExtensionWarning:
                QtWidgets.QMessageBox.warning(
                    self,
                    "File name change",
                    "The file name entered does not have an explicit extension. We added it for you, otherwise the QR generation will fail.\nYou can rename the file once created if you prefer.\n\nThis is a bug and will be fixed in future versions. Sorry for the inconvenience.",
                )

    def decodeFile(self, fn=None):
        if not fn:
            fn, fter = QtWidgets.QFileDialog.getOpenFileName(
                self,
                self.tr("Open QRCode"),
                filter=self.tr("Images (*.png *.jpg);; All Files (*.*)"),
            )
            if fn:
                fn = str(fn)
            else:
                return
        if os.path.isfile(fn):
            qr = QR(filename=fn)
            decode_result = None

            try:
                decode_result = qr.decode()
            except IOError:
                # raised by GIL when not an image
                decode_result = False

            if decode_result:
                self.showInfo(qr)
            else:
                QtWidgets.QMessageBox.information(
                    self,
                    self.tr("Decode File"),
                    str(self.tr("No QRCode could be found in file: <b>%s</b>.")) % fn,
                )
            qr.destroy()
        else:
            QtWidgets.QMessageBox.information(
                self,
                "Decode from file",
                "The file <b>%s</b> doesn't exist." % os.path.abspath(fn),
                QtWidgets.QMessageBox.Ok,
            )

    def decodeFromMemory(self, image):
        qr = QR()
        decode_result = None

        try:
            decode_result = qr.decode(image=image)
        except IOError:
            # raised by GIL when not an image
            decode_result = False

        if decode_result:
            self.showInfo(qr)
        else:
            QtWidgets.QMessageBox.information(
                self,
                self.tr("Decode Image"),
                str(self.tr("No QRCode could be found in dropped file.")),
            )
        qr.destroy()

    def decodeClipboard(self):
        clipboard = QtWidgets.QApplication.clipboard()
        qimage = clipboard.image()
        if qimage.isNull():
            QtWidgets.QMessageBox.information(
                self,
                self.tr("Decode from Clipboard"),
                self.tr("No image found in clipboard."),
            )
            return
        buffer = QtCore.QBuffer()
        buffer.open(QtCore.QBuffer.ReadWrite)
        qimage.save(buffer, "PNG")
        pil_image = Image.open(io.BytesIO(bytes(buffer.data())))
        self.decodeFromMemory(pil_image)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Paste):
            if not QtWidgets.QApplication.clipboard().image().isNull():
                self.decodeClipboard()
                return
        super().keyPressEvent(event)

    def showInfo(self, qr):
        dt = qr.data_type
        print(str(dt) + ":", end="")
        data = qr.data_decode[dt](qr.data)
        if type(data) == tuple:
            for d in data:
                print(d.encode("utf-8"))
        elif isinstance(data, dict):
            # FIXME: Print the decoded symbols
            print("Dict")
            print(data.keys())
            print(data.values())
        else:
            print(data.encode("utf-8"))
        msg = {
            "text": lambda: str(self.tr("QRCode contains the following text:\n\n%s"))
            % (data),
            "url": lambda: str(
                self.tr("QRCode contains the following url address:\n\n%s")
            )
            % (data),
            "bookmark": lambda: str(
                self.tr("QRCode contains a bookmark:\n\nTitle: %s\nURL: %s")
            )
            % (data),
            "email": lambda: str(
                self.tr("QRCode contains the following e-mail address:\n\n%s")
            )
            % (data),
            "emailmessage": lambda: str(
                self.tr(
                    "QRCode contains an e-mail message:\n\nTo: %s\nSubject: %s\nMessage: %s"
                )
            )
            % (data),
            "telephone": lambda: str(self.tr("QRCode contains a telephone number: "))
            + (data),
            "phonebook": lambda: str(
                self.tr(
                    "QRCode contains a phonebook entry:\n\nName: %s\nTel: %s\nE-Mail: %s\nNote: %s\nBirthday: %s\nAddress: %s\nURL: %s"
                )
            )
            % (
                data.get("N") or "",
                data.get("TEL") or "",
                data.get("EMAIL") or "",
                data.get("NOTE") or "",
                QtCore.QDate.fromString(data.get("BDAY") or "", "yyyyMMdd").toString(),
                data.get("ADR") or "",
                data.get("URL") or "",
            ),
            "sms": lambda: str(
                self.tr(
                    "QRCode contains the following SMS message:\n\nTo: %s\nMessage: %s"
                )
            )
            % (data),
            "mms": lambda: str(
                self.tr(
                    "QRCode contains the following MMS message:\n\nTo: %s\nMessage: %s"
                )
            )
            % (data),
            "geo": lambda: str(
                self.tr(
                    "QRCode contains the following coordinates:\n\nLatitude: %s\nLongitude:%s"
                )
            )
            % (data),
            "wifi": lambda: str(
                self.tr(
                    "QRCode contains the following WiFi Network Configuration:\n\nSSID: %s\nEncryption Type: %s\nPassword: %s\nHidden network: %s\n"
                )
            )
            % (data),
            "sepa": lambda: str(
                self.tr(
                    "QRCode contains the following Single Payment Information:\n\nName: %s\nAccount: %s\nBNC: %s\nAmmount: %s\nReason: %s\nCurrency: %s\n"
                )
            )
            % (
                data.get("name")[0] or "",
                data.get("account")[0] or "",
                data.get("bnc")[0] or "",
                data.get("amount")[0] or "",
                data.get("reason")[0] or "",
                data.get("currency")[0] or "",
            ),
            "bip21": lambda: str(
                self.tr(
                    "QRCode contains the following Bitcoin information:\n\nAddress: %s\nAmount: %s\nLabel: %s\nMessage: %s"
                )
            )
            % (
                data.get("address") or "",
                " ".join(data.get("options").get("amount") or [])
                if data.get("options")
                else "",
                " ".join(data.get("options").get("label") or [])
                if data.get("options")
                else "",
                " ".join(data.get("options").get("message") or [])
                if data.get("options")
                else "",
            ),
        }
        wanna = self.tr("\n\nDo you want to ")
        action = {
            "text": "",
            "url": wanna + self.tr("open it in a browser?"),
            "bookmark": wanna + self.tr("open it in a browser?"),
            "email": wanna + self.tr("send an e-mail to the address?"),
            "emailmessage": wanna + self.tr("send the e-mail?"),
            "telephone": "",
            "phonebook": "",
            "sms": "",
            "mms": "",
            "geo": wanna + self.tr("open it in Google Maps?"),
            "wifi": "",
            "sepa": "",
            "bip21": "",
        }
        if action[qr.data_type] != "":
            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Question,
                self.tr("Decode QRCode"),
                msg[qr.data_type]() + action[qr.data_type],
                QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes,
                self,
            )
            msgBox.addButton(self.tr("&Edit"), QtWidgets.QMessageBox.ApplyRole)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Yes)
            rsp = msgBox.exec_()
        else:
            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Information,
                self.tr("Decode QRCode"),
                msg[qr.data_type]() + action[qr.data_type],
                QtWidgets.QMessageBox.Ok,
                self,
            )
            msgBox.addButton(self.tr("&Edit"), QtWidgets.QMessageBox.ApplyRole)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            rsp = msgBox.exec_()

        if rsp == QtWidgets.QMessageBox.Yes:
            # Open Link
            if qr.data_type == "email":
                link = "mailto:" + data
            elif qr.data_type == "emailmessage":
                link = "mailto:%s?subject=%s&body=%s" % (data)
            elif qr.data_type == "geo":
                link = "http://maps.google.com/maps?q=%s,%s" % data
            elif qr.data_type == "bookmark":
                link = data[1]
            else:
                link = qr.data_decode[qr.data_type](qr.data)
            print("Opening " + link)
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(link))
        elif rsp == 0:
            # Edit the code
            data = qr.data_decode[qr.data_type](qr.data)
            try:
                tabIndex = self.templateNames.index(self.templates[qr.data_type])
            except KeyError:
                if qr.data_type == "email":
                    # We have to use the same tab index as EMail Message
                    tabIndex = self.templateNames.index(self.templates["emailmessage"])
            if qr.data_type == "text":
                self.tabs.setCurrentIndex(tabIndex)
                self.textEdit.setPlainText(data)
            elif qr.data_type == "url":
                self.tabs.setCurrentIndex(tabIndex)
                self.urlEdit.setText(data)
            elif qr.data_type == "bookmark":
                self.bookmarkTitleEdit.setText(data[0])
                self.bookmarkUrlEdit.setText(data[1])
                self.tabs.setCurrentIndex(tabIndex)
            elif qr.data_type == "emailmessage":
                self.emailEdit.setText(data[0])
                self.emailSubjectEdit.setText(data[1])
                self.emailBodyEdit.setPlainText(data[2])
                self.tabs.setCurrentIndex(tabIndex)
            elif qr.data_type == "email":
                self.emailEdit.setText(data)
                self.emailSubjectEdit.setText("")
                self.emailBodyEdit.setPlainText("")
                self.tabs.setCurrentIndex(tabIndex)
            elif qr.data_type == "telephone":
                self.telephoneEdit.setText(data)
                self.tabs.setCurrentIndex(tabIndex)
            elif qr.data_type == "phonebook":
                self.phonebookNameEdit.setText(data.get("N") or "")
                self.phonebookTelEdit.setText(data.get("TEL") or "")
                self.phonebookEMailEdit.setText(data.get("EMAIL") or "")
                self.phonebookNoteEdit.setText(data.get("NOTE") or "")
                if data.get("BDAY"):
                    self.phonebookBirthdayEdit.setDate(
                        QtCore.QDate.fromString(data.get("BDAY"), "yyyyMMdd")
                    )
                    self.phonebookBirthdayLabel.setChecked(True)
                self.phonebookAddressEdit.setText(data.get("ADR") or "")
                self.phonebookUrlEdit.setText(data.get("URL") or "")
                self.tabs.setCurrentIndex(tabIndex)
            elif qr.data_type == "sms":
                self.smsNumberEdit.setText(data[0])
                self.smsBodyEdit.setPlainText(data[1])
                self.tabs.setCurrentIndex(tabIndex)
            elif qr.data_type == "mms":
                self.mmsNumberEdit.setText(data[0])
                self.mmsBodyEdit.setPlainText(data[1])
                self.tabs.setCurrentIndex(tabIndex)
            elif qr.data_type == "geo":
                self.geoLatEdit.setText(data[0])
                self.geoLongEdit.setText(data[1])
                self.tabs.setCurrentIndex(tabIndex)
            elif qr.data_type == "wifi":
                self.wifiSSIDEdit.setText(data[0] or "")
                self.wifiEncryptionType.setCurrentIndex(
                    {"WEP": 0, "WPA": 1, "nopass": 2}.get(data[1]) or 0
                )
                self.wifiPasswordEdit.setText(data[2] or "")
                self.wifiHiddenNetwork.setCheckState(
                    True if data[3] == "true" else False
                )
                self.tabs.setCurrentIndex(tabIndex)
            elif qr.data_type == "sepa":
                self.sepaNameEdit.setText(data.get("name")[0])
                self.sepaAccountEdit.setText(data.get("account")[0])
                self.sepaBNCEdit.setText(data.get("bnc")[0])
                self.sepaAmountEdit.setText(data.get("amount")[0])
                self.sepaReasonEdit.setText(data.get("reason")[0])
                self.sepaCurrencyEdit.setText(data.get("currency")[0])
                self.tabs.setCurrentIndex(tabIndex)
            elif qr.data_type == "bip21":
                self.bip21AddressEdit.setText(data.get("address"))
                self.bip21LabelEdit.setText(
                    " ".join(data.get("options").get("label") or [])
                    if data.get("options")
                    else ""
                )
                self.bip21MessageEdit.setText(
                    " ".join(data.get("options").get("message") or [])
                    if data.get("options")
                    else ""
                )
                self.bip21AmountEdit.setText(
                    " ".join(data.get("options").get("amount") or [])
                    if data.get("options")
                    else ""
                )
                self.tabs.setCurrentIndex(tabIndex)

    def decodeWebcam(self):
        vdDialog = VideoDevices()
        device_desc = vdDialog.videoDevice.currentText()
        if vdDialog.videoDevice.count() != 1:
            d_res = vdDialog.exec_()
            device_desc = {
                QDialog.Rejected: "",
                QDialog.Accepted: vdDialog.videoDevice.currentText(),
            }[d_res]
        device = {
            device.description(): device.deviceName()
            for device in QCameraInfo.availableCameras()
        }.get(device_desc, None)

        if device:
            qr = QR()
            qr.decode_webcam(device=device)
            try:
                matchData = qr.data_decode[qr.data_type](qr.data)
            except IndexError:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.tr("Decoding Failed"),
                    self.tr(
                        f"<p>oops! Your code seems to be of type '{qr.data_type}', but no decoding for data '{qr.data}' could be found.</p>"
                    ),
                    QtWidgets.QMessageBox.Ok,
                )
            else:
                if matchData == "NULL":
                    QtWidgets.QMessageBox.warning(
                        self,
                        self.tr("Decoding Failed"),
                        self.tr(
                            "<p>Oops! no code was found.<br /> Maybe your webcam didn't focus.</p>"
                        ),
                        QtWidgets.QMessageBox.Ok,
                    )
                else:
                    self.showInfo(qr)

            qr.destroy()

    def about(self):
        QtWidgets.QMessageBox.about(
            self,
            self.tr("About QtQR"),
            str(
                self.tr(
                    '<h1>QtQR %s</h1><p>A simple software for creating and decoding QR Codes that uses python-qrtools as backend. Both are part of the <a href="https://launchpad.net/qr-tools">QR Tools</a> project.</p><p></p><p>This is Free Software: GNU-GPLv3</p><p></p><p>Please visit our website for more information and to check out the code:<br /><a href="https://code.launchpad.net/qr-tools/">https://code.launchpad.net/qr-tools/</p><p>copyright &copy; Ramiro Algozino &lt;<a href="mailto:algozino@gmail.com">algozino@gmail.com</a>&gt;</p>'
                )
            )
            % __version__,
        )

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            fn = url.toLocalFile()
            if fn:
                self.decodeFile(str(fn))
            else:
                print("DEBUG: Downloading dropped file from %s" % url.toString())
                self.NetAccessMgr.get(QtNetwork.QNetworkRequest(url))
                # FIX-ME: We should check if the download gets timeout.
                # and notify that we are downloading, the download could
                # take some seconds to complete.

    def closeEvent(self, event):
        self.write_settings()

    def handleNetworkData(self, QNetReply):
        print("DEBUG: Finished downloading file.")
        image_bytes = Image.io.BytesIO(bytes(QNetReply.readAll()))
        image = Image.open(image_bytes)
        self.decodeFromMemory(image)

    def toggleShowPassword(self, status):
        if status == 0:
            self.wifiPasswordEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        elif status == 2:
            self.wifiPasswordEdit.setEchoMode(QtWidgets.QLineEdit.Normal)

    def loadVCardFile(self, fn=None):
        """
        Implements the Load VCard from file dialog and puts the data into the right widgets.
        """
        if fn is None:
            fn, fter = QtWidgets.QFileDialog.getOpenFileName(
                self,
                self.tr("Open VCard File"),
                filter=self.tr("VCard (*.vcard *.vcf);; All Files (*.*)"),
            )
            if fn:
                fn = str(fn)
            else:
                # the user cancelled the dialog
                return
        if os.path.isfile(fn):
            # TODO
            vcf = VCF(fn)
            if vcf.properties == {}:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Load VCard Failed",
                    "We could not extract data from the file <b>%s</b>."
                    % os.path.abspath(fn),
                    QtWidgets.QMessageBox.Ok,
                )
            else:
                data = vcf.toMeCard()
                # print("DEBUG: mecard is:", data)
                # FIXME: we are duplicating this logic from the load from file method.
                self.phonebookNameEdit.setText(data.get("N") or "")
                self.phonebookTelEdit.setText(data.get("TEL") or "")
                self.phonebookEMailEdit.setText(data.get("EMAIL") or "")
                self.phonebookNoteEdit.setText(data.get("NOTE") or "")
                if data.get("BDAY"):
                    self.phonebookBirthdayEdit.setDate(
                        QtCore.QDate.fromString(data.get("BDAY"), "yyyyMMdd")
                    )
                    self.phonebookBirthdayLabel.setChecked(True)
                self.phonebookAddressEdit.setText(data.get("ADR") or "")
                self.phonebookUrlEdit.setText(data.get("URL") or "")
                self.tabs.setCurrentIndex(
                    self.templateNames.index(self.templates["phonebook"])
                )
                self.qrencode()
        else:
            QtWidgets.QMessageBox.information(
                self,
                "Decode from file",
                "The file <b>%s</b> doesn't exist." % os.path.abspath(fn),
                QtWidgets.QMessageBox.Ok,
            )


class VCF:
    """
    A very basic implementation of VCards file format
    We don't handle all of the available properties, we just focus on the ones
    that we need for the MECARD QR Codes.
    TODO: may be it is better to have this implementation in a separated file or even a dedicated library.
    """

    def __init__(self, fn=None):
        self.fn = fn
        self.plainText = ""
        self.properties = {}
        self.meCardProperties = [
            "N",
            "URL",
            "TEL",
            "ADR",
            "BDAY",
            "LABEL",
            "EMAIL",
            "NOTE",
        ]

        if fn is not None:
            self.decodeFile()

    def decodeFile(self):
        """
        Decode a vcf (VCard) file, just the basic fields.
        Returns True if success, False if something is wrong.
        This will override entries that are repeated, like having 2 URLs will keep the latest one.
        """
        with open(self.fn) as vcard:
            self.plainText = vcard.read()
            lines = self.plainText.splitlines()
            if len(lines) < 2:
                # Just one line means something is wrong.
                return False
            if lines[0] == ("BEGIN:VCARD") and lines[-1] == ("END:VCARD"):
                for line in lines[1:-1]:
                    key, value = line.split(":", maxsplit=1)
                    # TODO: here we drop some important information when keeping the first split.
                    self.properties[key.split(";")[0]] = value
                return True
            else:
                return False

    def toMeCard(self):
        """Returns only the properties needed by MeCard"""
        mecard = {}
        for key in self.meCardProperties:
            mecard[key] = self.properties.get(key)
        return mecard


class VideoDevices(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)

        self.setWindowTitle(self.tr("Decode from Webcam"))
        self.cameraIcon = QtGui.QIcon.fromTheme("camera")
        self.icon = QtWidgets.QLabel()
        self.icon.setPixmap(self.cameraIcon.pixmap(64, 64).scaled(64, 64))
        self.videoDevice = QtWidgets.QComboBox()
        self.label = QtWidgets.QLabel(
            self.tr(
                "You are about to decode from your webcam. Please put the code in front of your camera with a good light source and keep it steady.\nQtQR will try to detect automatically the QR Code.\n\nPlease select the video device you want to use for decoding:"
            )
        )
        self.label.setWordWrap(True)
        self.Buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self.Buttons.accepted.connect(self.accept)
        self.Buttons.rejected.connect(self.reject)
        self.layout = QtWidgets.QVBoxLayout()
        self.hlayout = QtWidgets.QHBoxLayout()
        self.vlayout = QtWidgets.QVBoxLayout()
        self.hlayout.addWidget(self.icon, 0, QtCore.Qt.AlignTop)
        self.vlayout.addWidget(self.label)
        self.vlayout.addWidget(self.videoDevice)
        self.hlayout.addLayout(self.vlayout)
        self.layout.addLayout(self.hlayout)
        self.layout.addStretch()
        self.layout.addWidget(self.Buttons)
        self.setLayout(self.layout)
        self.videoDevice.addItems(
            [info.description() for info in QCameraInfo.availableCameras()]
        )


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setDesktopFileName("qtqr")

    # This is to make Qt use locale configuration; i.e. Standard Buttons
    # in your system's language.
    locale = str(QtCore.QLocale.system().name())
    translator = QtCore.QTranslator()

    # We load from standard location the translations
    translator.load(
        "qtqr_" + locale,
        QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath),
    )
    app.installTranslator(translator)
    qtTranslator = QtCore.QTranslator()
    qtTranslator.load(
        "qt_" + locale,
        QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath),
    )
    app.installTranslator(qtTranslator)

    mw = MainWindow()
    mw.show()

    if len(sys.argv) > 1:
        if sys.argv[1] in ("--version", "-v"):
            print("QtQR version", __version__)
            sys.exit(0)
        # Open the file and try to decode it
        for fn in sys.argv[1:]:
            # We should check if the file exists.
            ext = os.path.splitext(fn)[1]
            if ext == ".vcf" or ext == ".vcard":
                print(
                    "WARN: loading data from a vCard file may result in data loss. QtQR does not support all the available fields and keeps the last occurrence for duplicated entries (like several telephone numbers)"
                )
                mw.loadVCardFile(fn)
            else:
                mw.decodeFile(fn)
    sys.exit(app.exec_())
