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
    def read_uint64(file_handle, packStr=GcovConst.PACKUINT32):
        """
            uint64:  uint32:low uint32:high
        """
        lowOrder = GcovIO.read_uint32(file_handle, packStr)
        highOrder = GcovIO.read_uint32(file_handle, packStr)

        val = (highOrder << 32) | lowOrder

        return val
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
    def write_quad_char(file_handle, quad_char):
        """
            uint32 in quad char format
        """
        file_handle.write(quad_char)
        return

    @staticmethod
    def write_uint32(file_handle, val, packStr=GcovConst.PACKUINT32):
        """
            uint32:  byte3 byte2 byte1 byte0 | byte0 byte1 byte2 byte3
        """
        file_handle.write(struct.pack(packStr, val))
        return

    @staticmethod
    def write_uint64(file_handle, val):
        """
            uint64:  uint32:low uint32:high
        """
        lowOrder = val & GcovConst.LOWORDERMASK
        highOrder = (val & GcovConst.HIGHORDERMASK) >> 32

        # Write the low order word
        GcovIO.write_uint32(file_handle, lowOrder)

        # Write the high order word
        GcovIO.write_uint32(file_handle, highOrder)
        return