import sys
import unittest
from PySide6.QtWidgets import QApplication
from model.patient_model import PatientModel
from ui.single_patient_window import SinglePatientWindow


class TestUi(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication(sys.argv)

    def setUp(self) -> None:
        self.model = PatientModel("Admin")

    def test_spw(self):
        self.window = SinglePatientWindow(self.model)

    def tearDown(self) -> None:
        sys.exit(self.app.exec())
