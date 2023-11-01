import struct

import GcovConst


class GcovIO:
    @staticmethod
    def unpack_uint32(buffer, pos, packStr=GcovConst.PACKUINT32):

        # Note: The comma is important because the return type from struct.unpack_from is a tuple
        val, = struct.unpack_from(packStr, buffer, pos)
        cpos = pos + 4
        return val, cpos

    @staticmethod
    def unpack_uint64(buffer, pos, packStr=GcovConst.PACKUINT32):

        cpos = pos

        # Note: The comma is important because the return type from struct.unpack_from is a tuple
        lowOrder, = struct.unpack_from(packStr, buffer, cpos)
        cpos = cpos + 4

        highOrder, = struct.unpack_from(packStr, buffer, cpos)
        cpos = cpos + 4

        val = (highOrder << 32) | lowOrder

        return val, cpos

    @staticmethod
    def unpack_string(buffer, pos, strWords):

        val = None

        if strWords > 0:
            strlen = strWords * 4
            strend = pos + strlen

            buffSlice = buffer[pos: strend]
            val = buffSlice.rstrip(b'\x00').decode()

            cpos = pos + strlen

        return val, cpos

    @staticmethod
    def read_quad_char(file_handle):
        """
            uint32:  byte3 byte2 byte1 byte0 | byte0 byte1 byte2 byte3
        """
        quadByte = file_handle.read(4)
        if len(quadByte) < 4:
            print("ERROR: Problem reading UInt32, not enough bytes left in record. quadByte=%s" % quadByte)

        return quadByte

    @staticmethod
    def read_uint32(file_handle, packStr=GcovConst.PACKUINT32):
        """
            uint32:  byte3 byte2 byte1 byte0 | byte0 byte1 byte2 byte3
        """
        quadByte = file_handle.read(4)
        if len(quadByte) < 4:
            print("ERROR: Problem reading UInt32, not enough bytes left in record. quadByte=%s" % quadByte)

        val, = struct.unpack(packStr, quadByte)

        return val