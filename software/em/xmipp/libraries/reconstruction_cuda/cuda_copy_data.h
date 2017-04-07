

#ifndef CUDA_COPYDATA_H
#define CUDA_COPYDATA_H

cudaPitchedPtr CopyVolumeHostToDevice(const float* host, uint width, uint height, uint depth);

void CopyVolumeDeviceToHost(float* host, const cudaPitchedPtr device, uint width, uint height, uint depth);

#endif
