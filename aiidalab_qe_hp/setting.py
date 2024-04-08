# -*- coding: utf-8 -*-
"""Panel for HP plugin.

"""
import ipywidgets as ipw
import traitlets as tl
from aiida.orm import StructureData, Float, Bool
from aiida_quantumespresso.workflows.pw.base import PwBaseWorkChain
from aiida_quantumespresso.calculations.functions.create_kpoints_from_distance import (
    create_kpoints_from_distance,
)
from aiidalab_qe.common.panel import Panel


class Setting(Panel):
    title = "HP Settings"
    identifier = "hp"
    input_structure = tl.Instance(StructureData, allow_none=True)
    protocol = tl.Unicode(allow_none=True)

    one_shot_description = """<div>Single calculation without iterative self-consistent procedure, no structural optimization. </div>"""
    self_consistent_description = """<div>Iterative self-consistent procedure, with structural optimization. </div>"""
    dft_u_description = """<div>Only on-site U Hubbard parameter is computed. </div>"""
    dft_u_v_description = (
        """<div>On-site U and inter-site V Hubbard parameters are computed. </div>"""
    )
    atomic_description = """<div>Non-orthogonalized atomic orbitals. </div>"""
    ortho_atomic_description = """<div>Löwdin-orthogonalized atomic orbitals. </div>"""
    method_description = ipw.HTML(one_shot_description)
    calculation_type_description = ipw.HTML(dft_u_description)
    projector_type_description = ipw.HTML(ortho_atomic_description)
    Hubbard_U_title = ipw.HTML(
        """<div style="padding-top: 0px; padding-bottom: 0px">
        <h4>Select atoms for which on-site Hubbard U must be computed</h4></div>"""
    )
    Hubbard_V_title = ipw.HTML(
        """<div style="padding-top: 0px; padding-bottom: 0px">
        <h4>Select couples of atoms for which inter-site Hubbard V must be computed</h4></div>"""
    )
    Info = ipw.HTML()

    def __init__(self, **kwargs):
        self.hubbard_u_map = {}
        self.hubbard_v_map = {}
        # method to calculate the Hubbard U and V values: One-shot or Self-consistent
        self.method = ipw.Dropdown(
            options=["one-shot", "self-consistent"],
            value="one-shot",
            description="Method:",
            disabled=False,
            style={"description_width": "initial"},
        )
        # type of calculation: DFT+U (default) or DFT+U+V
        self.calculation_type = ipw.Dropdown(
            options=["DFT+U", "DFT+U+V"],
            value="DFT+U",
            description="Calculation type:",
            disabled=False,
            style={"description_width": "initial"},
        )
        # type of Hubbard projectors: atomic or ortho-atomic (default)
        self.projector_type = ipw.Dropdown(
            options=["atomic", "ortho-atomic"],
            value="ortho-atomic",
            description="Hubbard projector type:",
            disabled=False,
            style={"description_width": "initial"},
        )
        self.qpoint_mesh = ipw.HTML()
        self.hubbard_u = ipw.VBox()
        self.hubbard_v = ipw.VBox()
        # Override setting widget
        self.qpoints_override_prompt = ipw.HTML("<b>&nbsp;&nbsp;Override&nbsp;</b>")
        self.qpoints_override = ipw.Checkbox(
            description="",
            indent=False,
            value=False,
            layout=ipw.Layout(max_width="10%"),
        )
        self.qpoints_distance = ipw.BoundedFloatText(
            min=0.0,
            step=0.05,
            description="q-points distance (1/Å):",
            disabled=False,
            style={"description_width": "initial"},
        )
        self.parallelize_atoms = ipw.Checkbox(
            description="Use parallelization over perturbed Hubbard atoms.",
            indent=False,
            value=True,
            style={"description_width": "initial"},
            layout={"width": "600px"},
        )
        self.parallelize_qpoints = ipw.Checkbox(
            description="Use parallelization over q points.",
            indent=False,
            value=True,
            style={"description_width": "initial"},
        )

        self.method.observe(self._on_method_change, names="value")
        self.calculation_type.observe(self._on_calculation_type_change, names="value")
        self.projector_type.observe(self._on_projector_type_change, names="value")
        self.qpoints_distance.observe(self._on_qpoints_distance_change, names="value")
        ipw.dlink(
            (self.qpoints_override, "value"),
            (self.qpoints_distance, "disabled"),
            lambda override: not override,
        )
        self.children = [
            ipw.HBox(children=[self.method, self.method_description]),
            ipw.HBox(
                children=[self.calculation_type, self.calculation_type_description]
            ),
            ipw.HBox(children=[self.projector_type, self.projector_type_description]),
            # self.qpoints_distance,
            ipw.HBox(
                [
                    self.qpoints_distance,
                    self.qpoint_mesh,
                    self.qpoints_override_prompt,
                    self.qpoints_override,
                ]
            ),
            self.parallelize_atoms,
            self.parallelize_qpoints,
            ipw.VBox(layout=ipw.Layout(border="1px solid black")),
            ipw.VBox(children=[self.Hubbard_U_title, self.hubbard_u]),
            ipw.VBox(children=[self.Hubbard_V_title, self.hubbard_v]),
            self.Info,
        ]
        super().__init__(**kwargs)

    @tl.observe("protocol")
    def _protocol_changed(self, _):
        """Input protocol changed, update the widget values."""
        parameters = PwBaseWorkChain.get_protocol_inputs(self.protocol)
        self.qpoints_distance.value = parameters["kpoints_distance"] * 4

    def _on_method_change(self, _=None):
        if self.method.value == "one-shot":
            self.method_description.value = self.one_shot_description
        else:
            self.method_description.value = self.self_consistent_description

    def _on_calculation_type_change(self, _=None):
        if self.calculation_type.value == "DFT+U":
            self.calculation_type_description.value = self.dft_u_description
        else:
            self.calculation_type_description.value = self.dft_u_v_description
        self._generate_hubbard_table()

    def _on_projector_type_change(self, _=None):
        if self.projector_type.value == "atomic":
            self.projector_type_description.value = self.atomic_description
        else:
            self.projector_type_description.value = self.ortho_atomic_description

    def _on_qpoints_distance_change(self, _=None):
        if self.input_structure is None:
            return
        if self.qpoints_distance.value > 0:
            mesh = create_kpoints_from_distance.process_class._func(
                self.input_structure,
                Float(self.qpoints_distance.value),
                Bool(False),
            )
            self.qpoint_mesh.value = "Mesh " + str(mesh.get_kpoints_mesh()[0])
        else:
            self.qpoint_mesh.value = "Please select a number higher than 0.0"

    def get_panel_value(self):
        """Return a dictionary with the input parameters for the plugin."""
        hubbard_u = [
            [data[1].value, data[2].value, max(data[3].value, 1e-10)]
            for data in self.hubbard_u_map.values()
            if data[0].value
        ]
        hubbard_v = [
            [
                data[1].value,
                data[2].value,
                data[3].value,
                data[4].value,
                max(data[5].value, 1e-10),
            ]
            for data in self.hubbard_v_map.values()
            if data[0].value
        ]
        parameters = {
            "method": self.method.value,
            "qpoints_distance": self.qpoints_distance.value,
            "parallelize_atoms": self.parallelize_atoms.value,
            "parallelize_qpoints": self.parallelize_qpoints.value,
            "calculation_type": self.calculation_type.value,
            "projector_type": self.projector_type.value,
            "hubbard_u": hubbard_u,
            "hubbard_v": hubbard_v,
        }
        return parameters

    def set_panel_value(self, input_dict):
        """Load a dictionary with the input parameters for the plugin."""
        self.method.value = input_dict.get("method", "one-shot")
        self.qpoints_distance.value = input_dict.get("qpoints_distance", 1000)
        self.parallelize_atoms.value = input_dict.get("parallelize_atoms", True)
        self.parallelize_qpoints.value = input_dict.get("parallelize_qpoints", True)
        self.calculation_type.value = input_dict.get("calculation_type", "DFT+U")
        self.projector_type.value = input_dict.get("projector_type", "ortho-atomic")
        hubbard_u = input_dict.get("hubbard_u", [])
        for data in hubbard_u:
            checkbox, _, manifold, U = self.hubbard_u_map[data[0]]
            checkbox.value = True
            manifold.value = data[1]
            U.value = data[2]

        hubbard_v = input_dict.get("hubbard_v", [])
        for data in hubbard_v:
            checkbox, _, manifold1, _, manifold2, V = self.hubbard_v_map[
                (data[0], data[2])
            ]
            checkbox.value = True
            manifold1.value = data[1]
            manifold2.value = data[3]
            V.value = data[4]

    @tl.observe("input_structure")
    def _update_structure(self, _=None):
        self._generate_hubbard_table()

    def _generate_hubbard_table(self, _=None):
        self._generate_u()
        self._generate_v()

    def _generate_u(self):
        """Generate a table with the U values for the selected structure.
        One row for each kind in the structure.
        Each row includes: kind name, manifold, U value."""
        if self.input_structure is None:
            return
        structure = self.input_structure
        kind_list = [Kind.name for Kind in structure.kinds]
        rows = [
            ipw.HBox(
                [
                    ipw.HTML(
                        value="Atomic type",
                        layout=ipw.Layout(width="100px", margin="0 0 0 20px"),
                    ),
                    ipw.HTML(value="Manifold", layout=ipw.Layout(width="100px")),
                    ipw.HTML(
                        value="Initial value in eV (optional)",
                        layout=ipw.Layout(width="250px"),
                    ),
                ]
            )
        ]
        self.hubbard_u_map = {}
        for kind_name in kind_list:
            checkbox = ipw.Checkbox(
                value=False,
                description="",
                indent=False,
                layout=ipw.Layout(width="20px"),
            )
            name = ipw.HTML(value=kind_name, layout=ipw.Layout(width="60px"))
            manifold = ipw.Text(
                value="",
                placeholder="",
                description="",
                layout=ipw.Layout(width="100px"),
            )
            u = ipw.FloatText(
                value=0,
                description="",
                min=1e10,
                max=100,
                layout=ipw.Layout(width="100px", margin="0 0 0 40px"),
            )
            # for the moment, the "border-bottom": "1px solid black" is not working
            rows.append(ipw.HBox([checkbox, name, manifold, u]))
            self.hubbard_u_map[kind_name] = [checkbox, name, manifold, u]
            #
            manifold.observe(self._validate_table, names="value")
        rows.append(
            ipw.VBox(layout=ipw.Layout(border="1px solid black", margin="10px 0 0 0"))
        )
        self.hubbard_u.children = rows

    def _generate_v(self):
        """Generate a table with the V values for the selected structure.
        One row for each kind pair in the structure.
        Each row includes: kind name1, manifold1, kind name2, manifold2, V value."""
        self.hubbard_v.children = []
        self.hubbard_v_map = {}
        self.Hubbard_V_title.value = ""
        if self.input_structure is None or self.calculation_type.value != "DFT+U+V":
            return
        self.Hubbard_V_title.value = """<div style="padding-top: 0px; padding-bottom: 0px">
            <h4>Select couples of atoms for which inter-site Hubbard V must be computed</h4></div>"""
        structure = self.input_structure
        kind_list = [Kind.name for Kind in structure.kinds]
        rows = [
            ipw.HBox(
                [
                    ipw.HTML(
                        value="Atomic type 1",
                        layout=ipw.Layout(width="100px", margin="0 0 0 20px"),
                    ),
                    ipw.HTML(value="Manifold 1", layout=ipw.Layout(width="100px")),
                    ipw.HTML(
                        value="Atomic type 2",
                        layout=ipw.Layout(width="100px", margin="0 0 0 0"),
                    ),
                    ipw.HTML(value="Manifold 2", layout=ipw.Layout(width="100px")),
                    ipw.HTML(
                        value="Initial value in eV (optional)",
                        layout=ipw.Layout(width="250px"),
                    ),
                ]
            )
        ]
        for i in range(len(kind_list)):
            for j in range(i + 1, len(kind_list)):
                kind_name1 = kind_list[i]
                kind_name2 = kind_list[j]
                checkbox = ipw.Checkbox(
                    value=False,
                    description="",
                    indent=False,
                    layout=ipw.Layout(width="20px"),
                )
                name1 = ipw.HTML(
                    value=kind_name1,
                    layout=ipw.Layout(width="50px", margin="0 0 0 20px"),
                )
                manifold1 = ipw.Text(
                    value="",
                    placeholder="",
                    description="",
                    layout=ipw.Layout(width="100px"),
                )
                name2 = ipw.HTML(
                    value=kind_name2,
                    layout=ipw.Layout(width="50px", margin="0 0 0 50px"),
                )
                manifold2 = ipw.Text(
                    value="",
                    placeholder="",
                    description="",
                    layout=ipw.Layout(width="100px"),
                )
                v = ipw.FloatText(
                    value=0,
                    description="",
                    min=1e10,
                    max=100,
                    layout=ipw.Layout(width="100px", margin="0 0 0 40px"),
                )
                rows.append(ipw.HBox([checkbox, name1, manifold1, name2, manifold2, v]))
                self.hubbard_v_map[(kind_name1, kind_name2)] = [
                    checkbox,
                    name1,
                    manifold1,
                    name2,
                    manifold2,
                    v,
                ]
                manifold1.observe(self._validate_table, names="value")
                manifold2.observe(self._validate_table, names="value")
        rows.append(
            ipw.VBox(layout=ipw.Layout(border="1px solid black", margin="10px 0 0 0"))
        )
        self.hubbard_v.children = rows

    def _validate_table(self, _=None):
        """The manifold field must be same for the same kind."""
        if self.calculation_type.value == "DFT+U":
            return
        for key, data in self.hubbard_v_map.items():
            if not data[0].value:
                continue
            # wait for the user to fill the manifold field
            # only compare the selected kind
            if (
                len(data[2].value) > 1
                and self.hubbard_u_map[key[0]][0].value
                and data[2].value != self.hubbard_u_map[key[0]][2].value
            ):
                # add warning message to the Info widget
                self.Info.value = """<div style="color:red; padding-top: 0px; padding-bottom: 0px">
                    <h4>Warning: The manifold for the atoms {} must be the same for U and V.</h4></div>""".format(
                    key[0]
                )
                return
            if (
                len(data[4].value) > 1
                and self.hubbard_u_map[key[1]][0].value
                and data[4].value != self.hubbard_u_map[key[1]][2].value
            ):
                # add warning message to the Info widget
                self.Info.value = """<div style="color:red; padding-top: 0px; padding-bottom: 0px">
                    <h4>Warning: The manifold for the atoms {} must be the same for U and V.</h4></div>""".format(
                    key[1]
                )
                return
        self.Info.value = ""

    def reset(self):
        """Reset the panel to its initial state."""
        self.input_structure = None
        self.hubbard_u.children = []
