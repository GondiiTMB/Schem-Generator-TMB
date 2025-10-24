import gzip
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
from nbtlib import Compound, File
from nbtlib.tag import ByteArray, Int, Short

try:
    import litemapy
except ImportError:  # pragma: no cover - optional dependency for litematics
    litemapy = None


LEGACY_BLOCK_MAP: Dict[str, Tuple[int, int]] = {
    "minecraft:air": (0, 0),
    "minecraft:stone": (1, 0),
    "minecraft:grass_block": (2, 0),
    "minecraft:dirt": (3, 0),
    "minecraft:cobblestone": (4, 0),
    "minecraft:oak_planks": (5, 0),
    "minecraft:spruce_planks": (5, 1),
    "minecraft:birch_planks": (5, 2),
    "minecraft:jungle_planks": (5, 3),
    "minecraft:oak_sapling": (6, 0),
    "minecraft:bedrock": (7, 0),
    "minecraft:water": (9, 0),
    "minecraft:lava": (11, 0),
    "minecraft:sand": (12, 0),
    "minecraft:gravel": (13, 0),
    "minecraft:gold_ore": (14, 0),
    "minecraft:iron_ore": (15, 0),
    "minecraft:coal_ore": (16, 0),
    "minecraft:oak_log": (17, 0),
    "minecraft:spruce_log": (17, 1),
    "minecraft:birch_log": (17, 2),
    "minecraft:jungle_log": (17, 3),
    "minecraft:oak_leaves": (18, 0),
    "minecraft:glass": (20, 0),
    "minecraft:lapis_block": (22, 0),
    "minecraft:sandstone": (24, 0),
    "minecraft:note_block": (25, 0),
    "minecraft:brick_block": (45, 0),
    "minecraft:stone_bricks": (98, 0),
    "minecraft:quartz_block": (155, 0),
    "minecraft:sea_lantern": (169, 0),
}

LEGACY_NAME_TO_ID = {name: value for name, value in LEGACY_BLOCK_MAP.items()}


@dataclass
class SchematicData:
    size: Tuple[int, int, int]
    palette: List[str]
    blocks: np.ndarray  # shape (y, z, x)

    def to_json(self) -> dict:
        return {
            "size": self.size,
            "palette": self.palette,
            "blocks": self.blocks.astype(int).tolist(),
        }

    def crop(self, min_corner: Tuple[int, int, int], max_corner: Tuple[int, int, int]) -> "SchematicData":
        min_x, min_y, min_z = min_corner
        max_x, max_y, max_z = max_corner
        cropped = self.blocks[min_y:max_y, min_z:max_z, min_x:max_x]
        width = cropped.shape[2]
        height = cropped.shape[0]
        length = cropped.shape[1]
        return SchematicData(size=(width, height, length), palette=self.palette, blocks=cropped.copy())


class UnsupportedFormatError(RuntimeError):
    pass


def detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".schem":
        return "schem"
    if suffix == ".schematic":
        return "schematic"
    if suffix == ".litematic":
        return "litematic"
    raise UnsupportedFormatError(f"Unsupported file format: {path.suffix}")


def _load_schematic(path: Path) -> SchematicData:
    fmt = detect_format(path)
    if fmt == "schem":
        return _load_schem(path)
    if fmt == "schematic":
        return _load_schematic_legacy(path)
    if fmt == "litematic":
        return _load_litematic(path)
    raise UnsupportedFormatError(path.suffix)


def load_schematic(path: Path) -> SchematicData:
    return _load_schematic(path)


def save_schematic(data: SchematicData, path: Path, fmt: Optional[str] = None) -> None:
    fmt = fmt or detect_format(path)
    if fmt == "schem":
        _save_schem(data, path)
    elif fmt == "schematic":
        _save_schematic_legacy(data, path)
    elif fmt == "litematic":
        _save_litematic(data, path)
    else:
        raise UnsupportedFormatError(fmt)


# === Helper conversions ===


def _schem_palette_to_list(palette: Dict[str, int]) -> List[str]:
    return [block for block, idx in sorted(palette.items(), key=lambda kv: kv[1])]


def _list_to_schem_palette(palette: List[str]) -> Dict[str, int]:
    return {block: idx for idx, block in enumerate(palette)}


def _load_schem(path: Path) -> SchematicData:
    with gzip.open(path, "rb") as fh:
        file = File.parse(fh)
    width = int(file.root["Width"])
    height = int(file.root["Height"])
    length = int(file.root["Length"])
    palette = _schem_palette_to_list(dict(file.root["Palette"]))
    block_data = np.frombuffer(file.root["BlockData"].raw, dtype=np.uint8)
    blocks = np.unpackbits(block_data, bitorder="big")
    bits_per_block = int(file.root["PaletteMax"].unpack())
    block_count = width * height * length
    blocks = blocks[: block_count * bits_per_block]
    blocks = blocks.reshape((-1, bits_per_block))
    indices = np.packbits(blocks, axis=1, bitorder="little")[:, 0]
    indices = indices.reshape((height, length, width))
    return SchematicData(size=(width, height, length), palette=palette, blocks=indices)


def _save_schem(data: SchematicData, path: Path) -> None:
    width, height, length = data.size
    palette_map = _list_to_schem_palette(data.palette)
    bits_per_block = max(4, int(np.ceil(np.log2(len(data.palette)))))
    block_count = width * height * length
    padded = np.zeros(block_count * bits_per_block, dtype=np.uint8)
    flat_indices = data.blocks.reshape(-1)
    bit_array = np.unpackbits(flat_indices[:, np.newaxis], axis=1, bitorder="little")
    bit_array = bit_array[:, :bits_per_block]
    padded[: bit_array.size] = bit_array.reshape(-1)
    packed = np.packbits(padded.reshape(-1, 8), axis=1, bitorder="big")[:, 0]
    block_data = ByteArray(packed.tolist())
    root = Compound(
        Width=Short(width),
        Height=Short(height),
        Length=Short(length),
        Palette=Compound({key: Int(val) for key, val in palette_map.items()}),
        PaletteMax=Int(bits_per_block),
        BlockData=block_data,
    )
    file = File(root=root)
    with gzip.open(path, "wb") as fh:
        file.write(fh)


def _load_schematic_legacy(path: Path) -> SchematicData:
    with gzip.open(path, "rb") as fh:
        file = File.parse(fh)
    width = int(file.root["Width"])
    height = int(file.root["Height"])
    length = int(file.root["Length"])
    blocks = np.array(list(file.root["Blocks"]), dtype=np.uint8).reshape((height, length, width))
    data = np.array(list(file.root.get("Data", [])), dtype=np.uint8).reshape((height, length, width))
    palette: List[str] = []
    palette_indices = np.zeros_like(blocks, dtype=np.int16)
    for y in range(height):
        for z in range(length):
            for x in range(width):
                block_id = int(blocks[y, z, x])
                meta = int(data[y, z, x]) if data.size else 0
                name = _legacy_id_to_name(block_id, meta)
                if name not in palette:
                    palette.append(name)
                palette_indices[y, z, x] = palette.index(name)
    return SchematicData(size=(width, height, length), palette=palette, blocks=palette_indices)


def _save_schematic_legacy(data: SchematicData, path: Path) -> None:
    width, height, length = data.size
    blocks = np.zeros((height, length, width), dtype=np.uint8)
    meta = np.zeros_like(blocks)
    for idx, block in enumerate(data.palette):
        mask = data.blocks == idx
        legacy = LEGACY_NAME_TO_ID.get(block)
        if legacy:
            block_id, block_meta = legacy
        elif block.startswith("minecraft:block_"):
            try:
                _, raw = block.split(":", 1)
                parts = raw.split(":")
                block_id = int(parts[0].split("_")[-1])
                block_meta = int(parts[1]) if len(parts) > 1 else 0
            except (ValueError, IndexError):
                block_id, block_meta = 1, 0
        else:
            block_id, block_meta = 1, 0
        blocks[mask] = block_id % 256
        meta[mask] = block_meta % 16
    root = Compound(
        Width=Short(width),
        Height=Short(height),
        Length=Short(length),
        Blocks=ByteArray(blocks.reshape(-1).tolist()),
        Data=ByteArray(meta.reshape(-1).tolist()),
    )
    file = File(root=root)
    with gzip.open(path, "wb") as fh:
        file.write(fh)


def _load_litematic(path: Path) -> SchematicData:
    if litemapy is None:
        raise UnsupportedFormatError("litemapy is required to read litematic files")
    structure = litemapy.SchemFile.load(path)
    region = next(iter(structure.regions.values()))
    size = (region.width, region.height, region.length)
    palette: List[str] = []
    palette_indices = np.zeros((region.height, region.length, region.width), dtype=np.int32)
    for y in range(region.height):
        for z in range(region.length):
            for x in range(region.width):
                block = region.getblock(x, y, z)
                name = block.blockstate.get("Name", "minecraft:air")
                if name not in palette:
                    palette.append(name)
                palette_indices[y, z, x] = palette.index(name)
    return SchematicData(size=size, palette=palette, blocks=palette_indices)


def _save_litematic(data: SchematicData, path: Path) -> None:
    if litemapy is None:
        raise UnsupportedFormatError("litemapy is required to write litematic files")
    width, height, length = data.size
    schem = litemapy.SchemFile()
    region = schem.add_region("generated", width, height, length)
    for idx, block in enumerate(data.palette):
        palette_id = region.add_blockstate(block)
        mask = data.blocks == idx
        ys, zs, xs = np.where(mask)
        for y, z, x in zip(ys, zs, xs):
            region.setblock(x, y, z, palette_id)
    schem.save(path)


def _legacy_id_to_name(block_id: int, meta: int) -> str:
    for name, (legacy_id, legacy_meta) in LEGACY_NAME_TO_ID.items():
        if legacy_id == block_id and legacy_meta == meta:
            return name
    return f"minecraft:block_{block_id}:{meta}"
