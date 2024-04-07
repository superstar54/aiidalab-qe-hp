from aiida_quantumespresso.data.hubbard_structure import HubbardStructureData
from aiida_quantumespresso.common.types import ElectronicType, SpinType
from aiidalab_qe_hp.workflows import QeappHpWorkChain
from aiida_quantumespresso_hp.workflows.hubbard import SelfConsistentHubbardWorkChain
from aiida import orm

QPOINTS_DISTANCE_MAP = {
    "fast": 1000,
    "moderate": 500,
    "precise": 100,
}

PROTOCOL_MAP_U = {"fast": 1.0, "moderate": 0.5, "precise": 0.1}

PROTOCOL_MAP_V = {
    "fast": 0.5,
    "moderate": 0.1,
    "precise": 0.02,
}


def check_codes(pw_code, hp_code):
    """Check that the codes are installed on the same computer."""
    if (
        not any(
            [
                pw_code is None,
                hp_code is None,
            ]
        )
        and len(
            set(
                (
                    pw_code.computer.pk,
                    hp_code.computer.pk,
                )
            )
        )
        != 1
    ):
        raise ValueError(
            "All selected codes must be installed on the same computer. This is because the "
            "HP calculations rely on large files that are not retrieved by AiiDA."
        )


def get_builder(codes, structure, parameters, **kwargs):
    pw_code = codes.get("pw")
    hp_code = codes.get("hp")
    check_codes(pw_code, hp_code)
    protocol = parameters["workchain"]["protocol"]
    # generate Hubbard structure
    hubbard_structure = HubbardStructureData.from_structure(structure)
    hubbard_u = parameters["hp"].pop("hubbard_u")
    hubbard_v = parameters["hp"].pop("hubbard_v")
    for data in hubbard_u:
        hubbard_structure.initialize_onsites_hubbard(*data)
    for data in hubbard_v:
        hubbard_structure.initialize_intersites_hubbard(*data)
    # print(HubbardUtils(hubbard_structure).get_hubbard_card())
    hubbard = parameters.get("hp", {})
    parallelize_atoms = hubbard.get("parallelize_atoms", False)
    parallelize_qpoints = hubbard.get("parallelize_qpoints", False)
    overrides = {
        "tolerance_onsite": orm.Float(PROTOCOL_MAP_U[protocol]),
        "tolerance_intersite": orm.Float(PROTOCOL_MAP_V[protocol]),
        "hubbard": {
            "parallelize_atoms": orm.Bool(parallelize_atoms),
            "parallelize_qpoints": orm.Bool(parallelize_qpoints),
            "qpoints_distance": QPOINTS_DISTANCE_MAP[protocol],
        },
    }
    builder = SelfConsistentHubbardWorkChain.get_builder_from_protocol(
        pw_code=pw_code,
        hp_code=hp_code,  # modify here if you downloaded the notebook
        hubbard_structure=hubbard_structure,
        protocol=protocol,
        overrides=overrides,
        electronic_type=ElectronicType(parameters["workchain"]["electronic_type"]),
        spin_type=SpinType(parameters["workchain"]["spin_type"]),
        initial_magnetic_moments=parameters["advanced"]["initial_magnetic_moments"],
        **kwargs,
    )
    method = parameters["hp"].pop("method")
    if method == "one-shot":
        builder.max_iterations = orm.Int(1)
        builder.meta_convergence = orm.Bool(False)
        builder.pop("relax", None)
    builder.pop("clean_workdir", None)

    return builder


workchain_and_builder = {
    "workchain": SelfConsistentHubbardWorkChain,
    "exclude": ("clean_workdir", "structure"),
    "get_builder": get_builder,
}
