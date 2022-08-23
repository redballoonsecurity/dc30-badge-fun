from ofrak import OFRAK, Resource
from ofrak.core import (
    ProgramAttributes,
    PatchFromSourceModifier,
    PatchFromSourceModifierConfig,
    Program,
    SourceBundle,
    LinkableSymbolType,
    MemoryRegion,
    UpdateLinkableSymbolsModifier,
    UpdateLinkableSymbolsModifierConfig,
    LinkableSymbol,
    BinaryInjectorModifier,
    BinaryInjectorModifierConfig,
    StringFindReplaceModifier,
    StringFindReplaceConfig,
)
from ofrak.service.assembler.assembler_service_keystone import KeystoneAssemblerService
from ofrak_patch_maker.model import Segment, BinFileType
from ofrak_patch_maker.toolchain.model import ToolchainConfig, CompilerOptimizationLevel
from ofrak_patch_maker.toolchain.version import ToolchainVersion
from ofrak_type.architecture import (
    InstructionSet,
    SubInstructionSet,
    InstructionSetMode,
    ProcessorType,
)
from ofrak_type.bit_width import BitWidth
from ofrak_type.endianness import Endianness
from ofrak_type.memory_permissions import MemoryPermissions
from ofrak_type.range import Range


BADGE_FW = "./badge_fw.bin"
OUTPUT_FILE = "./patched_badge_fw.bin"

ARCH_INFO = ProgramAttributes(
    InstructionSet.ARM,
    SubInstructionSet.ARMv5T,
    BitWidth.BIT_32,
    Endianness.LITTLE_ENDIAN,
    None,
)

assembler_service = KeystoneAssemblerService()

START_VM_ADDRESS = 0x10000000
FIRMWARE_SIZE = 0x177CC

FREE_SCRATCH_SPACE = 0x20026F04
DRAW_VOLUME_RANGE = Range(0x10000D14, 0x10000E18)
DRAW_USB_ID_RANGE = Range(0x10000E1C, 0x10000E50)

TOOLCHAIN_CONFIG = ToolchainConfig(
    file_format=BinFileType.ELF,
    force_inlines=False,
    relocatable=False,
    no_std_lib=True,
    no_jump_tables=True,
    no_bss_section=True,
    compiler_optimization_level=CompilerOptimizationLevel.SPACE,
    check_overlap=True,
)
TOOLCHAIN_VERSION = ToolchainVersion.GNU_ARM_NONE_EABI_10_2_1

PATCH_SOURCE = "./play_note_sequence.c"

LINKABLE_SYMBOLS = [
    # Existing variables in binary
    LinkableSymbol(0x20026eea, "notes_held_bitmap", LinkableSymbolType.RW_DATA, InstructionSetMode.NONE),
    LinkableSymbol(0x200019d8, "octave", LinkableSymbolType.RW_DATA, InstructionSetMode.NONE),
    LinkableSymbol(0x20001991, "most_recent_note_played", LinkableSymbolType.RW_DATA, InstructionSetMode.NONE),
    LinkableSymbol(0x200063d8, "notes_played", LinkableSymbolType.RW_DATA, InstructionSetMode.NONE),
    LinkableSymbol(0x20026f01, "instrument", LinkableSymbolType.RW_DATA, InstructionSetMode.NONE),

    # Variables we created in some scratch space
    LinkableSymbol(FREE_SCRATCH_SPACE, "counter", LinkableSymbolType.RW_DATA,InstructionSetMode.NONE),
    LinkableSymbol(FREE_SCRATCH_SPACE + 0x8, "seq_i", LinkableSymbolType.RW_DATA,InstructionSetMode.NONE),
    LinkableSymbol(FREE_SCRATCH_SPACE + 0x10, "state", LinkableSymbolType.RW_DATA,InstructionSetMode.NONE),

    # Existing functions in binary
    LinkableSymbol(0x10005074, "draw_rect_white", LinkableSymbolType.FUNC, InstructionSetMode.THUMB),
    LinkableSymbol(0x10004fc4, "write_character", LinkableSymbolType.FUNC, InstructionSetMode.THUMB),
    LinkableSymbol(0x1000503c, "write_text", LinkableSymbolType.FUNC, InstructionSetMode.THUMB),

]


async def ofrak_the_strings(resource: Resource):
    """
    Change Play menu to OFRAK!

    Update credits to give credit where due
    """
    # First, let's overwrite Play with "OFRAK!"
    await resource.run(
        StringFindReplaceModifier, StringFindReplaceConfig("Play", "OFRAK!", True, True)
    )
    # Let's overwrite credits with OFRAK animal names
    await resource.run(
        StringFindReplaceModifier,
        StringFindReplaceConfig("ktjgeekmom", "mushroom", True, False),
    )
    await resource.run(
        StringFindReplaceModifier,
        StringFindReplaceConfig("compukidmike", "caterpillar", True, False),
    )
    await resource.run(
        StringFindReplaceModifier,
        StringFindReplaceConfig("redactd", "rbs", True, False),
    )


async def ofrak_challenge_one(resource: Resource):
    """
    Win challenge 1 by pressing any key!
    :param resource:
    :return:
    """
    check_challenge_address = 0x10002DF0
    win_address = 0x10002E20
    jump_asm = f"b {hex(win_address)}"
    jump_bytes = await assembler_service.assemble(
        jump_asm, check_challenge_address + 4, ARCH_INFO, InstructionSetMode.THUMB
    )

    await resource.run(
        BinaryInjectorModifier,
        BinaryInjectorModifierConfig([(0x10002DF0 + 4, jump_bytes)]),
    )


async def ofrak_the_logo(resource: Resource):
    """
    Replace the DefCon logo with OFRAK!
    """
    logo_offset = 0x13D24
    ofrak_logo_path = "./shroomscreen.data"
    with open(ofrak_logo_path, "rb") as f:
        ofrak_logo_bytes = f.read()
    resource.queue_patch(
        Range.from_size(logo_offset, len(ofrak_logo_bytes)), ofrak_logo_bytes
    )
    await resource.save()


async def overwrite_draw_volume_info(resource):
    """
    Creates free space! But you no longer get to see the current volume and the nice arrows
    telling you which way to adjust it.
    """
    # Creates free space! But you no longer get to see the current volume
    # and the nice arrows telling you you can adjust it

    return_instruction = await assembler_service.assemble(
        "mov pc, lr",
        DRAW_VOLUME_RANGE.end - 2,
        ARCH_INFO,
        InstructionSetMode.THUMB,
    )

    nop_sled = await assembler_service.assemble(
        "\n".join(
            ["nop"] * int((DRAW_VOLUME_RANGE.length() - len(return_instruction)) / 2)
        ),
        DRAW_VOLUME_RANGE.start,
        ARCH_INFO,
        InstructionSetMode.THUMB,
    )

    final_mc = nop_sled + return_instruction
    assert len(final_mc) == DRAW_VOLUME_RANGE.length()

    await resource.run(
        BinaryInjectorModifier,
        BinaryInjectorModifierConfig([(DRAW_VOLUME_RANGE.start, final_mc)]),
    )


async def ofrak_player_piano(ofrak_context, resource: Resource):
    """
    Patch in the auto-player that plays the sequence to solve challenge 1.
    """
    # Not strictly necessary, but nice to really clear all "free space"
    await overwrite_draw_volume_info(resource)

    source_bundle_r = await ofrak_context.create_root_resource(
        "", b"", tags=(SourceBundle,)
    )
    source_bundle: SourceBundle = await source_bundle_r.view_as(SourceBundle)
    with open(PATCH_SOURCE, "r") as f:
        await source_bundle.add_source_file(f.read(), PATCH_SOURCE)

    await resource.run(
        UpdateLinkableSymbolsModifier,
        UpdateLinkableSymbolsModifierConfig(tuple(LINKABLE_SYMBOLS)),
    )

    await resource.run(
        PatchFromSourceModifier,
        PatchFromSourceModifierConfig(
            source_bundle_r.get_id(),
            {
                PATCH_SOURCE: (
                    Segment(
                        ".text",
                        DRAW_VOLUME_RANGE.start,
                        0,
                        False,
                        DRAW_VOLUME_RANGE.length() - 0x50,
                        MemoryPermissions.RX,
                    ),
                    Segment(
                        ".rodata",
                        DRAW_VOLUME_RANGE.end - 0x50,
                        0,
                        False,
                        0x50,
                        MemoryPermissions.R,
                    ),
                ),
            },
            TOOLCHAIN_CONFIG,
            TOOLCHAIN_VERSION,
        ),
    )


async def main(ofrak_context):
    resource = await ofrak_context.create_root_resource_from_file(BADGE_FW)
    resource.add_tag(Program)
    resource.add_attributes(ARCH_INFO)
    resource.add_view(MemoryRegion(START_VM_ADDRESS, FIRMWARE_SIZE))
    await resource.save()

    await ofrak_the_strings(resource)
    await ofrak_the_logo(resource)

    if False:  # Change to False to switch to injecting player!
        await ofrak_challenge_one(resource)
    else:
        await ofrak_player_piano(ofrak_context, resource)

    await resource.save()
    await resource.flush_to_disk(OUTPUT_FILE)


if __name__ == "__main__":
    ofrak = OFRAK()
    ofrak.run(main)
