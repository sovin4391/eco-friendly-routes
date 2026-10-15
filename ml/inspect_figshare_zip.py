"""
Inspects the central directory of RDD2022_released_through_CRDDC2022.zip on Figshare
using HTTP Range requests to examine the country archives without downloading 13 GB.
"""
import struct
import urllib.request
import sys

TOTAL_SIZE = 13264172619
TAIL_SIZE = 2 * 1024 * 1024
FIGSHARE_URL = "https://ndownloader.figshare.com/files/38030910"

def get_country_archives():
    req = urllib.request.Request(
        FIGSHARE_URL,
        headers={"User-Agent": "Mozilla/5.0", "Range": f"bytes={TOTAL_SIZE - TAIL_SIZE}-{TOTAL_SIZE - 1}"}
    )
    with urllib.request.urlopen(req, timeout=25) as res:
        tail = res.read()

    # Find Zip64 EOCD Locator
    locator_pos = tail.rfind(b"PK\x06\x07")
    if locator_pos == -1:
        raise RuntimeError("Zip64 locator not found")

    disk_num, zip64_eocd_offset, total_disks = struct.unpack("<IQI", tail[locator_pos+4:locator_pos+20])
    
    # Locate Zip64 EOCD
    zip64_eocd_pos = tail.rfind(b"PK\x06\x06")
    rec = tail[zip64_eocd_pos:zip64_eocd_pos+56]
    _, _, _, _, _, _, total_entries, cd_size, cd_offset = struct.unpack("<QHHIIQQQQ", rec[4:56])

    cd_rel = cd_offset - (TOTAL_SIZE - TAIL_SIZE)
    cd_data = tail[cd_rel:]
    
    pos = 0
    items = []
    while pos < len(cd_data) and cd_data[pos:pos+4] == b"PK\x01\x02":
        method = struct.unpack("<H", cd_data[pos+10:pos+12])[0]
        comp_size = struct.unpack("<I", cd_data[pos+20:pos+24])[0]
        uncomp_size = struct.unpack("<I", cd_data[pos+24:pos+28])[0]
        name_len = struct.unpack("<H", cd_data[pos+28:pos+30])[0]
        extra_len = struct.unpack("<H", cd_data[pos+30:pos+32])[0]
        comm_len = struct.unpack("<H", cd_data[pos+32:pos+34])[0]
        local_offset = struct.unpack("<I", cd_data[pos+42:pos+46])[0]

        name = cd_data[pos+46:pos+46+name_len].decode("utf-8", errors="replace")
        extra = cd_data[pos+46+name_len:pos+46+name_len+extra_len]

        if local_offset == 0xFFFFFFFF or comp_size == 0xFFFFFFFF or uncomp_size == 0xFFFFFFFF:
            epos = 0
            while epos < len(extra):
                eid, esize = struct.unpack("<HH", extra[epos:epos+4])
                if eid == 1:
                    idx = epos + 4
                    if uncomp_size == 0xFFFFFFFF:
                        uncomp_size = struct.unpack("<Q", extra[idx:idx+8])[0]
                        idx += 8
                    if comp_size == 0xFFFFFFFF:
                        comp_size = struct.unpack("<Q", extra[idx:idx+8])[0]
                        idx += 8
                    if local_offset == 0xFFFFFFFF:
                        local_offset = struct.unpack("<Q", extra[idx:idx+8])[0]
                        idx += 8
                    break
                epos += 4 + esize

        items.append({
            "name": name,
            "method": method,
            "comp_size": comp_size,
            "uncomp_size": uncomp_size,
            "local_offset": local_offset,
        })
        pos += 46 + name_len + extra_len + comm_len

    return items


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    items = get_country_archives()
    print(f"Found {len(items)} country packages inside Figshare RDD2022 zip:")
    for item in items:
        name = item["name"]
        method_str = "STORED (0% compression)" if item["method"] == 0 else "DEFLATED"
        size_mb = item["comp_size"] / (1024 * 1024)
        print(f"  {name:32} | {size_mb:9.2f} MB | {method_str} | Offset: {item['local_offset']}")
