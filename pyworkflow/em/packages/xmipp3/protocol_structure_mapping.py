# **************************************************************************
# *
# * Authors:     Mohsen Kazemi  (mkazemi@cnb.csic.es)
# *              C.O.S. Sorzano (coss@cnb.csic.es)
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
# *  e-mail address 'jmdelarosa@cnb.csic.es'
# *
# **************************************************************************

import pyworkflow.em as em
import pyworkflow.protocol.params as params
from pyworkflow.em.packages.xmipp3.convert import getImageLocation
from pyworkflow.protocol.constants import LEVEL_ADVANCED
from pyworkflow.utils.path import cleanPattern, createLink, moveFile, copyFile, makePath, cleanPath
from os.path import basename, exists
from pyworkflow.object import String
import os
from pyworkflow.em.data import SetOfNormalModes
from pyworkflow.em.packages.xmipp3 import XmippMdRow
from pyworkflow.em.packages.xmipp3.pdb.protocol_pseudoatoms_base import XmippProtConvertToPseudoAtomsBase
import xmipp
from pyworkflow.em.packages.xmipp3.nma.protocol_nma_base import XmippProtNMABase, NMA_CUTOFF_REL
from pyworkflow.em.packages.xmipp3.protocol_align_volume import XmippProtAlignVolume, ALIGN_MASK_CIRCULAR, ALIGN_ALGORITHM_LOCAL, ALIGN_ALGORITHM_FAST_FOURIER




class XmippProtStructureMapping(XmippProtConvertToPseudoAtomsBase,XmippProtNMABase, XmippProtAlignVolume):
    """ 
    Multivariate distance analysis of elastically aligned electron microscopy density maps
    for exploring pathways of conformational changes    
     """
    _label = 'structure mapping'
    
    #def __init__(self, **args):
    #    em.ProtAlignVolume.__init__(self, **args)
    #    self.stepsExecutionMode = em.STEPS_PARALLEL
    
    #--------------------------- DEFINE param functions --------------------------------------------
    def _defineParams(self, form):
        form.addSection(label='Input')
        form.addParam('inputVolumes', params.MultiPointerParam, pointerClass='SetOfVolumes,Volume',  
                      label="Input volume(s)", important=True, 
                      help='Select one or more volumes (Volume or SetOfVolumes)\n'
                           'to be aligned againt the reference volume.')
        #XmippProtAlignVolume._defineParams(self, form.addParam.applyMask)
        
        form.addSection(label='Pseudoatom')
        XmippProtConvertToPseudoAtomsBase._defineParams(self,form)
        self.getParam("pseudoAtomRadius").setDefault(2)
        self.getParam("pseudoAtomTarget").setDefault(2)
        
        form.addSection(label='Normal Mode Analysis')
        XmippProtNMABase._defineParamsCommon(self,form)
        form.addParallelSection(threads=8, mpi=1)
        
    #--------------------------- INSERT steps functions --------------------------------------------    
    def _insertAllSteps(self):
        cutoffStr=''
        if self.cutoffMode == NMA_CUTOFF_REL:
            cutoffStr = 'Relative %f'%self.rcPercentage.get()
        else:
            cutoffStr = 'Absolute %f'%self.rc.get()

        maskArgs = self._getMaskArgs()
        alignArgs = self._getAlignArgs()
        
        
        volList = [vol.clone() for vol in self._iterInputVolumes()]
                    
        for voli in volList:
            fnIn = getImageLocation(voli)
            fnMask = self._insertMaskStep(fnIn)
            prefix="_%d"%voli.getObjId()        
            self._insertFunctionStep('convertToPseudoAtomsStep', fnIn, fnMask, voli.getSamplingRate(), prefix)
            fnPseudoAtoms = self._getPath("pseudoatoms_%d.pdb"%voli.getObjId())
            self._insertFunctionStep('computeModesStep', fnPseudoAtoms, self.numberOfModes, cutoffStr)
            self._insertFunctionStep('reformatOutputStep', os.path.basename(fnPseudoAtoms), prefix)
            for volj in volList:
                if volj is not voli:
                    refFn = getImageLocation(voli)
                    inVolFn = getImageLocation(volj)
                    self._insertFunctionStep('alignVolumeStep', refFn, inVolFn, vol.outputName, 
                                                maskArgs, alignArgs)
                    
            
        
        
                
                   
    #    self._insertFunctionStep('createOutputStep')
        
    #--------------------------- STEPS functions --------------------------------------------
    
   
    
    
    
        #cleanPath("vec_ani.pkl")
    
          
            
         
            
      
    #def createOutputStep(self):
    
    """ for pseudoatom"""
    
    #inputVol = self.inputStructure.get()
    #pdb = PdbFile(self._getPath('pseudoatoms.pdb'), pseudoatoms=True)
    #self.createChimeraScript(inputVol, pdb)
    #self._defineOutputs(outputPdb=pdb)
    #self._defineSourceRelation(self.inputStructure, pdb)
    
    
    
    """ for mode analysis""" 
    
    #fnSqlite = self._getPath('modes.sqlite')
    #nmSet = SetOfNormalModes(filename=fnSqlite)

    #md = xmipp.MetaData(self._getPath('modes.xmd'))
    #row = XmippMdRow()
        
    #for objId in md:
    #    row.readFromMd(md, objId)
    #    nmSet.append(rowToMode(row))
    #inputPdb = self.inputStructure.get()
    #nmSet.setPdb(inputPdb)
    #self._defineOutputs(outputModes=nmSet)
    #self._defineSourceRelation(self.inputStructure, nmSet)
    
    
    
    
    
    
    """ for align volume"""
    
    #    vols = []
    #    for vol in self._iterInputVolumes():
    #        outVol = em.Volume()
    #        outVol.setLocation(vol.outputName)
    #        outVol.setObjLabel(vol.getObjLabel())
    #        outVol.setObjComment(vol.getObjComment())
    #        vols.append(outVol) 
    #        
    #    if len(vols) > 1:
    #        volSet = self._createSetOfVolumes()
    #        volSet.setSamplingRate(self.inputReference.get().getSamplingRate())
    #        for vol in vols:
    #            volSet.append(vol)
    #        outputArgs = {'outputVolumes': volSet}
    #    else:
    #        vols[0].setSamplingRate(self.inputReference.get().getSamplingRate())
    #        outputArgs = {'outputVolume': vols[0]}
    #        
    #    self._defineOutputs(**outputArgs)
    #    for pointer in self.inputVolumes:
    #        self._defineSourceRelation(pointer, outputArgs.values()[0])

    
    #--------------------------- INFO functions --------------------------------------------
    
    def _validate(self):
        errors = []
        for pointer in self.inputVolumes:
            if pointer.pointsNone():
                errors.append('Invalid input, pointer: %s' % pointer.getObjValue())
                errors.append('              extended: %s' % pointer.getExtended())
        return errors    
    
    #def _summary(self):
    #    summary = []
    #            
    #    return summary
    
    #def _methods(self):
    #    nVols = self._getNumberOfInputs()
    #        
    #    return [methods]
        
    #def _citations(self):
    #    if self.alignmentAlgorithm == ALIGN_ALGORITHM_FAST_FOURIER:
    #        return ['Chen2013']
        
    #--------------------------- UTILS functions --------------------------------------------
    def _iterInputVolumes(self):
        """ Iterate over all the input volumes. """
        for pointer in self.inputVolumes:
            item = pointer.get()
            if item is None:
                break
            itemId = item.getObjId()
            if isinstance(item, em.Volume):
                item.outputName = self._getExtraPath('output_vol%06d.vol' % itemId)
                yield item
            elif isinstance(item, em.SetOfVolumes):
                for vol in item:
                    vol.outputName = self._getExtraPath('output_vol%06d_%03d.vol' % (itemId, vol.getObjId()))
                    yield vol
                    
    def _getAlignArgs(self):
        alignArgs = ''
        
        if self.alignmentAlgorithm == ALIGN_ALGORITHM_FAST_FOURIER:
            alignArgs += " --frm"
            
        elif self.alignmentAlgorithm == ALIGN_ALGORITHM_LOCAL:
            alignArgs += " --local --rot %f %f 1 --tilt %f %f 1 --psi %f %f 1 -x %f %f 1 -y %f %f 1 -z %f %f 1 --scale %f %f 0.005" %\
               (self.initialRotAngle, self.initialRotAngle,
                self.initialTiltAngle, self.initialTiltAngle,
                self.initialInplaneAngle, self.initialInplaneAngle,
                self.initialShiftX, self.initialShiftX,
                self.initialShiftY, self.initialShiftY,
                self.initialShiftZ,self.initialShiftZ,
                self.initialScale, self.initialScale)
        else: # Exhaustive or Exhaustive+Local
            alignArgs += " --rot %f %f %f --tilt %f %f %f --psi %f %f %f -x %f %f %f -y %f %f %f -z %f %f %f --scale %f %f %f" %\
               (self.minRotationalAngle, self.maxRotationalAngle, self.stepRotationalAngle,
                self.minTiltAngle, self.maxTiltAngle, self.stepTiltAngle,
                self.minInplaneAngle, self.maxInplaneAngle, self.stepInplaneAngle,
                self.minimumShiftX, self.maximumShiftX, self.stepShiftX,
                self.minimumShiftY, self.maximumShiftY, self.stepShiftY,
                self.minimumShiftZ, self.maximumShiftZ, self.stepShiftZ,
                self.minimumScale, self.maximumScale, self.stepScale)
        return alignArgs
     
    def _getMaskArgs(self):
        maskArgs = ''
        if self.applyMask:
            if self.maskType == ALIGN_MASK_CIRCULAR:
                maskArgs+=" --mask circular -%d" % self.maskRadius
            else:
                maskArgs+=" --mask binary_file %s" % self.volMask
        return maskArgs
  