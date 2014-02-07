# **************************************************************************
# *
# * Authors:     Josue Gomez Blanco (jgomez@cnb.csic.es)
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
"""
This sub-package contains wrapper around resolution3D Xmipp protocol
"""


from pyworkflow.em import *  
from pyworkflow.utils import *  
from math import floor
from xmipp3 import XmippProtocol
from convert import createXmippInputVolumes, readSetOfVolumes


class XmippProtResolution3D(ProtValidate3D):
    """ Protocol for Xmipp-based resolution3D """
    _label = 'resolution 3D'
      

    def _defineParams(self, form):
        form.addSection(label='Input')
        # Volumes to process
        form.addParam('inputVolume', PointerParam, label="Volume to compare", important=True, 
                      pointerClass='Volume',
                      help='This volume will be compared to the reference volume.')  
        form.addParam('doFSC', BooleanParam, default=True,
                      label="Calculate FSC?", 
                      help='If set True calculate FSC and DPR.')
        form.addParam('referenceVolume', PointerParam, label="Reference volume", condition='doFSC', 
                      pointerClass='Volume',
                      help='Input volume will be compared to this volume.')  
        form.addParam('doStructureFactor', BooleanParam, default=True,
                      label="Calculate Structure Factor?", 
                      help='If set True calculate Structure Factor')
        form.addParam('doSSNR', BooleanParam, default=True,
                      label="Calculate Spectral SNR?", 
                      help='If set True calculate Structure Factor')
        form.addParam('doVSSNR', BooleanParam, default=False,
                      label="Calculate Volumetric Spectral SNR?", 
                      help='If set True calculate Structure Factor')

#        form.addParallelSection(threads=1, mpi=8)         
    
    def _insertAllSteps(self):
        """Insert all steps to calculate the resolution of a 3D reconstruction. """
        
        self.inputVol = self.inputVolume.get().locationToXmipp()
        self.refVol = self.referenceVolume.get().locationToXmipp()
        
        if self.doFSC:
            self._insertFunctionStep('calculateFscStep')
        if self.doStructureFactor:
            self._insertFunctionStep('structureFactorcStep')
        if self.doSSNR or self.doVSSNR:
            # Implement when RECONSTRUCTOR method is implemented
            pass
        
#         self._insertFunctionStep('createOutput')
        
    def _defineMetadataRootName(self, mdrootname):
        
        if mdrootname=='fsc':
            return self._getPath('fsc.xmd')
        if mdrootname=='structureFactor':
            return self._getPath('structureFactor.xmd')
        
    def _defineStructFactorName(self):
        structFactFn = self._defineMetadataRootName('structureFactor')
        return structFactFn
    
    def _defineFscName(self):
        fscFn = self._defineMetadataRootName('fsc')
        return fscFn
         
    def calculateFscStep(self):
        """ Calculate the FSC between two volumes"""
        
        samplingRate = self.inputVolume.get().getSamplingRate()
        fscFn = self._defineFscName()
        args="--ref %s -i %s -o %s --sampling_rate %f --do_dpr" % (self.refVol, self.inputVol, fscFn, samplingRate)
        self.runJob(None, "xmipp_resolution_fsc", args)
    
    def structureFactorcStep(self):
        """ Calculate the structure factors of the volume"""
        
        samplingRate = self.inputVolume.get().getSamplingRate()
        structureFn = self._defineStructFactorName()
        args = "-i %s -o %s --sampling %f" % (self.inputVol, structureFn, samplingRate)
        self.runJob(None, "xmipp_volume_structure_factor", args)
        
    def _validate(self):
        validateMsgs = []
        
        if not self.inputVolume.hasValue():
            validateMsgs.append('Please provide an initial volume.')
        if self.doFSC and not self.referenceVolume.hasValue():
            validateMsgs.append('Please provide a reference volume.')
            
        return validateMsgs
    
    def _summary(self):
        summary = []
        summary.append("Input volumes:  %s" % self.inputVolume.get().getNameId())
        
        return summary
        
    def _citations(self):
        papers=[]
        if self.doSSNR or self.doVSSNR:
            papers.append('[%s] %s'%('Unser2005_SSNR',self._package._referencesDict['Unser2005_SSNR']))
        return papers
