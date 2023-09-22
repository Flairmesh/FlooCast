################################################################################
#  HidDfuAPI.py : Declares the DLL functions for Python.
#  Copyright (c) 2023 Qualcomm Technologies International, Ltd.
#  All Rights Reserved.
#  Qualcomm Technologies International, Ltd. Confidential and Proprietary.
#
#  Auto-generated Python wrapper for HidDfu DLL.
#  Created on 2023-02-25 00:32 from HidDfu.h file"
################################################################################

import os
import ctypes as ct
from typing import Tuple

class HidDfu():
    """
    A python wrapper class for HidDfu DLL.
    Usage:
        myDll = HidDfu("<DLL_PATH>" [, debug=False])    
    """
    def __init__(self, path_to_dll):
        """Load the HidDfu DLL"""
        self.HidDfuDLL = None
        try:
            full_path = os.path.realpath(path_to_dll)
            if full_path.strip().lower().endswith('.dll'):
                path_to_dll = os.path.dirname(full_path) + '\\'  # Extract directory from DLL name
                
            if not path_to_dll.endswith('\\'):
                path_to_dll += '\\'

            if not path_to_dll + ';' in os.environ['PATH']: # add this to the path if not already present
                os.environ['PATH'] = path_to_dll + ';' + os.environ['PATH']

            self.HidDfuDLL = ct.windll.LoadLibrary(path_to_dll + 'HidDfu')
        except Exception as e:
            print("Cannot load HidDfu.dll from " + path_to_dll)
            if ct.sizeof(ct.c_void_p) == 8:
                print("Check that the DLL is present and 64 bit.\n"
                      "64 bit Python can only be used with 64 bit DLL")
            else:
                print("Check that the DLL is present and 32 bit\n"
                      "32 bit Python can only be used with 32 bit DLL")
            raise e
    # end __init__

    #
    # Pre-defined constants that may be used as parameter values or returns from the HidDfu API
    #
    PROGRESS_REBOOT_VALUE = 95
    RESTART_DELAY_SEC = 60

    HIDDFU_ERROR_NONE = 0
    HIDDFU_ERROR_SEQUENCE = -1
    HIDDFU_ERROR_CONNECTION = -2
    HIDDFU_ERROR_FILE_OPEN_FAILED = -3
    HIDDFU_ERROR_FILE_WRITE_FAILED = -4
    HIDDFU_ERROR_FILE_INVALID_FORMAT = -5
    HIDDFU_ERROR_FILE_CRC_INCORRECT = -6
    HIDDFU_ERROR_FILE_READ_FAILED = -7
    HIDDFU_ERROR_UPGRADE_FAILED = -8
    HIDDFU_ERROR_RESET_FAILED = -9
    HIDDFU_ERROR_OUT_OF_MEM = -10
    HIDDFU_ERROR_INVALID_PARAMETER = -11
    HIDDFU_ERROR_DRIVER_INTERFACE_FAILURE = -12
    HIDDFU_ERROR_OPERATION_FAILED_TO_START = -13
    HIDDFU_ERROR_BUSY = -14
    HIDDFU_ERROR_CLEAR_STATUS_FAILED = -15
    HIDDFU_ERROR_DEVICE_FIRMWARE = -16
    HIDDFU_ERROR_UNSUPPORTED = -17
    HIDDFU_ERROR_OPERATION_PARTIAL_SUCCESS = -18
    HIDDFU_ERROR_PARAM_TOO_SMALL = -19
    HIDDFU_ERROR_UNKNOWN = -20
    HIDDFU_ERROR_VERSION_MISMATCH = -21
    HIDDFU_ERROR_NO_OP_IN_PROGRESS = -22
    HIDDFU_ERROR_NO_RESPONSE = -23
    HIDDFU_ERROR_OP_PARTIAL_SUCCESS_NO_RESPONSE = -24

    #
    # Exported routines for the HidDfu API
    #

    def hidDfuGetFirmwareVersions(self, versionString: str='', maxLength: int=0, checkMatch: int=0) -> Tuple[int, str, int]:
        r"""Function HidDfu::hidDfuGetFirmwareVersions() wrapper for hidDfuGetFirmwareVersions in HidDfu DLL.

        Python API:
            hidDfuGetFirmwareVersions(versionString: str='', maxLength: int=0, checkMatch: int=0) -> Tuple[int, str, int]

        Python Example Call Syntax:
            retval, versionString, maxLength = myDll.hidDfuGetFirmwareVersions(checkMatch=0)
            print(retval, versionString, maxLength)

        Detail From Wrapped C API:
            Function :      int32 hidDfuGetFirmwareVersions(char* versionString,
                                                            uint16* maxLength,
                                                            uint8 checkMatch);

            Parameters :    versionString - 
                                Pointer to a buffer where the comma/semicolon separated
                                string representing device version information for all
                                the connected devices will be written. The format of the
                                string is:
                                "dev1_ver_major,dev1_ver_minor,dev1_config_ver;dev1_ver_major,..."

                            maxLength -
                                Length of the versionString buffer, returns expected
                                length if the length given is less than is required to
                                store the version string.

                            checkMatch -
                                Boolean value - set to 1 to check if all the devices
                                have the same version, 0 otherwise.

            Returns :       An error code, either HIDDFU_ERROR_NONE if successful, or
                            one of the other HIDDFU_ERROR_ codes defined in this file.

            Description :   This function gets the version information of the connected
                            devices. A device connection is required.

        """
        self.HidDfuDLL.hidDfuGetFirmwareVersions.restype = ct.c_int32
        self.HidDfuDLL.hidDfuGetFirmwareVersions.argtypes = [ct.c_char_p, ct.c_void_p, ct.c_uint8]
        local_versionString = None if versionString is None else ct.create_string_buffer(bytes(versionString, encoding="UTF-8"), 1024 if maxLength < 1024 else maxLength)
        local_maxLength = ct.c_uint16(maxLength)
        retval = self.HidDfuDLL.hidDfuGetFirmwareVersions(local_versionString, ct.byref(local_maxLength), checkMatch)
        versionString = local_versionString.value.decode()
        maxLength = local_maxLength.value
        return retval, versionString, maxLength
    # end of hidDfuGetFirmwareVersions


    def hidDfuGetVersion(self, major: int=0, minor: int=0, release: int=0, build: int=0) -> Tuple[int, int, int, int, int]:
        r"""Function HidDfu::hidDfuGetVersion() wrapper for hidDfuGetVersion in HidDfu DLL.

        Python API:
            hidDfuGetVersion(major: int=0, minor: int=0, release: int=0, build: int=0) -> Tuple[int, int, int, int, int]

        Python Example Call Syntax:
            retval, major, minor, release, build = myDll.hidDfuGetVersion()
            print(retval, major, minor, release, build)

        Detail From Wrapped C API:
            Function :      int32 hidDfuGetVersion(uint16* major, uint16* minor, 
                                                   uint16* release, uint16* build)

            Parameters :    major - 
                                Location to store the major version number.

                            minor -
                                Location to store the minor version number.

                            release -
                                Location to store the release number.

                            build -
                                Location to store the build number.

            Returns :       An error code, either HIDDFU_ERROR_NONE if successful, or 
                            one of the other HIDDFU_ERROR_ codes defined in this file.

            Description :   This function gets the version information of the HidDfu 
                            DLL. A device connection is not required.

        """
        self.HidDfuDLL.hidDfuGetVersion.restype = ct.c_int32
        self.HidDfuDLL.hidDfuGetVersion.argtypes = [ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p]
        local_major = ct.c_uint16(major)
        local_minor = ct.c_uint16(minor)
        local_release = ct.c_uint16(release)
        local_build = ct.c_uint16(build)
        retval = self.HidDfuDLL.hidDfuGetVersion(ct.byref(local_major), ct.byref(local_minor), ct.byref(local_release), ct.byref(local_build))
        major = local_major.value
        minor = local_minor.value
        release = local_release.value
        build = local_build.value
        return retval, major, minor, release, build
    # end of hidDfuGetVersion


    def hidDfuConnect(self, vid: int, pid: int, usage: int, usagePage: int, count: int=0) -> Tuple[int, int]:
        r"""Function HidDfu::hidDfuConnect() wrapper for hidDfuConnect in HidDfu DLL.

        Python API:
            hidDfuConnect(vid: int, pid: int, usage: int, usagePage: int, count: int=0) -> Tuple[int, int]

        Python Example Call Syntax:
            retval, count = myDll.hidDfuConnect(vid=0, pid=0, usage=0, usagePage=0)
            print(retval, count)

        Detail From Wrapped C API:
            Function :      int32 hidDfuConnect(uint16 vid, uint16 pid, uint16 usage,
                                                uint16 usagePage, uint16* count)

            Parameters :    vid -
                                Target device USB Vendor ID.

                            pid -
                                Target device USB Product ID.

                            usage -
                                Target device USB usage value. Set this value to 0 to 
                                ignore the device usage value.

                                <p>For QCC304x-8x and QCC514x-8x devices usage must be
                                0x1.

                            usagePage -
                                Target device USB usagePage value. Set this value to 
                                0 to ignore the device usagePage value.

                                <p>For CSRA681xx, QCC302x-8x and QCC512x-8x devices
                                usagePage must be 0xFF00.

                            count -
                                The number of HidDfu devices found.

            Returns :       An error code, either HIDDFU_ERROR_NONE if successful, or
                            one of the other HIDDFU_ERROR_ codes defined in this file.

            Description :   Attempts to connect to the specified USB devices. If
                            multiple matching devices are connected to the system, a
                            connection attempt will be made with all the matching
                            devices found.

                            <p>Consecutive calls to hidDfuConnect cannot be made unless
                            hidDfuDisconnect is called in between. If any of the devices
                            are to be plugged in/out after calling hidDfuConnect, then
                            they should be disconnected first using hidDfuDisconnect,
                            and only then plugged in/out; after which hidDfuConnect
                            could be called again to connect to HID devices.

        """
        self.HidDfuDLL.hidDfuConnect.restype = ct.c_int32
        self.HidDfuDLL.hidDfuConnect.argtypes = [ct.c_uint16, ct.c_uint16, ct.c_uint16, ct.c_uint16, ct.c_void_p]
        local_count = ct.c_uint16(count)
        retval = self.HidDfuDLL.hidDfuConnect(vid, pid, usage, usagePage, ct.byref(local_count))
        count = local_count.value
        return retval, count
    # end of hidDfuConnect


    def hidDfuDisconnect(self) -> int:
        r"""Function HidDfu::hidDfuDisconnect() wrapper for hidDfuDisconnect in HidDfu DLL.

        Python API:
            hidDfuDisconnect() -> int

        Python Example Call Syntax:
            retval = myDll.hidDfuDisconnect()
            print(retval)

        Detail From Wrapped C API:
            Function :      int32 hidDfuDisconnect(void)

            Parameters :    None

            Returns :       An error code, either HIDDFU_ERROR_NONE if successful, or 
                            one of the other HIDDFU_ERROR_ codes defined in this file.

            Description :   Disconnects from currently connected devices. If a device is
                            not connected, does nothing and returns HIDDFU_ERROR_NONE.

        """
        self.HidDfuDLL.hidDfuDisconnect.restype = ct.c_int32
        self.HidDfuDLL.hidDfuDisconnect.argtypes = []
        
        retval = self.HidDfuDLL.hidDfuDisconnect()
        
        return retval
    # end of hidDfuDisconnect


    def hidDfuBackup(self, fileName: str, resetAfter: int) -> int:
        r"""Function HidDfu::hidDfuBackup() wrapper for hidDfuBackup in HidDfu DLL.

        Python API:
            hidDfuBackup(fileName: str, resetAfter: int) -> int

        Python Example Call Syntax:
            retval = myDll.hidDfuBackup(fileName='abc', resetAfter=0)
            print(retval)

        Detail From Wrapped C API:
            Function :      int32 hidDfuBackup(const char* fileName, uint8 resetAfter)

            Parameters :    fileName -
                                Name of backup image file to write

                            resetAfter -
                                Reset the devices after backup

            Returns :       An error code, either HIDDFU_ERROR_NONE if successful, or 
                            one of the other HIDDFU_ERROR_ codes defined in this file.

            Description :   Reads the image from the connected BlueCore chip and saves
                            to the specified file. If there are multiple devices, files
                            are suffixed with a "-" and a number. The number is based on
                            the order in which the devices were enumerated by the system.
                            This function starts the operation. Use hidDfuGetProgress
                            to check for completion and hidDfuGetResult to get the final
                            status.

                            <p>This function is not supported for CSRA681xx,
                            QCC302x-8x and QCC512x-8x devices.

        """
        self.HidDfuDLL.hidDfuBackup.restype = ct.c_int32
        self.HidDfuDLL.hidDfuBackup.argtypes = [ct.c_char_p, ct.c_uint8]
        local_fileName = None if fileName is None else ct.create_string_buffer(bytes(fileName, encoding="UTF-8"))
        retval = self.HidDfuDLL.hidDfuBackup(local_fileName, resetAfter)
        
        return retval
    # end of hidDfuBackup


    def hidDfuUpgrade(self, fileName: str, resetAfter: int) -> int:
        r"""Function HidDfu::hidDfuUpgrade() wrapper for hidDfuUpgrade in HidDfu DLL.

        Python API:
            hidDfuUpgrade(fileName: str, resetAfter: int) -> int

        Python Example Call Syntax:
            retval = myDll.hidDfuUpgrade(fileName='abc', resetAfter=0)
            print(retval)

        Detail From Wrapped C API:
            Function :      int32 hidDfuUpgrade(const char* fileName, uint8 resetAfter)

            Parameters :    fileName -
                                Name of upgrade image file

                            resetAfter -
                                Reset the devices after upgrade

            Returns :       An error code, either HIDDFU_ERROR_NONE if successful, or 
                            one of the other HIDDFU_ERROR_ codes defined in this file.

            Description :   Reads an image from the specified file and upgrades the 
                            connected BlueCore devices. This function starts the 
                            operation. Use hidDfuGetProgress to check for completion 
                            and hidDfuGetResult to get the final status.

                            <p>For a particular device there can be only one instance of
                            upgrade/backup running at any time.

                            <p>This function is not supported for CSRA681xx,
                            QCC302x-8x and QCC512x-8x devices - use hidDfuUpgradeBin
                            instead.

        """
        self.HidDfuDLL.hidDfuUpgrade.restype = ct.c_int32
        self.HidDfuDLL.hidDfuUpgrade.argtypes = [ct.c_char_p, ct.c_uint8]
        local_fileName = None if fileName is None else ct.create_string_buffer(bytes(fileName, encoding="UTF-8"))
        retval = self.HidDfuDLL.hidDfuUpgrade(local_fileName, resetAfter)
        
        return retval
    # end of hidDfuUpgrade


    def hidDfuUpgradeBin(self, fileName: str) -> int:
        r"""Function HidDfu::hidDfuUpgradeBin() wrapper for hidDfuUpgradeBin in HidDfu DLL.

        Python API:
            hidDfuUpgradeBin(fileName: str) -> int

        Python Example Call Syntax:
            retval = myDll.hidDfuUpgradeBin(fileName='abc')
            print(retval)

        Detail From Wrapped C API:
            Function :      int32 hidDfuUpgradeBin(const char* fileName)

            Parameters :    fileName -
                                Name of upgrade binary image file

            Returns :       An error code, either HIDDFU_ERROR_NONE if successful, or 
                            one of the other HIDDFU_ERROR_ codes defined in this file.

            Description :   Reads a binary image from the specified file and upgrades
                            the connected device(s). This function starts the operation.
                            Use hidDfuGetResult to get the final status.

                            <p>For a particular device there can be only one instance of
                            upgrade/backup running at any time.

                            <p>This function is supported for CSRA681xx, QCC302x-8x
                            and QCC512x-8x devices only.

        """
        self.HidDfuDLL.hidDfuUpgradeBin.restype = ct.c_int32
        self.HidDfuDLL.hidDfuUpgradeBin.argtypes = [ct.c_char_p]
        local_fileName = None if fileName is None else ct.create_string_buffer(bytes(fileName, encoding="UTF-8"))
        retval = self.HidDfuDLL.hidDfuUpgradeBin(local_fileName)
        
        return retval
    # end of hidDfuUpgradeBin


    def hidDfuStop(self, waitForStopMs: int) -> int:
        r"""Function HidDfu::hidDfuStop() wrapper for hidDfuStop in HidDfu DLL.

        Python API:
            hidDfuStop(waitForStopMs: int) -> int

        Python Example Call Syntax:
            retval = myDll.hidDfuStop(waitForStopMs=0)
            print(retval)

        Detail From Wrapped C API:
            Function :      int32 hidDfuStop(uint16 waitForStopMs)

            Parameters :    waitForStopMs -
                                Wait time (in milliseconds) for operation to stop.

            Returns :       An error code, either HIDDFU_ERROR_NONE if a running
                            operation has been stopped, HIDDFU_ERROR_NO_OP_IN_PROGRESS
                            if no operation is running or HIDDFU_ERROR_UNKNOWN on failure.

            Description :   Stop an ongoing hidDfuUpgrade, hidDfuBackup or
                            hidDfuUpgradeBin operation.

        """
        self.HidDfuDLL.hidDfuStop.restype = ct.c_int32
        self.HidDfuDLL.hidDfuStop.argtypes = [ct.c_uint16]
        
        retval = self.HidDfuDLL.hidDfuStop(waitForStopMs)
        
        return retval
    # end of hidDfuStop


    def hidDfuResetDevice(self) -> int:
        r"""Function HidDfu::hidDfuResetDevice() wrapper for hidDfuResetDevice in HidDfu DLL.

        Python API:
            hidDfuResetDevice() -> int

        Python Example Call Syntax:
            retval = myDll.hidDfuResetDevice()
            print(retval)

        Detail From Wrapped C API:
            Function :      int32 hidDfuResetDevice(void)

            Parameters :    None

            Returns :       An error code, either HIDDFU_ERROR_NONE if successful, or 
                            one of the other HIDDFU_ERROR_ codes defined in this file.

            Description :   This function resets the connected devices, causing the
                            devices to exit DFU mode. If the reset is successful, the
                            device connections are also closed.

                            <p>The reset is performed in a single thread (i.e. main
                            thread) for all devices. After the devices are reset,
                            hidDfuConnect should be called before any other API
                            function in order to reconnect with the devices.

                            <p>This function is not supported for CSRA681xx,
                            QCC302x-8x and QCC512x-8x devices.

        """
        self.HidDfuDLL.hidDfuResetDevice.restype = ct.c_int32
        self.HidDfuDLL.hidDfuResetDevice.argtypes = []
        
        retval = self.HidDfuDLL.hidDfuResetDevice()
        
        return retval
    # end of hidDfuResetDevice


    def hidDfuGetProgress(self) -> int:
        r"""Function HidDfu::hidDfuGetProgress() wrapper for hidDfuGetProgress in HidDfu DLL.

        Python API:
            hidDfuGetProgress() -> int

        Python Example Call Syntax:
            retval = myDll.hidDfuGetProgress()
            print(retval)

        Detail From Wrapped C API:
            Function :      uint8 hidDfuGetProgress(void)

            Parameters :    None

            Returns :       The progress of an operation (percentage).

            Description :   This function gets the progress of on-going upgrade or
                            backup operations for the devices. For operations performed
                            on multiple devices, the average (mean) percentage for all
                            devices is returned. If an operation has finished, 100 is
                            returned.

        """
        self.HidDfuDLL.hidDfuGetProgress.restype = ct.c_uint8
        self.HidDfuDLL.hidDfuGetProgress.argtypes = []
        
        retval = self.HidDfuDLL.hidDfuGetProgress()
        
        return retval
    # end of hidDfuGetProgress


    def hidDfuGetResult(self) -> int:
        r"""Function HidDfu::hidDfuGetResult() wrapper for hidDfuGetResult in HidDfu DLL.

        Python API:
            hidDfuGetResult() -> int

        Python Example Call Syntax:
            retval = myDll.hidDfuGetResult()
            print(retval)

        Detail From Wrapped C API:
            Function :      int32 hidDfuGetResult(void)

            Parameters :    None

            Returns :       The result for the last completed operation, either
                            HIDDFU_ERROR_NONE if successful, or one of the other
                            HIDDFU_ERROR_ codes defined in this file.

            Description :   This function gets the result of the last completed
                            operation. Returns an error if an operation has not been
                            run, if an operation is ongoing, or if the last operation
                            failed.

                            <p>If there are multiple devices, and all failed devices
                            have the same error, then that error code is returned. If
                            there are different errors, HIDDFU_ERROR_UNKNOWN will be
                            returned.

                            <p>Use hidDfuGetLastError to get the description in the 
                            case of an error.

        """
        self.HidDfuDLL.hidDfuGetResult.restype = ct.c_int32
        self.HidDfuDLL.hidDfuGetResult.argtypes = []
        
        retval = self.HidDfuDLL.hidDfuGetResult()
        
        return retval
    # end of hidDfuGetResult


    def hidDfuGetLastError(self) -> int:
        r"""Function HidDfu::hidDfuGetLastError() wrapper for hidDfuGetLastError in HidDfu DLL.

        Python API:
            hidDfuGetLastError() -> int

        Python Example Call Syntax:
            retval = myDll.hidDfuGetLastError()
            print(retval)

        Detail From Wrapped C API:
            Function :      const char* hidDfuGetLastError(void)

            Parameters :    None

            Returns :       The details of the last error.

            Description :   This function gets a description of the last error.

        """
        self.HidDfuDLL.hidDfuGetLastError.restype = ct.c_char_p
        self.HidDfuDLL.hidDfuGetLastError.argtypes = []
        
        retval = self.HidDfuDLL.hidDfuGetLastError()
        
        return retval
    # end of hidDfuGetLastError


    def hidDfuGetFailedDevicesCount(self) -> int:
        r"""Function HidDfu::hidDfuGetFailedDevicesCount() wrapper for hidDfuGetFailedDevicesCount in HidDfu DLL.

        Python API:
            hidDfuGetFailedDevicesCount() -> int

        Python Example Call Syntax:
            retval = myDll.hidDfuGetFailedDevicesCount()
            print(retval)

        Detail From Wrapped C API:
            Function :      uint8 hidDfuGetFailedDevicesCount(void)

            Parameters :    None

            Returns :       The number of devices which failed for the last upgrade or
                            backup operation.

            Description :   This function gets the count of failed devices, in the event
                            of an upgrade or backup failure.

        """
        self.HidDfuDLL.hidDfuGetFailedDevicesCount.restype = ct.c_uint8
        self.HidDfuDLL.hidDfuGetFailedDevicesCount.argtypes = []
        
        retval = self.HidDfuDLL.hidDfuGetFailedDevicesCount()
        
        return retval
    # end of hidDfuGetFailedDevicesCount


    def hidDfuSendCommand(self, data: int, length: int) -> int:
        r"""Function HidDfu::hidDfuSendCommand() wrapper for hidDfuSendCommand in HidDfu DLL.

        Python API:
            hidDfuSendCommand(data: int, length: int) -> int

        Python Example Call Syntax:
            retval = myDll.hidDfuSendCommand(data=0, length=0)
            print(retval)

        Detail From Wrapped C API:
            Function :      int32 hidDfuSendCommand(const uint8* data, uint32 length)

            Parameters :    data -
                                The command data to send.

                            length -
                                Length of the data (in bytes).

            Returns :       An error code, either HIDDFU_ERROR_NONE if successful, or 
                            one of the other HIDDFU_ERROR_ codes defined in this file.

            Description :   Sends a custom command to a connected devices. This function
                            can be used to cause the connected devices to switch from
                            normal mode to DFU mode (after which hidDfuDisconnect and
                            hidDfuConnect can be called to reconnect using the DFU mode
                            connection parameters).

                            <p>The operation runs in a single thread (i.e. main thread)
                            for all devices.

                            <p>This function is not supported for CSRA681xx,
                            QCC302x-8x and QCC512x-8x devices.

        """
        self.HidDfuDLL.hidDfuSendCommand.restype = ct.c_int32
        self.HidDfuDLL.hidDfuSendCommand.argtypes = [ct.c_void_p, ct.c_uint32]
        local_data = ct.c_uint8(data)
        retval = self.HidDfuDLL.hidDfuSendCommand(ct.byref(local_data), length)
        data = local_data.value
        return retval
    # end of hidDfuSendCommand




# endclass HidDfu

  