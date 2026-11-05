"""Minimal reader of netCDF classic files (CDF-1 and CDF-2, the format of the CRU TS files), so that the build
environment needs no netCDF library. Format specification: Unidata, "The NetCDF Classic Format Specification"
(NetCDF Users Guide, file format appendix).

Usage:
    variables, attributes = read(raw_bytes)   # {name: numpy array}, {variable: {attribute: value}}
"""
import struct

import numpy as np

_NC_DIMENSION, _NC_VARIABLE, _NC_ATTRIBUTE = 0x0A, 0x0B, 0x0C
_TYPES = {1: ">i1", 2: "S1", 3: ">i2", 4: ">i4", 5: ">f4", 6: ">f8"}


class _Reader:
    def __init__(self, raw):
        self.raw, self.pos = raw, 0

    def int32(self):
        value = struct.unpack_from(">i", self.raw, self.pos)[0]
        self.pos += 4
        return value

    def offset(self, version):
        fmt, size = (">i", 4) if version == 1 else (">q", 8)
        value = struct.unpack_from(fmt, self.raw, self.pos)[0]
        self.pos += size
        return value

    def padded(self, size):
        data = self.raw[self.pos:self.pos + size]
        self.pos += (size + 3) // 4 * 4
        return data

    def name(self):
        return self.padded(self.int32()).decode("utf-8")

    def values(self, nc_type, count):
        dtype = np.dtype(_TYPES[nc_type])
        data = self.padded(dtype.itemsize * count)
        if nc_type == 2:
            return data.rstrip(b"\x00").decode("utf-8", "replace")
        return np.frombuffer(data, dtype=dtype)

    def list_header(self, tag):
        found, count = self.int32(), self.int32()
        assert found in (0, tag), "unexpected netCDF header tag %d" % found
        return count

    def attributes(self):
        result = {}
        for _ in range(self.list_header(_NC_ATTRIBUTE)):
            name = self.name()
            nc_type = self.int32()
            result[name] = self.values(nc_type, self.int32())
        return result


def read(raw):
    """Variables as numpy arrays (record variables with the record dimension first) and their attributes."""
    assert raw[:3] == b"CDF" and raw[3] in (1, 2), "not a netCDF classic file"
    version = raw[3]
    reader = _Reader(raw)
    reader.pos = 4
    records = reader.int32()
    dimensions = [(reader.name(), reader.int32()) for _ in range(reader.list_header(_NC_DIMENSION))]
    attributes = {"": reader.attributes()}
    layout = []
    for _ in range(reader.list_header(_NC_VARIABLE)):
        name = reader.name()
        dim_ids = [reader.int32() for _ in range(reader.int32())]
        attributes[name] = reader.attributes()
        nc_type = reader.int32()
        vsize = reader.int32()
        begin = reader.offset(version)
        layout.append((name, dim_ids, nc_type, vsize, begin))
    record_vars = [v for v in layout if v[1] and dimensions[v[1][0]][1] == 0]
    record_size = sum(v[3] for v in record_vars)
    variables = {}
    for name, dim_ids, nc_type, vsize, begin in layout:
        dtype = np.dtype(_TYPES[nc_type])
        shape = [dimensions[i][1] for i in dim_ids]
        if (name, dim_ids, nc_type, vsize, begin) in record_vars:
            shape[0] = records
            per_record = int(np.prod(shape[1:], dtype=np.int64)) * dtype.itemsize
            stride = per_record if len(record_vars) == 1 else record_size
            chunks = [raw[begin + r * stride:begin + r * stride + per_record] for r in range(records)]
            variables[name] = np.frombuffer(b"".join(chunks), dtype=dtype).reshape(shape)
        else:
            count = int(np.prod(shape, dtype=np.int64))
            variables[name] = np.frombuffer(raw, dtype=dtype, count=count, offset=begin).reshape(shape)
    return variables, attributes
