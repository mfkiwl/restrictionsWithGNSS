#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------
# Tim Hancock 2017

"""
Series of functions to deal with restrictionsInProposals. Defined as static functions to allow them to be used in forms ... (not sure if this is the best way ...)

"""
from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QAction,
    QDialogButtonBox,
    QLabel,
    QDockWidget,
    QDialog,
    QLabel,
    QPushButton,
    QApplication
)

from qgis.PyQt.QtGui import (
    QIcon,
    QPixmap,
    QImage
)

from qgis.PyQt.QtCore import (
    QObject,
    QTimer,
    QThread,
    pyqtSignal,
    pyqtSlot
)

from qgis.PyQt.QtSql import (
    QSqlDatabase
)

from qgis.core import (
    QgsExpressionContextScope,
    QgsExpressionContextUtils,
    QgsExpression,
    QgsFeatureRequest,
    QgsMessageLog,
    QgsFeature,
    QgsGeometry,
    QgsTransaction,
    QgsTransactionGroup,
    QgsProject,
    QgsSettings, Qgis,
    QgsEditFormConfig
)

from qgis.gui import *
import functools
import time
import os
#import cv2


from abc import ABCMeta
from TOMs.generateGeometryUtils import generateGeometryUtils
from TOMs.restrictionTypeUtilsClass import (TOMsParams, TOMsLayers)
from TOMs.ui.TOMsCamera import formCamera
from TOMs.core.TOMsMessageLog import TOMsMessageLog

try:
    import cv2
except ImportError:
    None

import uuid

class gpsLayers(TOMsLayers):
    def __init__(self, iface):
        TOMsLayers.__init__(self, iface)
        self.iface = iface
        QgsMessageLog.logMessage("In gpsLayers.init ...", tag="TOMs panel")
        # TODO: Load these from a local file - or database
        self.TOMsLayerList = [
            "Bays",
            "Lines",
            "Signs",
            "RestrictionPolygons",
            # "ConstructionLines",
            # "CPZs",
            # "ParkingTariffAreas",
            # "StreetGazetteerRecords",
            "RoadCentreLine",
            "RoadCasement",
            # "RestrictionTypes",
            "BayLineTypes",
            # "BayTypes",
            # "LineTypes",
            # "RestrictionPolygonTypes",
            "LengthOfTime",
            "PaymentTypes",
            "RestrictionShapeTypes",
            "SignTypes",
            "TimePeriods",
            "UnacceptabilityTypes"
                         ]
        self.TOMsLayerDict = {}

class gpsParams(TOMsParams):
    def __init__(self):
        TOMsParams.__init__(self)
        #self.iface = iface

        QgsMessageLog.logMessage("In gpsParams.init ...", tag="TOMs panel")

        self.TOMsParamsList.extend([
                          "gpsPort"
                               ])

class originalFeature(object):
    def __init__(self, feature=None):
        self.savedFeature = None

    def setFeature(self, feature):
        self.savedFeature = QgsFeature(feature)
        #self.printFeature()

    def getFeature(self):
        #self.printFeature()
        return self.savedFeature

    def getGeometryID(self):
        return self.savedFeature.attribute("GeometryID")

    def printFeature(self):
        QgsMessageLog.logMessage("In TOMsNodeTool:originalFeature - attributes (fid:" + str(self.savedFeature.id()) + "): " + str(self.savedFeature.attributes()),
                                 tag="TOMs panel")
        QgsMessageLog.logMessage("In TOMsNodeTool:originalFeature - attributes: " + str(self.savedFeature.geometry().asWkt()),
                                 tag="TOMs panel")

class FieldRestrictionTypeUtilsMixin():
    def __init__(self, iface):

        self.iface = iface
        self.settings = QgsSettings()

    def setDefaultFieldRestrictionDetails(self, currRestriction, currRestrictionLayer, currDate):
        QgsMessageLog.logMessage("In setDefaultFieldRestrictionDetails: ", tag="TOMs panel")

        # TODO: Need to check whether or not these fields exist. Also need to retain the last values and reuse
        # gis.stackexchange.com/questions/138563/replacing-action-triggered-script-by-one-supplied-through-qgis-plugin

        try:
            currRestriction.setAttribute("CreateDateTime", currDate)
        except Exception:
            None

        # set up form details
        config = currRestrictionLayer.editFormConfig()
        #config.setInitCodeSource( QgsEditFormConfig.CodeSourceEnvironment )

        basePath = os.path.dirname(os.path.realpath(__file__))
        formPath = os.path.abspath(os.path.join(basePath, '.\\ui\\{}.ui'.format(currRestrictionLayer.name())))
        config.setUiForm(formPath)
        #config.setLayout(QgsEditFormConfig.EditorLayout.UiFileLayout)
        QgsMessageLog.logMessage("In setDefaultFieldRestrictionDetails: formName = {}".format(formPath), tag="TOMs panel")
        #config.setInitFilePath("py_file.py")
        #config.setInitFunction("method_name")
        currRestrictionLayer.setEditFormConfig(config)
        #self.dialog = self.iface.getFeatureForm(closestLayer, closestFeature)

        generateGeometryUtils.setRoadName(currRestriction)
        if currRestrictionLayer.geometryType() == 1:  # Line or Bay
            generateGeometryUtils.setAzimuthToRoadCentreLine(currRestriction)
            #currRestriction.setAttribute("Restriction_Length", currRestriction.geometry().length())

        #currentCPZ, cpzWaitingTimeID = generateGeometryUtils.getCurrentCPZDetails(currRestriction)
        #currRestriction.setAttribute("CPZ", currentCPZ)
        #currDate = self.proposalsManager.date()

        if currRestrictionLayer.name() == "Lines":
            currRestriction.setAttribute("RestrictionTypeID", self.readLastUsedDetails("Lines", "RestrictionTypeID", 201))  # 10 = SYL (Lines)
            currRestriction.setAttribute("GeomShapeID", self.readLastUsedDetails("Lines", "GeomShapeID", 10))   # 10 = Parallel Line
            currRestriction.setAttribute("NoWaitingTimeID", self.readLastUsedDetails("Lines", "NoWaitingTimeID", None))
            currRestriction.setAttribute("NoLoadingTimeID", self.readLastUsedDetails("Lines", "NoLoadingTimeID", None))
            #currRestriction.setAttribute("NoWTimeID", cpzWaitingTimeID)
            #currRestriction.setAttribute("CreateDateTime", currDate)
            currRestriction.setAttribute("Unacceptability", self.readLastUsedDetails("Lines", "Unacceptability", None))

        elif currRestrictionLayer.name() == "Bays":
            currRestriction.setAttribute("RestrictionTypeID", self.readLastUsedDetails("Bays", "RestrictionTypeID", 101))  # 28 = Permit Holders Bays (Bays)
            currRestriction.setAttribute("GeomShapeID", self.readLastUsedDetails("Bays", "GeomShapeID", 1)) # 21 = Parallel Bay (Polygon)
            currRestriction.setAttribute("NrBays", -1)
            currRestriction.setAttribute("TimePeriodID", self.readLastUsedDetails("Bays", "TimePeriodID", None))

            #currRestriction.setAttribute("MaxStayID", ptaMaxStayID)
            #currRestriction.setAttribute("NoReturnID", ptaNoReturnTimeID)
            #currRestriction.setAttribute("ParkingTariffArea", currentPTA)
            #currRestriction.setAttribute("CreateDateTime", currDate)

        elif currRestrictionLayer.name() == "Signs":
            currRestriction.setAttribute("SignType_1", self.readLastUsedDetails("Signs", "SignType_1", 28))  # 28 = Permit Holders Only (Signs)

        elif currRestrictionLayer.name() == "RestrictionPolygons":
            currRestriction.setAttribute("RestrictionTypeID", self.readLastUsedDetails("RestrictionPolygons", "RestrictionTypeID", 4))  # 28 = Residential mews area (RestrictionPolygons)

    def storeLastUsedDetails(self, layer, field, value):
        entry = '{layer}/{field}'.format(layer=layer, field=field)
        QgsMessageLog.logMessage("In storeLastUsedDetails: " + str(entry) + " (" + str(value) + ")", tag="TOMs panel")
        self.settings.setValue(entry, value)

    def readLastUsedDetails(self, layer, field, default):
        entry = '{layer}/{field}'.format(layer=layer, field=field)
        QgsMessageLog.logMessage("In readLastUsedDetails: " + str(entry) + " (" + str(default) + ")", tag="TOMs panel")
        return self.settings.value(entry, default)

    def setupFieldRestrictionDialog(self, currRestrictionLayer, currRestriction):

        #self.restrictionDialog = restrictionDialog
        #self.currRestrictionLayer = currRestrictionLayer
        #self.currRestriction = currRestriction
        #self.restrictionTransaction = restrictionTransaction
        self.dialog = self.iface.getFeatureForm(currRestrictionLayer, currRestriction)

        # Create a copy of the feature
        self.origFeature = originalFeature()
        self.origFeature.setFeature(currRestriction)

        if self.dialog is None:
            QgsMessageLog.logMessage(
                "In setupRestrictionDialog. dialog not found",
                tag="TOMs panel")

        self.dialog.attributeForm().disconnectButtonBox()
        button_box = self.dialog.findChild(QDialogButtonBox, "button_box")

        if button_box is None:
            QgsMessageLog.logMessage(
                "In setupRestrictionDialog. button box not found",
                tag="TOMs panel")

        button_box.accepted.connect(functools.partial(self.onSaveFieldRestrictionDetails, currRestriction,
                                      currRestrictionLayer, self.dialog))

        button_box.rejected.connect(functools.partial(self.onRejectFieldRestrictionDetailsFromForm, self.dialog, currRestrictionLayer))

        #button_box.accepted.connect(self.deactivate)
        #button_box.rejected.connect(self.deactivate)
        
        self.dialog.attributeForm().attributeChanged.connect(functools.partial(self.onAttributeChangedClass2, currRestriction, currRestrictionLayer))

        self.photoDetails(self.dialog, currRestrictionLayer, currRestriction)

        """def onSaveRestrictionDetailsFromForm(self):
        QgsMessageLog.logMessage("In onSaveRestrictionDetailsFromForm", tag="TOMs panel")
        self.onSaveRestrictionDetails(self.currRestriction,
                                      self.currRestrictionLayer, self.restrictionDialog, self.restrictionTransaction)"""

    def onAttributeChangedClass2(self, currFeature, layer, fieldName, value):
        QgsMessageLog.logMessage(
            "In FormOpen:onAttributeChangedClass 2 - layer: " + str(layer.name()) + " (" + fieldName + "): " + str(value), tag="TOMs panel")

        # self.currRestriction.setAttribute(fieldName, value)
        try:

            currFeature[layer.fields().indexFromName(fieldName)] = value
            #currFeature.setAttribute(layer.fields().indexFromName(fieldName), value)

        except:

            reply = QMessageBox.information(None, "Error",
                                                "onAttributeChangedClass2. Update failed for: " + str(layer.name()) + " (" + fieldName + "): " + str(value),
                                                QMessageBox.Ok)  # rollback all changes

        self.storeLastUsedDetails(layer.name(), fieldName, value)

        return

        """def onSaveFieldRestrictionDetails(self, currRestriction, currRestrictionLayer, dialog):
        QgsMessageLog.logMessage("In onSaveFieldRestrictionDetails: " + str(currRestriction.attribute("GeometryID")), tag="TOMs panel")

        status = dialog.attributeForm().save()
        currRestrictionLayer.addFeature(currRestriction)  # TH (added for v3)
        #currRestrictionLayer.updateFeature(currRestriction)  # TH (added for v3)"""

    def onSaveFieldRestrictionDetails(self, currFeature, currFeatureLayer, dialog):
        QgsMessageLog.logMessage("In onSaveFieldRestrictionDetails: ", tag="TOMs panel")

        try:
            self.camera1.closeCameraForm()
            self.camera2.closeCameraForm()
            self.camera3.closeCameraForm()
        except:
            None

        attrs1 = currFeature.attributes()
        QgsMessageLog.logMessage("In onSaveDemandDetails: currRestriction: " + str(attrs1),
                                 tag="TOMs panel")

        QgsMessageLog.logMessage(
            ("In onSaveDemandDetails. geometry: " + str(currFeature.geometry().asWkt())),
            tag="TOMs panel")

        currFeatureID = currFeature.id()
        QgsMessageLog.logMessage("In onSaveDemandDetails: currFeatureID: " + str(currFeatureID),
                                 tag="TOMs panel")

        status = currFeatureLayer.updateFeature(currFeature)
        """if currFeatureID > 0:   # Not sure what this value should if the feature has not been created ...

            # TODO: Sort out this for UPDATE
            self.setDefaultRestrictionDetails(currFeature, currFeatureLayer)

            status = currFeatureLayer.updateFeature(currFeature)
            QgsMessageLog.logMessage("In onSaveDemandDetails: updated Feature: ", tag="TOMs panel")
        else:
            status = currFeatureLayer.addFeature(currFeature)
            QgsMessageLog.logMessage("In onSaveDemandDetails: added Feature: " + str(status), tag="TOMs panel")"""

        QgsMessageLog.logMessage("In onSaveDemandDetails: Before commit", tag="TOMs panel")

        """reply = QMessageBox.information(None, "Information",
                                        "Wait a moment ...",
                                        QMessageBox.Ok)"""
        attrs1 = currFeature.attributes()
        QgsMessageLog.logMessage("In onSaveDemandDetails: currRestriction: " + str(attrs1),
                                 tag="TOMs panel")

        QgsMessageLog.logMessage(
            ("In onSaveDemandDetails. geometry: " + str(currFeature.geometry().asWkt())),
            tag="TOMs panel")

        """QgsMessageLog.logMessage("In onSaveDemandDetails: currActiveLayer: " + str(self.iface.activeLayer().name()),
                                 tag="TOMs panel")"""
        QgsMessageLog.logMessage("In onSaveDemandDetails: currActiveLayer: " + str(currFeatureLayer.name()),
                                 tag="TOMs panel")
        currFeatureLayer
        #Test
        #status = dialog.attributeForm().save()
        #status = dialog.accept()
        #status = dialog.accept()

        """reply = QMessageBox.information(None, "Information",
                                        "And another ... iseditable: " + str(currFeatureLayer.isEditable()),
                                        QMessageBox.Ok)"""

        #currFeatureLayer.blockSignals(True)

        """if currFeatureID == 0:
            self.iface.mapCanvas().unsetMapTool(self.iface.mapCanvas().mapTool())
            QgsMessageLog.logMessage("In onSaveDemandDetails: mapTool unset",
                                     tag="TOMs panel")"""

        """try:
            currFeatureLayer.commitChanges()
        except:
            reply = QMessageBox.information(None, "Information", "Problem committing changes" + str(currFeatureLayer.commitErrors()), QMessageBox.Ok)

        #currFeatureLayer.blockSignals(False)

        QgsMessageLog.logMessage("In onSaveDemandDetails: changes committed", tag="TOMs panel")

        status = dialog.close()"""

        status = dialog.attributeForm().save()
        #currRestrictionLayer.addFeature(currRestriction)  # TH (added for v3)
        currFeatureLayer.updateFeature(currFeature)  # TH (added for v3)

        try:
            currFeatureLayer.commitChanges()
        except:
            reply = QMessageBox.information(None, "Information", "Problem committing changes" + str(currFeatureLayer.commitErrors()), QMessageBox.Ok)

        QgsMessageLog.logMessage("In onSaveDemandDetails: changes committed", tag="TOMs panel")

        status = dialog.close()
        self.iface.mapCanvas().unsetMapTool(self.iface.mapCanvas().mapTool())

    def onRejectFieldRestrictionDetailsFromForm(self, restrictionDialog, currFeatureLayer):
        QgsMessageLog.logMessage("In onRejectFieldRestrictionDetailsFromForm", tag="TOMs panel")

        try:
            self.camera1.closeCameraForm()
            self.camera2.closeCameraForm()
            self.camera3.closeCameraForm()
        except:
            None

        currFeatureLayer.rollBack()
        restrictionDialog.reject()
        self.demandDialog.close()

    def photoDetails(self, restrictionDialog, currRestrictionLayer, currRestriction):

        # Function to deal with photo fields

        self.demandDialog = restrictionDialog
        self.currDemandLayer = currRestrictionLayer
        self.currFeature = currRestriction

        QgsMessageLog.logMessage("In photoDetails", tag="TOMs panel")

        FIELD1 = self.demandDialog.findChild(QLabel, "Photo_Widget_01")
        FIELD2 = self.demandDialog.findChild(QLabel, "Photo_Widget_02")
        FIELD3 = self.demandDialog.findChild(QLabel, "Photo_Widget_03")

        # sort out path for Photos
        photoPath = QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable('PhotoPath')
        TOMsMessageLog.logMessage("In photoDetails. '{}'".format(photoPath),
                                 level=Qgis.Info)
        if len(str(photoPath)) <= 0:
            reply = QMessageBox.information(None, "Information", "Please set value for PhotoPath.", QMessageBox.Ok)
            return

        if os.path.isabs(photoPath):
            path_absolute = photoPath
        else:
            projectPath = QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable('project_home')
            path_absolute = os.path.abspath(os.path.join(projectPath, photoPath))
        TOMsMessageLog.logMessage("In photoDetails. '{}' {}".format(projectPath, path_absolute),
                                 level=Qgis.Info)
        # check that the path exists
        if not os.path.isdir(path_absolute):
            reply = QMessageBox.information(None, "Information", "Did not find value for project path.", QMessageBox.Ok)
            return

        layerName = self.currDemandLayer.name()

        # Generate the full path to the file

        # fileName1 = "Photos"
        fileName1 = "Photos_01"
        fileName2 = "Photos_02"
        fileName3 = "Photos_03"

        idx1 = self.currDemandLayer.fields().indexFromName(fileName1)
        idx2 = self.currDemandLayer.fields().indexFromName(fileName2)
        idx3 = self.currDemandLayer.fields().indexFromName(fileName3)

        """  v2.18
        idx1 = self.currDemandLayer.fieldNameIndex(fileName1)
        idx2 = self.currDemandLayer.fieldNameIndex(fileName2)
        idx3 = self.currDemandLayer.fieldNameIndex(fileName3)
        """

        QgsMessageLog.logMessage("In photoDetails. idx1: " + str(idx1) + "; " + str(idx2) + "; " + str(idx3),
                                 tag="TOMs panel")
        # if currFeatureFeature[idx1]:
        # QgsMessageLog.logMessage("In photoDetails. photo1: " + str(currFeatureFeature[idx1]), tag="TOMs panel")
        # QgsMessageLog.logMessage("In photoDetails. photo2: " + str(currFeatureFeature.attribute(idx2)), tag="TOMs panel")
        # QgsMessageLog.logMessage("In photoDetails. photo3: " + str(currFeatureFeature.attribute(idx3)), tag="TOMs panel")

        if FIELD1:
            QgsMessageLog.logMessage("In photoDetails. FIELD 1 exisits",
                                     tag="TOMs panel")
            if self.currFeature[idx1]:
                newPhotoFileName1 = os.path.join(path_absolute, self.currFeature[idx1])
            else:
                newPhotoFileName1 = None

            # QgsMessageLog.logMessage("In photoDetails. Photo1: " + str(newPhotoFileName1), tag="TOMs panel")
            pixmap1 = QPixmap(newPhotoFileName1)
            if pixmap1.isNull():
                pass
                # FIELD1.setText('Picture could not be opened ({path})'.format(path=newPhotoFileName1))
            else:
                FIELD1.setPixmap(pixmap1)
                FIELD1.setScaledContents(True)
                QgsMessageLog.logMessage("In photoDetails. Photo1: " + str(newPhotoFileName1), tag="TOMs panel")

            START_CAMERA_1 = self.demandDialog.findChild(QPushButton, "startCamera1")
            TAKE_PHOTO_1 = self.demandDialog.findChild(QPushButton, "getPhoto1")
            TAKE_PHOTO_1.setEnabled(False)

            self.camera1 = formCamera(path_absolute, newPhotoFileName1)
            START_CAMERA_1.clicked.connect(
                functools.partial(self.camera1.useCamera, START_CAMERA_1, TAKE_PHOTO_1, FIELD1))
            self.camera1.notifyPhotoTaken.connect(functools.partial(self.savePhotoTaken, idx1))

        if FIELD2:
            QgsMessageLog.logMessage("In photoDetails. FIELD 2 exisits",
                                     tag="TOMs panel")
            if self.currFeature[idx2]:
                newPhotoFileName2 = os.path.join(path_absolute, self.currFeature[idx2])
            else:
                newPhotoFileName2 = None

            # newPhotoFileName2 = os.path.join(path_absolute, str(self.currFeature[idx2]))
            # newPhotoFileName2 = os.path.join(path_absolute, str(self.currFeature.attribute(fileName2)))
            # QgsMessageLog.logMessage("In photoDetails. Photo2: " + str(newPhotoFileName2), tag="TOMs panel")
            pixmap2 = QPixmap(newPhotoFileName2)
            if pixmap2.isNull():
                pass
                # FIELD1.setText('Picture could not be opened ({path})'.format(path=newPhotoFileName1))
            else:
                FIELD2.setPixmap(pixmap2)
                FIELD2.setScaledContents(True)
                QgsMessageLog.logMessage("In photoDetails. Photo2: " + str(newPhotoFileName2), tag="TOMs panel")

            START_CAMERA_2 = self.demandDialog.findChild(QPushButton, "startCamera2")
            TAKE_PHOTO_2 = self.demandDialog.findChild(QPushButton, "getPhoto2")
            TAKE_PHOTO_2.setEnabled(False)

            self.camera2 = formCamera(path_absolute, newPhotoFileName2)
            START_CAMERA_2.clicked.connect(
                functools.partial(self.camera2.useCamera, START_CAMERA_2, TAKE_PHOTO_2, FIELD2))
            self.camera2.notifyPhotoTaken.connect(functools.partial(self.savePhotoTaken, idx2))

        if FIELD3:
            QgsMessageLog.logMessage("In photoDetails. FIELD 3 exisits",
                                     tag="TOMs panel")

            if self.currFeature[idx3]:
                newPhotoFileName3 = os.path.join(path_absolute, self.currFeature[idx3])
            else:
                newPhotoFileName3 = None

            # newPhotoFileName3 = os.path.join(path_absolute, str(self.currFeature[idx3]))
            # newPhotoFileName3 = os.path.join(path_absolute,
            #                                 str(self.currFeature.attribute(fileName3)))
            # newPhotoFileName3 = os.path.join(path_absolute, str(layerName + "_Photos_03"))

            # QgsMessageLog.logMessage("In photoDetails. Photo3: " + str(newPhotoFileName3), tag="TOMs panel")
            pixmap3 = QPixmap(newPhotoFileName3)
            if pixmap3.isNull():
                pass
                # FIELD1.setText('Picture could not be opened ({path})'.format(path=newPhotoFileName1))
            else:
                FIELD3.setPixmap(pixmap3)
                FIELD3.setScaledContents(True)
                QgsMessageLog.logMessage("In photoDetails. Photo3: " + str(newPhotoFileName3), tag="TOMs panel")

            START_CAMERA_3 = self.demandDialog.findChild(QPushButton, "startCamera3")
            TAKE_PHOTO_3 = self.demandDialog.findChild(QPushButton, "getPhoto3")
            TAKE_PHOTO_3.setEnabled(False)

            self.camera3 = formCamera(path_absolute, newPhotoFileName3)
            START_CAMERA_3.clicked.connect(
                functools.partial(self.camera3.useCamera, START_CAMERA_3, TAKE_PHOTO_3, FIELD3))
            self.camera3.notifyPhotoTaken.connect(functools.partial(self.savePhotoTaken, idx3))

        pass

    def getLookupDescription(self, lookupLayer, code):

        #QgsMessageLog.logMessage("In getLookupDescription", tag="TOMs panel")

        query = "\"Code\" = " + str(code)
        request = QgsFeatureRequest().setFilterExpression(query)

        #QgsMessageLog.logMessage("In getLookupDescription. queryStatus: " + str(query), tag="TOMs panel")

        for row in lookupLayer.getFeatures(request):
            #QgsMessageLog.logMessage("In getLookupDescription: found row " + str(row.attribute("Description")), tag="TOMs panel")
            return row.attribute("Description") # make assumption that only one row

        return None

    @pyqtSlot(str)
    def savePhotoTaken(self, idx, fileName):
        QgsMessageLog.logMessage("In demandFormUtils::savePhotoTaken ... " + fileName + " idx: " + str(idx),
                                 tag="TOMs panel")
        if len(fileName) > 0:
            simpleFile = ntpath.basename(fileName)
            QgsMessageLog.logMessage("In demandFormUtils::savePhotoTaken. Simple file: " + simpleFile, tag="TOMs panel")

            try:
                self.currFeature[idx] = simpleFile
                QgsMessageLog.logMessage("In demandFormUtils::savePhotoTaken. attrib value changed", tag="TOMs panel")
            except:
                QgsMessageLog.logMessage("In demandFormUtils::savePhotoTaken. problem changing attrib value",
                                         tag="TOMs panel")
                reply = QMessageBox.information(None, "Error",
                                                "savePhotoTaken. problem changing attrib value",
                                                QMessageBox.Ok)
