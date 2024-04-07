import ipywidgets as ipw
from aiidalab_qe.common.panel import ResultPanel
from weas_widget import WeasWidget
from aiida_quantumespresso.utils.hubbard import get_supercell_atomic_index
import numpy as np
from .widget import TableWidget


class Result(ResultPanel):
    title = "HP"
    workchain_labels = ["hp"]

    def __init__(self, node=None, **kwargs):
        super().__init__(node=node, **kwargs)
        self.result_table = TableWidget()
        guiConfig = {
            "enabled": True,
            "components": {"atomsControl": True, "buttons": True},
            "buttons": {
                "fullscreen": True,
                "download": True,
                "measurement": True,
            },
        }
        self.structure_view = WeasWidget(guiConfig=guiConfig)
        self.result_table.observe(self._process_row_index, "row_index")

    def _process_row_index(self, change):
        if change["new"] is not None:
            selected_atoms_indices = [
                i - 1 for i in self.result_table.data[change["new"] + 1][3:5]
            ]
            self.structure_view.avr.selected_atoms_indices = selected_atoms_indices

    def _update_view(self):
        if "relax" not in self.node.inputs.hp:
            hubbard_structure = self.node.outputs.hp.hubbard_structure
        else:
            hubbard_structure = self.node.outputs.hp.hubbard_structure
        self._update_structure(hubbard_structure)
        self._generate_table(hubbard_structure)
        self.children = [
            ipw.VBox(
                children=[
                    self.result_table,
                    ipw.VBox([ipw.HTML("""<h4>Structure</h4>"""), self.structure_view]),
                ],
                layout=ipw.Layout(justify_content="space-between", margin="10px"),
            ),
        ]

    def _update_structure(self, hubbard_structure):
        atoms0 = hubbard_structure.get_ase()
        atoms = atoms0.copy()
        atoms.translate(np.dot([1, 1, 1], atoms.cell))
        # create a supercell around the atoms, from -1 to 1 in each direction
        for i in range(-1, 2):
            for j in range(-1, 2):
                for k in range(-1, 2):
                    if i == 0 and j == 0 and k == 0:
                        continue
                    atoms1 = atoms0.copy()
                    atoms1.translate(np.dot([i + 1, j + 1, k + 1], atoms0.cell))
                    atoms.extend(atoms1)
        # set the cell to be 3 times the original cell
        atoms.cell = np.array([3 * atoms.cell[c] for c in range(3)])
        self.structure_view.from_ase(atoms)
        self.structure_view.avr.model_style = 1
        self.structure_view.avr.color_type = "VESTA"
        self.structure_view.avr.atom_label_type = "Index"

    def _generate_table(self, hubbard_structure):
        # Start of the HTML string for the table

        data = [
            [
                "Hubbard",
                "Kind-Manifold (I)",
                "Kind-Neighbour(J)",
                "Index (I)",
                "Index (J)",
                "Value (eV)",
                "Translation",
                "Distance (Å)",
            ]
        ]
        hubbard = hubbard_structure.hubbard.dict()["parameters"]
        natoms = len(hubbard_structure.sites)
        for site in hubbard:
            kind = hubbard_structure.sites[site["atom_index"]].kind_name
            neighbour_kind = hubbard_structure.sites[site["neighbour_index"]].kind_name
            index_i = site["atom_index"] + 1
            index_j = (
                get_supercell_atomic_index(
                    site["neighbour_index"], natoms, site["translation"]
                )
                + 1
            )
            distance = np.linalg.norm(
                hubbard_structure.sites[site["neighbour_index"]].position
                + np.dot(
                    np.array(site["translation"]), np.array(hubbard_structure.cell)
                )
                - hubbard_structure.sites[site["atom_index"]].position
            )
            distance = round(distance, 2)
            value = round(site["value"], 2)
            data.append(
                [
                    site["hubbard_type"],
                    f"{kind}-{site['atom_manifold']}",
                    f"{neighbour_kind}-{site['neighbour_manifold']}",
                    index_i,
                    index_j,
                    value,
                    site["translation"],
                    distance,
                ]
            )

        self.result_table.data = data
