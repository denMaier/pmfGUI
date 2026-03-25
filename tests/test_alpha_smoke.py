import os
from pathlib import Path
import stat
import tempfile
import time
import unittest

from foamlib import FoamCase, FoamFile

from alpha_runtime import (
    derive_launch_command,
    get_foam_run_report,
    load_cell_zones,
    load_run_metadata,
    start_case_run,
    sync_run_metadata,
    tail_run_log,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_TEMPLATE = REPO_ROOT / "templates" / "base"


class AlphaSmokeTests(unittest.TestCase):
    def test_base_template_parses_with_foamlib(self):
        poro_fluid_properties = FoamFile(BASE_TEMPLATE / "constant/poroFluid/poroFluidProperties").as_dict()
        control_dict = FoamFile(BASE_TEMPLATE / "system/controlDict").as_dict()

        self.assertIn("poroFluidModel", poro_fluid_properties)
        self.assertEqual(control_dict["application"], "poroMechanicalFoam")

    def test_case_creation_from_template(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = Path(tmpdir) / "created-case"
            FoamCase(BASE_TEMPLATE).copy(case_dir)

            self.assertTrue((case_dir / "system/controlDict").exists())
            self.assertTrue((case_dir / "constant/physicsProperties").exists())
            self.assertTrue((case_dir / "0/solid/D").exists())

    def test_cell_zone_loading_from_case(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = Path(tmpdir)
            cell_zone_path = case_dir / "constant/polyMesh/cellZones"
            cell_zone_path.parent.mkdir(parents=True, exist_ok=True)
            cell_zone_path.write_text(
                """FoamFile
{
    version 2.0;
}

zones
(
);

solidZone
{
    type cellZone;
}

fluidZone
{
    type cellZone;
}
""",
                encoding="utf-8",
            )

            cell_zones = load_cell_zones(case_dir)

            self.assertEqual(sorted(cell_zones.keys()), ["fluidZone", "solidZone"])

    def test_foam_run_preflight_with_and_without_environment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ready_report = get_foam_run_report({"FOAM_RUN": tmpdir})

        missing_report = get_foam_run_report({})

        self.assertTrue(ready_report.ready)
        self.assertFalse(missing_report.ready)
        self.assertEqual(missing_report.blocking_issues[0].code, "foam_run_missing")

    def test_launch_command_derives_from_control_dict_application(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = Path(tmpdir) / "launch-case"
            FoamCase(BASE_TEMPLATE).copy(case_dir)

            self.assertEqual(derive_launch_command(case_dir), ["poroMechanicalFoam"])

    def test_run_metadata_and_log_rehydrate_from_case_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            case_dir = tmp_path / "runtime-case"
            FoamCase(BASE_TEMPLATE).copy(case_dir)

            boundary_path = case_dir / "constant/polyMesh/boundary"
            boundary_path.parent.mkdir(parents=True, exist_ok=True)
            boundary_path.write_text("dummy boundary", encoding="utf-8")

            with FoamFile(case_dir / "system/controlDict") as control_dict:
                control_dict["application"] = "fakeSolver"

            bin_dir = tmp_path / "bin"
            bin_dir.mkdir()
            fake_solver = bin_dir / "fakeSolver"
            fake_solver.write_text(
                "#!/bin/sh\n"
                "echo solver-start\n"
                "sleep 0.2\n"
                "echo solver-end\n",
                encoding="utf-8",
            )
            fake_solver.chmod(fake_solver.stat().st_mode | stat.S_IEXEC)

            previous_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{previous_path}"
            try:
                started_state = start_case_run(case_dir)
                self.assertEqual(started_state["status"], "running")
                self.assertIsNotNone(started_state["pid"])

                rehydrated_state = load_run_metadata(case_dir)
                self.assertEqual(rehydrated_state["pid"], started_state["pid"])
                self.assertTrue(Path(rehydrated_state["log_path"]).exists())

                time.sleep(0.5)

                final_state = sync_run_metadata(case_dir)
                self.assertEqual(final_state["status"], "completed")
                self.assertEqual(final_state["return_code"], 0)

                log_tail = tail_run_log(final_state["log_path"])
                self.assertIn("solver-start", log_tail)
                self.assertIn("solver-end", log_tail)
            finally:
                os.environ["PATH"] = previous_path


if __name__ == "__main__":
    unittest.main()
