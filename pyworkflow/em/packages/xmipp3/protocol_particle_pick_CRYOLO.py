# **************************************************************************
# *
# * Authors:     Jose Gutierrez Tabuenca (jose.gutierrez@cnb.csic.es)
# *              J.M. De la Rosa Trevin (jmdelarosa@cnb.csic.es)
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

import json
import os

from pyworkflow.em import *
from pyworkflow.utils import Environ
from pyworkflow.protocol.launch import launch
from pyworkflow.utils.path import *
from pyworkflow.em.showj import launchSupervisedPickerGUI
from convert import writeSetOfMicrographs, readSetOfCoordinates

import xmipp
from xmipp3 import XmippProtocol


class XmippProtParticlePickingCRYOLO(ProtParticlePicking, XmippProtocol):
    """ Picks particles in a set of micrographs
    either manually or in a supervised mode.
    """
    _label = 'manual-picking CRYOLO'

    def __init__(self, **args):
        ProtParticlePicking.__init__(self, **args)

    #--------------------------- DEFINE param functions ------------------------   
    def _defineParams(self, form):
        ProtParticlePicking._defineParams(self, form)
        form.addParam('memory', FloatParam, default=2,
                      label='Memory to use (In Gb)', expertLevel=2)
        # form.addParam('saveDiscarded', BooleanParam, default=False,
        #               label='Save discarded particles',
        #               help='Generates an output with '
        #                    'the manually discarded particles.')
        form.addParam('input_size', params.IntParam, default= 1024,
                      label="Input size",
                      help="Input size of the micrographs")
        form.addParam('anchors', params.IntParam, default= 160,
                      label="Anchors",
                      help="Box dimension")
        form.addParam('batch_size', params.IntParam, default= 3,
                      label="Batch size",
                      help="Box dimension")
        form.addParam('learning_rates', params.FloatParam, default= 1e-4,
                      label="Learning rates",
                      help="?")
        form.addParam('max_box_per_image', params.IntParam, default=600,
                      label="Maximum box per image",
                      help="?")



    #--------------------------- INSERT steps functions ------------------------
    def _insertAllSteps(self):
        """The Particle Picking process is realized for a set of micrographs"""
        # Get pointer to input micrographs
        self.inputMics = self.inputMicrographs.get()
        micFn = self.inputMics.getFileName()

        # Launch Particle Picking GUI
        self._insertFunctionStep('launchParticlePickGUIStep', micFn)
        self._insertFunctionStep('convertTrainCoordsStep')
        self._insertFunctionStep('cryoloModelingStep')
        self._insertFunctionStep('cryoloDeepPickingStep')
        self._insertFunctionStep('createOutputStep')

    def launchParticlePickGUIStep(self, micFn):
        # Launch the particle picking GUI
        extraDir = self._getExtraPath()
        memory = int(self.memory.get())
        process = launchSupervisedPickerGUI(micFn, extraDir, self, memory=memory)
        process.wait()

    def convertTrainCoordsStep(self):

        def convertMic(mic):
            fileName = mic.getFileName()
            extensionFn =getExt(fileName)
            if extensionFn != ".mrc":
                fileName1 = replaceExt(fileName, "mrc")
                ih = ImageHandler()   #initalize as an object
                ih.convert(extensionFn, fileName1)

            #fileNameOut = self._getExtraPath(basename(fileName))
            #print fileNameOut


        coordFn = self._getPath('coordinates.sqlite')
        coordSet = SetOfCoordinates(filename=coordFn)
        coordSet._xmippMd = String()
        coordSet.loadAllProperties()
        self.boxSize = coordSet.getBoxSize()

        trainMicDir = self._getExtraPath('train_image')
        pwutils.path.makePath(trainMicDir)

        trainCoordDir = self._getExtraPath('train_annotation')
        pwutils.path.makePath(trainCoordDir)
        oldMicName = None
        for item in coordSet:
            xCoord = item.getX()
            yCoord = item.getY()
            micName = item.getMicName()
            boxName = join(trainCoordDir, replaceExt(micName, "box"))
            boxFile = open(boxName, 'a+')
            boxFile.write("%s\t%s\t%s\t%s\n" % (xCoord, yCoord,
                                                self.boxSize, self.boxSize))
            boxFile.close()
            # we only copy the micrographs once
            if micName != oldMicName:
                mic = self.inputMics[item.getMicId()]
                newMicFn = convertMic(mic)
                copyFile(mic.getFileName(), trainMicDir)
            oldMicName = micName



    # def cretingTrainingDataset(self, micFileName):
    #     pwutils.path.makePath(train_image)
    #     if not exists(train_image):
    #         raise Exception("No created dir: %s " % train_image)
    #     copyFile(micFileName, train_image)
    #     #print (os.path.exists(params.IntParam)
    #     #print (self.input_size.get())


    def createConfigurationFile(self):

        inputSize = self.input_size.get()
        anchors = self.boxSize.get()
        maxBoxPerImage = self.max_box_per_image.get()

        model = {"architecture": "crYOLO",
                 "input_size": inputSize,
                 "anchors": [anchors, anchors],
                 "max_box_per_image": maxBoxPerImage,
                  }

        train = { "train_image_folder": "train_image/",
                  "train_annot_folder": "train_annotation/",
                  "train_times": 10,
                  "pretrained_weights": "model.h5",
                  "batch_size": 3,
                  "learning_rate": 1e-4,
                  "nb_epoch": 50,
                  "warmup_epochs": 0,
                  "object_scale": 5.0,
                  "no_object_scale": 1.0,
                  "coord_scale": 1.0,
                  "class_scale": 1.0,
                  "log_path": "logs/",
                  "saved_weights_name": "model.h5",
                  "debug": 'true'
                           }

        valid = {"valid_image_folder": "",
                 "valid_annot_folder": "",
                 "valid_times": 1
                 }

        jsonDict = {"model" : model,
                    "train" : train,
                    "valid" : valid}



        with open(self._getExtraPath('config_generalized_model.json'), 'w') as fp:
            json.dump(jsonDict, fp, indent=4)


    def cryoloModelingStep(self):
        # TEMPLATE: -c config.json -w 0 -g 0 -e 10
        wParam = 0  # define this in the form ???
        gParam = 0  # define this in the form ???
        eParam = 0  # define this in the form ???
        params = "-c config.json"
        params += " -w %s -g %s" % (wParam, gParam)
        if eParam != 0:
            params += " -e %s" % eParam

        program = getProgram('cryolo_train.py')

        self.preparingCondaProgram(program, params):
        shellName = os.environ.get('SHELL')

        self.info("**Running:** %s %s" % (program, param))
        self.runJob('%s ./script.sh' % shellName, '', cwd=self._getExtraPath(),
                    env=getEnviron())
        # if not exists(self._getFileName('out_vol3DFSC')):
        #     raise Exception('3D FSC run failed!')


    def cryoloDeepPickingStep(self):
        wParam = model.h5  # define this in the form ???
        gParam = 0  # define this in the form ???
        eParam = 0  # define this in the form ???
        tParam = 0.2 # define this in the form ???
        params = "-c config.json"
        params += " -w %s -g %s" % (wParam, gParam)
        params += "-i full_data/"
        params += "-o boxfiles/"
        params += "-t %s" % tParam

        program2 = getProgram('cryolo_predict.py')
        shellName = os.environ.get('SHELL')
        self.info("**Running:** %s %s" % (program2, params))
        self.runJob('%s ./script.sh' % shellName, '',
                    cwd=self._getExtraPath(),
                    env=getEnviron())


    def preparingCondaProgram(self, program, params):
        f = open(self._getExtraPath('script.sh'), "w")
        # print f
        # print ShellName
        # line0 = 'conda create -n cryolo -c anaconda python=2 pyqt=5 cudnn=7.1.2'
        lines = 'source activate %s\n' % CRYOLO_ENV_NAME
        lines += '%s %s\n' % (program, params)
        lines += 'source deactivate\n'
        f.write(lines)
        f.close()


    # def _getArgs(self):
    #     """ Prepare the args dictionary."""
    #
    #     args = {'--halfmap1': basename(self._getFileName('input_half1Fn')),
    #             '--halfmap2': basename(self._getFileName('input_half2Fn')),
    #             '--fullmap': basename(self._getFileName('input_volFn')),
    #             '--apix': self.inputVolume.get().getSamplingRate(),
    #             '--ThreeDFSC': '3D-FSC',
    #             '--dthetaInDegrees': self.dTheta.get(),
    #             '--FSCCutoff': self.fscCutoff.get(),
    #             '--ThresholdForSphericity': self.thrSph.get(),
    #             '--HighPassFilter': self.hpFilter.get(),
    #             '--numThresholdsForSphericityCalcs': self.numThr.get()



    #     first version
    #     """ Setup the environment variables needed to launch crYOLO. """
    #     environ = Environ(os.environ)
    #     pos = pwutils.Environ.BEGIN if first else pwutils.Environ.END
    #     crYOLO_HOME = os.environ[('CRYOLO_HOME')] #?
    #     LD_LIBRARY_PATH = os.environ[]
    #     print crYOLO_HOME
    #     print ('bekafos')
    #     environ.update({'PATH': os.path.join(crYOLO_HOME, 'build','bin'),
    # }, position=pos)
    #
    #     # replace variable value
    #     environ.update({
    #         ''
    #         'PWD=/home/phorvath/crYOLO'
    #         'LIBTBX_BUILD': os.path.join(crYOLO_home, 'build'),
    #         'LIBTBX_OPATH': os.environ['PATH'],
    #     }, position=pwutils.Environ.REPLACE)  # replace
    #
    #     cudaLib = getCudaLib(environ, useMC2)
    #     environ.addLibrary(cudaLib)
    #
    #     return environ



    # def runCrYOLOProgram(program, args=None, extraEnvDict=None, cwd=None):
    #     """ Internal shortcut function to launch a Phenix program. """
    #     env = getEnviron()
    #     if extraEnvDict is not None:
    #         env.update(extraEnvDict)
    #     program = PHENIX_PYTHON + program
    #     pwutils.runJob(None, program, args, env=env, cwd=cwd)




    #
    # def
    # getEnviron(cls):
    # """ Setup the environment variables needed to launch sachselab. """
    # environ = Environ(os.environ)
    # print("getEnvirion(): %s" % os.environ.get(LOCSCALE_HOME_VAR))
    # if ('%s' % Plugin._homeVar) in environ:
    #     environ.update({
    #         'PATH': os.environ[Plugin._homeVar],
    #         'LD_LIBRARY_PATH': str.join(os.environ[Plugin._homeVar],
    #                                     'sachselablib')
    #                            + ":" + os.environ[Plugin._homeVar],
    #     }, position=Environ.BEGIN)
    # else:
    #     # TODO: Find a generic way to warn of this situation
    #     print "%s variable not set on environment." % Plugin._homeVar
    # return environ


    def createOutputStep(self):
        posDir = self._getExtraPath()
        coordSet = self._createSetOfCoordinates(self.inputMics)
        readSetOfCoordinates(posDir, self.inputMics, coordSet)
        self._defineOutputs(outputCoordinates=coordSet)
        self._defineSourceRelation(self.inputMicrographs, coordSet)



    # def createDiscardedStep(self):
    #     posDir = self._getExtraPath()
    #     suffixRoot = self._ProtParticlePicking__getOutputSuffix()
    #     suffix = '' if suffixRoot=='2' or suffixRoot=='' \
    #              else str(int(suffixRoot)-1)
    #     coordSetDisc = self._createSetOfCoordinates(self.inputMics,
    #                                                 suffix='Discarded'+suffix)
    #     readSetOfCoordinates(posDir, self.inputMics, coordSetDisc,
    #                          readDiscarded=True)
    #     if coordSetDisc.getSize()>0:
    #         outputName = 'outputDiscardedCoordinates' + suffix
    #         outputs = {outputName: coordSetDisc}
    #         self._defineOutputs(**outputs)
    #         self._defineSourceRelation(self.inputMicrographs, coordSetDisc)

    #--------------------------- INFO functions --------------------------------
    def _citations(self):
        return ['Wagner2018']

    #--------------------------- UTILS functions -------------------------------
    def __str__(self):
        """ String representation of a Supervised Picking run """
        if not hasattr(self, 'outputCoordinates'):
            msg = "No particles picked yet."
        else:

            picked = 0
            # Get the number of picked particles of the last coordinates set
            for key, output in self.iterOutputAttributes(EMObject):
                picked = output.getSize()

            msg = "%d particles picked (from %d micrographs)" % \
                  (picked, self.inputMicrographs.get().getSize())

        return msg

    def _methods(self):
        if self.getOutputsSize() > 0:
            return ProtParticlePicking._methods(self)
        else:
            return [self._getTmpMethods()]

    def _getTmpMethods(self):
        """ Return the message when there is not output generated yet.
         We will read the Xmipp .pos files and other configuration files.
        """
        configfile = join(self._getExtraPath(), 'config.xmd')
        existsConfig = exists(configfile)
        msg = ''

        if existsConfig:
            md = xmipp.MetaData('properties@' + configfile)
            configobj = md.firstObject()
            pickingState = md.getValue(xmipp.MDL_PICKING_STATE, configobj)
            particleSize = md.getValue(xmipp.MDL_PICKING_PARTICLE_SIZE, configobj)
            isAutopick = pickingState != "Manual"
            manualParts = md.getValue(xmipp.MDL_PICKING_MANUALPARTICLES_SIZE, configobj)
            autoParts = md.getValue(xmipp.MDL_PICKING_AUTOPARTICLES_SIZE, configobj)

            if manualParts is None:
                manualParts = 0

            if autoParts is None:
                autoParts = 0

            msg = 'User picked %d particles ' % (autoParts + manualParts)
            msg += 'with a particle size of %d.' % particleSize

            if isAutopick:
                msg += "Automatic picking was used ([Abrishami2013]). "
                msg += "%d particles were picked automatically " %  autoParts
                msg += "and %d  manually." % manualParts

        return msg

    def _summary(self):
        if self.getOutputsSize() > 0:
            return ProtParticlePicking._summary(self)
        else:
            return [self._getTmpSummary()]

    def _getTmpSummary(self):
        summary = []
        configfile = join(self._getExtraPath(), 'config.xmd')
        existsConfig = exists(configfile)
        if existsConfig:
            md = xmipp.MetaData('properties@' + configfile)
            configobj = md.firstObject()
            pickingState = md.getValue(xmipp.MDL_PICKING_STATE, configobj)
            particleSize = md.getValue(xmipp.MDL_PICKING_PARTICLE_SIZE, configobj)
            activeMic = md.getValue(xmipp.MDL_MICROGRAPH, configobj)
            isAutopick = pickingState != "Manual"
            manualParticlesSize = md.getValue(xmipp.MDL_PICKING_MANUALPARTICLES_SIZE, configobj)
            autoParticlesSize = md.getValue(xmipp.MDL_PICKING_AUTOPARTICLES_SIZE, configobj)

            summary.append("Manual particles picked: %d"%manualParticlesSize)
            summary.append("Particle size:%d" %(particleSize))
            autopick = "Yes" if isAutopick else "No"
            summary.append("Autopick: " + autopick)
            if isAutopick:
                summary.append("Automatic particles picked: %d"%autoParticlesSize)
            summary.append("Last micrograph: " + activeMic)
        return "\n".join(summary)

    def getCoordsDir(self):
        return self._getExtraPath()


def getEnviron():
    """ Setup the environment variables needed to launch 3DFSC. """
    environ = Environ(os.environ)
    CRYOLO_HOME = os.environ.get('CRYOLO_HOME')

    environ.update({
        'PATH': join(CRYOLO_HOME, 'bin'),
    }, position=Environ.BEGIN)

    if 'PYTHONPATH' in environ:
        # this is required for python virtual env to work
        environ.set('PYTHONPATH', '', position=Environ.BEGIN)
    return environ

def getProgram(self, program):
    """ Return the program binary that will be used. """
    if 'CRYOLO_HOME' not in os.environ:
        print("CRYOLO_HOME is not in the environ")
        return None
    cmd = join(os.environ['CRYOLO_HOME'], 'bin', program)
    return cmd